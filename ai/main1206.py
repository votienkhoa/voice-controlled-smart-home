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

# === Configuration ===
SAMPLE_RATE = 16000
SEG_SECONDS = 4.0
HOP_SECONDS = 1.0
RECORD_PATH = "recorded.wav"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CLASSIFIER_PATH = "/home/thuongnv/Downloads/classifier_model.pkl"
NORMALIZER_PATH = "/home/thuongnv/Downloads/normalizer.pkl"
PRETRAINED_DIR = "pretrained_ecapa"
WAKE_PHRASE = "xin chào"

COMMAND_TEMPLATES = [
    "bật đèn phòng ngủ",
    "tắt đèn phòng ngủ",
    "mở điều hòa",
    "tắt điều hòa",
]
PERMISSION_MAP = {
    "dung": ["bật đèn phòng ngủ", "tắt đèn phòng ngủ"],
    "huy": COMMAND_TEMPLATES,
    "khoa": ["mở điều hòa", "tắt điều hòa"],
    "thuong": [],
}

# === Load Models ===
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

def recognize_speech(timeout=None, phrase_time_limit=5):
    with sr.Microphone(sample_rate=SAMPLE_RATE) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.5)
        audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        return recognizer.recognize_google(audio, language="vi-VN").lower()
    except (sr.UnknownValueError, sr.RequestError):
        return ""

def record_audio(file_path, duration):
    recording = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    librosa.output.write_wav(file_path, recording[:, 0], sr=SAMPLE_RATE)

def load_segments(path, seg_s=SEG_SECONDS, hop_s=HOP_SECONDS, threshold=0.0):
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
        raise ValueError("Không có đoạn âm thanh đủ ngưỡng VAD.")
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
    print(f"[ACTION] Executing: {cmd}")
    # Placeholder for GPIO / MQTT / API integration

# === Main Loop ===
def main_loop():
    print("Đang hiệu chỉnh nhiễu môi trường...")
    with sr.Microphone(sample_rate=SAMPLE_RATE) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
    print(f"Hệ thống sẵn sàng. Nói '{WAKE_PHRASE}' để bắt đầu.")

    while True:
        try:
            phrase = recognize_speech(phrase_time_limit=4)
            if WAKE_PHRASE in phrase:
                print("[INFO] Phát hiện từ khóa đánh thức.")
                record_audio(RECORD_PATH, SEG_SECONDS)
                speaker = identify_speaker(RECORD_PATH)
                print(f"[INFO] Người nói: {speaker}")
                speak(f"Xin chào {speaker}")

                command_text = recognize_speech(phrase_time_limit=5)
                if not command_text:
                    speak("Tôi không nghe rõ, vui lòng thử lại.")
                    continue

                cmd, score = match_command(command_text)
                print(f"[INFO] Lệnh phù hợp: {cmd} (similarity={score:.2f})")

                if cmd in PERMISSION_MAP.get(speaker, []):
                    speak(f"Đang thực hiện lệnh: {cmd}")
                    execute_command(cmd)
                else:
                    speak("Bạn không có quyền thực hiện lệnh này.")
        except KeyboardInterrupt:
            print("Kết thúc chương trình.")
            break

if __name__ == "__main__":
    main_loop()
