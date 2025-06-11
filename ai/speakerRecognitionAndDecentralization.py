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
from collections import deque
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

def predict_speaker_from_raw_audio(raw_audio):
    import wave

    temp_path = "temp_speaker.wav"
    try:
        # Ghi file WAV đúng định dạng PCM 16-bit mono 16kHz
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # paInt16 = 2 bytes
            wf.setframerate(16000)
            wf.writeframes(raw_audio)

        speaker_name, _ = predict_speaker(temp_path, model, device)
    except Exception as e:
        print(f"[Speaker Recognition] Failed to read audio: {e}")
        speaker_name = "unknown"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return speaker_name

# Load model
model = torch.load('/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/speaker_recognition_full_model_undersampling.pth', weights_only=False)
model.eval()

# ========== Voice Command Control ==========
recognizer = sr.Recognizer()
sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
pygame.mixer.init()
audio_queue = queue.Queue()
buffer = deque(maxlen=50)
lock = threading.Lock()
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
    'thuong': ['bật đèn', 'tắt đèn', 'mở nhạc', 'tắt nhạc']
}
base_url = "https://api.kdth-smarthome.space"
command_embeddings = np.array(sentence_model.encode(command_list))

def play_response(text):
    tts = gTTS(text=text, lang='vi')
    filename = "temp_response.mp3"
    tts.save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    os.remove(filename)

def list_audio_input_devices():
    print("Available audio input devices:")
    p = pyaudio.PyAudio()
    selected_index = -1
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info["maxInputChannels"] > 0:
            print(f"  [{i}] {device_info['name']} (Channels: {device_info['maxInputChannels']})")
            if "seeed" in device_info['name'].lower() or "respeaker 2" in device_info['name'].lower():
                selected_index = i
                print(f"--> Selected ReSpeaker device index: {i}")
    p.terminate()
    return selected_index

def record_audio_stream(device_index):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    p = pyaudio.PyAudio()
    if device_index == -1:
        device_index = p.get_default_input_device_info()["index"]
    device_info = p.get_device_info_by_index(device_index)
    print(f"Using device: [{device_index}] {device_info['name']} (Channels: {device_info['maxInputChannels']})")

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                    input_device_index=device_index, frames_per_buffer=CHUNK)

    print("Recording... Say 'xin chào' followed by your command.")
    frames = []
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            buffer.append(data)
            frames.append(data)

            if len(frames) >= 30:
                audio_queue.put(b''.join(frames))
                frames.clear()
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        audio_queue.put(None)

def process_audio():
    global awaiting_command, current_user

    while True:
        raw_audio = audio_queue.get()
        if raw_audio is None:
            break

        try:
            audio = sr.AudioData(raw_audio, 16000, 2)

            def recognize():
                global awaiting_command, current_user
                try:
                    text = recognizer.recognize_google(audio, language='vi-VN').lower()
                    print(f"Heard: {text}")

                    with lock:
                        if "xin chào" in text and not awaiting_command:
                            awaiting_command = True
                            current_user = predict_speaker_from_raw_audio(raw_audio)
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

        except Exception as e:
            print(f"Processing error: {e}")

        audio_queue.task_done()

def main():
    print("Available audio input devices:")
    p = pyaudio.PyAudio()
    selected_device_index = -1
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            print(f"  [{i}] {device_info['name']} (Channels: {device_info['maxInputChannels']})")
            if "seeed" in device_info['name'].lower() or "respeaker 2" in device_info['name'].lower():
                selected_device_index = i
                print(f"--> Selected ReSpeaker device index: {i}")
    if selected_device_index == -1:
        selected_device_index = p.get_default_input_device_info()['index']
        print(f"--> Using default input device index: {selected_device_index}")
    p.terminate()

    print("Starting smart voice-controlled system with speaker recognition...")
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    pa = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                     input_device_index=selected_device_index, frames_per_buffer=CHUNK)
    print("Recording... Say 'xin chào' followed by your command.")
    try:
        global awaiting_command, current_user
        frames = []
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            buffer.append(data)
            frames.append(data)
            if len(frames) >= 30:
                raw_audio = b''.join(frames)
                audio = sr.AudioData(raw_audio, 16000, 2)
                try:
                    text = recognizer.recognize_google(audio, language='vi-VN').lower()
                    print(f"Heard: {text}")
                    if "xin chào" in text and not awaiting_command:
                        awaiting_command = True
                        current_user = predict_speaker_from_raw_audio(raw_audio)
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
                frames.clear()
    except KeyboardInterrupt:
        print("Stopped recording.")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        pygame.mixer.quit()
        print("Program stopped.")

if __name__ == "__main__":
    main()
