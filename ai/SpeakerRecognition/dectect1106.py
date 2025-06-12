import os
import io
import time
import numpy as np
import sounddevice as sd
import librosa
import torch
from speechbrain.inference import EncoderClassifier
import joblib
from sklearn.preprocessing import Normalizer
import speech_recognition as sr
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from gtts import gTTS
import pygame

# === Configuration ===
SR = 16000
DEVICE = "cpu"
CLASSIFIER_PATH = "/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/classifier_model.pkl"
NORMALIZER_PATH = "/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/normalizer.pkl"
WAKE_PHRASE = "xin chào"
SEG_DUR = 2.0  # seconds for speaker capture

# Predefined commands and permissions
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
spk_encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    run_opts={"device": DEVICE}
)
classifier_model = joblib.load(CLASSIFIER_PATH)
normalizer = joblib.load(NORMALIZER_PATH)
sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
command_embeddings = sentence_model.encode(COMMAND_TEMPLATES)

# Initialize recognizer and TTS
recognizer = sr.Recognizer()
pygame.mixer.init()


def speak(text):
    tts = gTTS(text=text, lang='vi')
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    pygame.mixer.music.load(buf, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def recognize_wake(timeout=None, phrase_time_limit=5):
    with sr.Microphone(sample_rate=SR) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.5)
        audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio, language="vi-VN").lower()
        print(f"[DEBUG] Heard phrase: {text}")
        return text
    except (sr.UnknownValueError, sr.RequestError):
        return ""


def recognize_command(timeout=None, phrase_time_limit=5):
    with sr.Microphone(sample_rate=SR) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.5)
        audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio, language="vi-VN").lower()
        print(f"[DEBUG] Heard command: {text}")
        return text
    except (sr.UnknownValueError, sr.RequestError):
        return ""


def get_speaker_via_sd(duration=SEG_DUR):
    """Record stereo and use channel 1 for speaker ID."""
    audio = sd.rec(int(duration * SR), samplerate=SR, channels=2, dtype='float32')
    sd.wait()
    mono = audio[:, 0]  # take first channel
    # normalize amplitude if needed
    mono = mono / np.max(np.abs(mono) + 1e-6)
    # extract embedding
    tensor = torch.tensor(mono).unsqueeze(0).to(DEVICE)
    emb = spk_encoder.encode_batch(tensor)
    vec = emb.squeeze(0).cpu().numpy()
    vec_norm = normalizer.transform(vec.reshape(1, -1))
    return classifier_model.predict(vec_norm)[0]


def match_command(text):
    emb = sentence_model.encode([text])[0]
    sims = cosine_similarity([emb], command_embeddings)[0]
    idx = int(np.argmax(sims))
    return COMMAND_TEMPLATES[idx], sims[idx]


def execute_command(cmd):
    print(f"[ACTION] {cmd}")  # integrate actual API here


def main_loop():
    # Calibrate once
    with sr.Microphone(sample_rate=SR) as mic:
        print("Calibrating ambient noise...")
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
    print(f"Hệ thống sẵn sàng. Nói '{WAKE_PHRASE}' để bắt đầu.")

    while True:
        try:
            phrase = recognize_wake(timeout=None, phrase_time_limit=4)
            if WAKE_PHRASE in phrase:
                print("[INFO] Wake word detected.")
                user = get_speaker_via_sd()
                print(f"Speaker: {user}")
                speak(f"Xin chào {user}")

                cmd_text = recognize_command(timeout=None, phrase_time_limit=5)
                if not cmd_text:
                    speak("Tôi không nghe rõ lệnh, vui lòng thử lại.")
                    continue
                cmd, score = match_command(cmd_text)
                print(f"Matched: {cmd} (sim={score:.2f})")

                if cmd in PERMISSION_MAP.get(user, []):
                    speak(f"Đang thực hiện lệnh {cmd}")
                    execute_command(cmd)
                else:
                    speak("Bạn không có quyền thực hiện lệnh này.")
        except KeyboardInterrupt:
            print("Chương trình kết thúc.")
            break


main_loop()
