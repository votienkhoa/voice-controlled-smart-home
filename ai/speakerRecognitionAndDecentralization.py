import os
import torch
import torchaudio
import librosa
import numpy as np
from torch import nn
import torch.nn.functional as F
import sounddevice as sd
from scipy.io.wavfile import write
import pyaudio
import speech_recognition as sr
import threading
import queue
import time
import io
import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from gtts import gTTS
import pygame

# ========== Speaker Recognition Setup ==========
speakers = ['dung', 'huy', 'khoa', 'thuong']
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class TransformerSpeakerID(nn.Module):
    def __init__(self, input_dim, num_classes, num_heads=2, num_layers=1, hidden_dim=64, dropout=0.3):
        super(TransformerSpeakerID, self).__init__()
        self.embedding = nn.Linear(input_dim, hidden_dim)
        encoder_layer = nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=num_heads, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        x = x.permute(0, 2, 1)
        x = self.embedding(x)
        x = self.transformer_encoder(x)
        x = x.mean(dim=1)
        x = self.fc(x)
        return x

def extract_mel_spectrogram(waveform, sr=16000, n_mels=256, hop_length=128, n_fft=2048, max_length=64):
    if waveform.ndim == 2:
        waveform = waveform.mean(axis=0)
    mel_spec = librosa.feature.melspectrogram(y=waveform, sr=sr, n_mels=n_mels, hop_length=hop_length, n_fft=n_fft)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_spec_db = (mel_spec_db - mel_spec_db.mean()) / mel_spec_db.std()
    if mel_spec_db.shape[1] > max_length:
        mel_spec_db = mel_spec_db[:, :max_length]
    elif mel_spec_db.shape[1] < max_length:
        mel_spec_db = np.pad(mel_spec_db, ((0, 0), (0, max_length - mel_spec_db.shape[1])), mode='constant')
    return mel_spec_db

def predict_speaker(audio_file, model, device):
    waveform, sample_rate = torchaudio.load(audio_file)
    mel_spec = extract_mel_spectrogram(waveform.numpy().squeeze())
    mel_spec = torch.tensor(mel_spec).float().unsqueeze(0).to(device)

    model.eval()
    with torch.no_grad():
        output = model(mel_spec)
        probabilities = F.softmax(output, dim=1)
        pred = torch.argmax(probabilities, dim=1).item()
        prob_list = probabilities[0].cpu().numpy()

    return speakers[pred], prob_list

def identify_speaker_from_audio(temp_filename='speaker.wav', duration=3):
    input_device_index = sd.default.device[0]
    device_info = sd.query_devices(input_device_index, 'input')
    channels = device_info['max_input_channels'] or 1
    print(f"Recording using device: {device_info['name']} with {channels} channels")
    audio = sd.rec(int(duration * 16000), samplerate=16000, channels=channels, dtype='int16')
    sd.wait()
    write(temp_filename, 16000, audio)
    speaker_name, _ = predict_speaker(temp_filename, model, device)
    return speaker_name

# Load model
model = torch.load('/media/thuongnv/New Volume/Code/Github/voice-controlled-smart-home/ai/SpeakerRecognition/speaker_recognition_full_model_undersampling.pth', weights_only=False)
model.eval()

# ========== Voice Command Control ==========
recognizer = sr.Recognizer()
sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
pygame.mixer.init()
audio_queue = queue.Queue()
awaiting_command = False
current_user = None

command_list = ['tắt đèn', 'bật đèn', 'mở nhạc', 'tắt nhạc']
response_map = {
    'tắt đèn': 'Đã tắt đèn',
    'bật đèn': 'Đã bật đèn',
    'mở nhạc': 'Đã mở nhạc',
    'tắt nhạc': 'Đã tắt nhạc'
}
command_endpoint = {
    'tắt đèn': '/led/off',
    'bật đèn': '/led/on',
}
user_permissions = {
    'dung': ['bật đèn', 'tắt đèn'],
    'huy': ['bật đèn'],
    'khoa': ['tắt đèn'],
    'thuong': []
}
base_url = "https://api.kdth-smarthome.space"
command_embeddings = sentence_model.encode(command_list)

def play_response(text):
    tts = gTTS(text=text, lang='vi')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    pygame.mixer.music.load(mp3_fp, 'mp3')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def record_audio_stream():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    device_index = -1
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if "seeed-2mic-voicecard" in device_info["name"]:
            device_index = i
            break
    if device_index == -1:
        device_index = p.get_default_input_device_info()["index"]

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    input_device_index=device_index, frames_per_buffer=CHUNK)

    print("Recording... Say 'xin chào' followed by your command.")
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_queue.put(data)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        audio_queue.put(None)

def process_audio():
    global awaiting_command, current_user
    audio_data = []
    last_audio_time = time.time()

    while True:
        data = audio_queue.get()
        if data is None:
            break
        audio_data.append(data)

        current_time = time.time()
        elapsed_time = current_time - last_audio_time
        process_interval = 4 if awaiting_command else 2

        if elapsed_time > process_interval:
            try:
                audio = sr.AudioData(b''.join(audio_data), 16000, 2)

                def recognize():
                    global awaiting_command, current_user
                    try:
                        text = recognizer.recognize_google(audio, language='vi-VN').lower()
                        print(f"Heard: {text}")

                        if text.strip() == "xin chào" and not awaiting_command:
                            awaiting_command = True
                            current_user = identify_speaker_from_audio()
                            print(f"Identified speaker: {current_user}")
                            play_response(f"Xin chào {current_user}")
                            print("Waiting for command...")

                        elif awaiting_command:
                            spoken_embedding = sentence_model.encode([text])[0]
                            similarities = cosine_similarity([spoken_embedding], command_embeddings)[0]
                            max_similarity = np.max(similarities)

                            if max_similarity > 0.7:
                                command_idx = np.argmax(similarities)
                                command = command_list[command_idx]
                                print(f"Command: {command} (Similarity: {max_similarity:.2f})")
                                if command in user_permissions.get(current_user, []):
                                    url = base_url + command_endpoint.get(command, '')
                                    if url:
                                        response = requests.get(url)
                                        if response.status_code == 200:
                                            play_response(response_map[command])
                                        else:
                                            play_response("Có lỗi khi gọi API.")
                                    else:
                                        play_response("Lệnh chưa được hỗ trợ qua API.")
                                else:
                                    play_response(f"{current_user} không có quyền thực hiện lệnh này.")
                            else:
                                play_response("Không hiểu lệnh vừa nói.")
                            awaiting_command = False

                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"Error: {e}")
                        play_response("Có lỗi xảy ra khi xử lý âm thanh.")

                threading.Thread(target=recognize, daemon=True).start()
                audio_data = []
                last_audio_time = current_time

            except Exception as e:
                print(f"Processing error: {e}")

        audio_queue.task_done()

def main():
    print("Starting smart voice-controlled system with speaker recognition...")
    record_thread = threading.Thread(target=record_audio_stream)
    process_thread = threading.Thread(target=process_audio)
    record_thread.start()
    process_thread.start()
    try:
        record_thread.join()
        process_thread.join()
    except KeyboardInterrupt:
        print("\nStopped recording.")
    finally:
        pygame.mixer.quit()
        print("Program stopped.")

if __name__ == "__main__":
    main()
