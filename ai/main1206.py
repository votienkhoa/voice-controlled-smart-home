import os
import io
import time
import numpy as np
import sounddevice as sd
import librosa
import torch
import joblib
import pygame
import speech_recognition as sr
from gtts import gTTS
from collections import Counter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from speechbrain.pretrained import EncoderClassifier
import wave
import requests
import soundfile as sf

# === Configuration ===
SAMPLE_RATE = 16000
DURATION = 2.5
RECORD_PATH = "recorded_command.wav"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CLASSIFIER_PATH = "/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/classifier_model(2).pkl"
NORMALIZER_PATH = "/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/normalizer(2).pkl"
PRETRAINED_DIR = "pretrained_ecapa"
WAKE_PHRASE = "xin chào"

COMMAND_TEMPLATES = [
    "bật đèn phòng con",
    "tắt đèn phòng con",
    "bật đèn phòng cha mẹ",
    "tắt đèn phòng cha mẹ",
    "bật đèn phòng khách",
    "tắt đèn phòng khách",
    "mở cửa phòng con",
    "đóng cửa phòng con",
    "mở cửa phòng cha mẹ",
    "đóng cửa phòng cha mẹ"
]

PERMISSION_MAP = {
    "dung": ["bật đèn phòng con", "tắt đèn phòng con"],
    "huy": [],
    "khoa": ["mở cửa phòng cha mẹ", "đóng cửa phòng cha mẹ"],
    "thuong": COMMAND_TEMPLATES,
}

# === Load models ===
encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir=PRETRAINED_DIR,
    run_opts={"device": DEVICE}
)
classifier_model = joblib.load(CLASSIFIER_PATH)
normalizer = joblib.load(NORMALIZER_PATH)
sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
command_embeddings = sentence_model.encode(COMMAND_TEMPLATES)

recognizer = sr.Recognizer()
pygame.mixer.init()

# === Utility Functions ===
def speak(text):
    tts = gTTS(text=text, lang='vi')
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    pygame.mixer.music.load(buf, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

def recognize_speech_from_file(file_path):
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="vi-VN").lower()
    except (sr.UnknownValueError, sr.RequestError):
        return ""

def record_audio(file_path, duration):
    print("[INFO] Ghi âm...")
    recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    sf.write(file_path, recording, SAMPLE_RATE)

def load_segments(path, seg_s=2.5, hop_s=1.0, threshold=0.0):
    y, _ = librosa.load(path, sr=SAMPLE_RATE)
    seg_len = int(seg_s * SAMPLE_RATE)
    hop_len = int(hop_s * SAMPLE_RATE)
    segments = []
    for start in range(0, len(y) - seg_len + 1, hop_len):
        seg = y[start:start + seg_len]
        rms = np.sqrt(np.mean(seg ** 2))
        if rms > threshold:
            segments.append(seg)
    return segments

def get_embedding(segment):
    sig = torch.tensor(segment).unsqueeze(0).to(DEVICE)
    emb = encoder.encode_batch(sig)
    return emb.squeeze(0).cpu().numpy()

def identify_speaker(audio_path):
    segments = load_segments(audio_path)
    if not segments:
        raise ValueError("[ERROR] Không tìm thấy đoạn giọng để nhận dạng.")
    embs = np.vstack([get_embedding(seg) for seg in segments])
    embs_norm = normalizer.transform(embs)
    preds = classifier_model.predict(embs_norm)
    counts = Counter(preds)
    speaker = counts.most_common(1)[0][0]
    return speaker

def match_command(text):
    emb = sentence_model.encode([text])[0]
    sims = cosine_similarity([emb], command_embeddings)[0]
    idx = int(np.argmax(sims))
    return COMMAND_TEMPLATES[idx], sims[idx]

def execute_command(cmd):
    print(f"[ACTION] Thực thi: {cmd}")
    try:
        if cmd == "bật đèn phòng con":
            requests.post("http://192.168.2.39:3000/led/1/on")
        elif cmd == "tắt đèn phòng con":
            requests.post("http://192.168.2.39:3000/led/1/off")
        elif cmd == "bật đèn phòng cha mẹ":
            requests.post("http://192.168.2.39:3000/led/2/on")
        elif cmd == "tắt đèn phòng cha mẹ":
            requests.post("http://192.168.2.39:3000/led/2/off")
        elif cmd == "bật đèn phòng khách":
            requests.post("http://192.168.2.39:3000/led/3/on")
        elif cmd == "tắt đèn phòng khách":
            requests.post("http://192.168.2.39:3000/led/3/off")
        elif cmd == "mở cửa phòng con":
            requests.post("http://192.168.2.39:3000/servo/1/angle/90")
        elif cmd == "đóng cửa phòng con":
            requests.post("http://192.168.2.39:3000/servo/1/angle/0")
        elif cmd == "mở cửa phòng cha mẹ":
            requests.post("http://192.168.2.39:3000/servo/2/angle/90")
        elif cmd == "đóng cửa phòng cha mẹ":
            requests.post("http://192.168.2.39:3000/servo/2/angle/0")
        else:
            print(f"[WARNING] Lệnh không xác định: {cmd}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Gửi yêu cầu thất bại: {e}")

# === Main Loop ===
def main_loop():
    print("[INFO] Đang hiệu chỉnh nhiễu...")
    with sr.Microphone(sample_rate=SAMPLE_RATE) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
    print(f"[READY] Hệ thống sẵn sàng. Hãy nói '{WAKE_PHRASE}'")

    while True:
        try:
            print("[LISTENING]...")
            with sr.Microphone(sample_rate=SAMPLE_RATE) as mic:
                audio = recognizer.listen(mic, timeout=None, phrase_time_limit=3)
            with open("wake.wav", "wb") as f:
                f.write(audio.get_wav_data())
            phrase = recognize_speech_from_file("wake.wav")

            if WAKE_PHRASE in phrase:
                print("[INFO] Wake word detected.")
                speak("Xin chào, bạn cần gì?")

                record_audio(RECORD_PATH, DURATION)
                speaker = identify_speaker(RECORD_PATH)
                print(f"[INFO] Nhận diện người nói: {speaker}")
                speak(f"Xin chào {speaker}")
                
                command_text = recognize_speech_from_file(RECORD_PATH)
                print(f"[INFO] Lệnh nhận được: {command_text}")

                if not command_text:
                    speak("Tôi không nghe rõ lệnh, vui lòng thử lại.")
                    continue

                cmd, score = match_command(command_text)
                print(f"[INFO] Lệnh khớp: {cmd} (similarity = {score:.2f})")

                if score < 0.5:
                    speak("Lệnh chưa rõ ràng, vui lòng thử lại.")
                    continue

                if cmd in PERMISSION_MAP.get(speaker, []):
                    execute_command(cmd)
                    speak(f"Đã thực hiện lệnh: {cmd}")
                else:
                    speak(f"Bạn không có quyền thực hiện lệnh {cmd}.")
        except KeyboardInterrupt:
            print("[EXIT] Kết thúc chương trình.")
            break

if __name__ == "__main__":
    main_loop()


