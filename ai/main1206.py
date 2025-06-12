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

import soundfile as sf
# === Configuration ===
SAMPLE_RATE = 16000
DURATION = 2.5  # seconds to capture full command + speaker
RECORD_PATH = "recorded_command.wav"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CLASSIFIER_PATH = "/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/classifier_model(1).pkl"
NORMALIZER_PATH = "/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/normalizer(1).pkl"
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
    # TODO: Thêm lỗi thực tế ở đây (GPIO, MQTT, API...)

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
                print(f"[INFO] Phù hợp với lệnh: {cmd} (sim={score:.2f})")

                if cmd in PERMISSION_MAP.get(speaker, []):
                    speak(f"Đang thực hiện lệnh: {cmd}")
                    execute_command(cmd)
                else:
                    speak(f"Bạn không có quyền thực hiện lệnh {cmd}.")
        except KeyboardInterrupt:
            print("[EXIT] Kết thúc chương trình.")
            break

if __name__ == "__main__":
    main_loop()
