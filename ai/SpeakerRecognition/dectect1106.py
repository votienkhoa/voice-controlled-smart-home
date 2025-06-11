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
CLASSIFIER_PATH = "/home/thuongnv/Downloads/classifier_model.pkl"
NORMALIZER_PATH = "/home/thuongnv/Downloads/normalizer.pkl"
WAKE_PHRASE = "xin chào"

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

# Speech recognizer + TTS init
recognizer = sr.Recognizer()
pygame.mixer.init()


def speak(text):
    """Convert text to speech and play."""
    tts = gTTS(text=text, lang='vi')
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    pygame.mixer.music.load(buf, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)


def recognize_wake(timeout=None, phrase_time_limit=5):
    """Listen for wake phrase and return text and audio data."""
    with sr.Microphone(sample_rate=SR) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.5)
        audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio, language="vi-VN").lower()
        print(f"[DEBUG] Heard phrase: {text}")
        return text, audio
    except sr.UnknownValueError:
        print("[DEBUG] Wake audio not understood")
        return "", None
    except sr.RequestError as e:
        print(f"[ERROR] API error: {e}")
        return "", None


def recognize_command(timeout=None, phrase_time_limit=5):
    """Listen for a command and return transcribed text."""
    with sr.Microphone(sample_rate=SR) as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.5)
        audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = recognizer.recognize_google(audio, language="vi-VN").lower()
        print(f"[DEBUG] Heard command: {text}")
        return text
    except sr.UnknownValueError:
        print("[DEBUG] Command not understood")
        return ""
    except sr.RequestError as e:
        print(f"[ERROR] API error: {e}")
        return ""


def get_speaker_from_audio(audio_data):
    """Extract speaker from raw WAV bytes."""
    wav_bytes = audio_data.get_wav_data()
    seg, _ = librosa.load(io.BytesIO(wav_bytes), sr=SR)
    tensor = torch.tensor(seg).unsqueeze(0).to(DEVICE)
    emb = spk_encoder.encode_batch(tensor)
    vec = emb.squeeze(0).cpu().numpy()
    vec_norm = normalizer.transform(vec.reshape(1, -1))
    return classifier_model.predict(vec_norm)[0]


def match_command(text):
    """Match text to closest command template."""
    emb = sentence_model.encode([text])[0]
    sims = cosine_similarity([emb], command_embeddings)[0]
    idx = int(np.argmax(sims))
    return COMMAND_TEMPLATES[idx], sims[idx]


def execute_command(cmd):
    """Placeholder to integrate device control APIs."""
    print(f"[ACTION] {cmd}")


def main_loop():
    # Calibrate ambient noise once
    with sr.Microphone(sample_rate=SR) as mic:
        print("Calibrating ambient noise...")
        recognizer.adjust_for_ambient_noise(mic, duration=1.0)
    print(f"Hệ thống sẵn sàng. Nói '{WAKE_PHRASE}' để bắt đầu.")

    while True:
        try:
            text, audio = recognize_wake(timeout=None, phrase_time_limit=4)
            if WAKE_PHRASE in text and audio is not None:
                print("[INFO] Wake word detected.")
                # Identify speaker from wake-word audio
                user = get_speaker_from_audio(audio)
                print(f"Speaker: {user}")
                speak(f"Xin chào {user}")

                # Listen for the actual command
                cmd_text = recognize_command(timeout=None, phrase_time_limit=5)
                if not cmd_text:
                    speak("Tôi không nghe rõ lệnh, vui lòng thử lại.")
                    continue

                cmd, score = match_command(cmd_text)
                print(f"Matched command: {cmd} (sim={score:.2f})")

                # Permission check
                if cmd in PERMISSION_MAP.get(user, []):
                    speak(f"Đang thực hiện lệnh {cmd}")
                    execute_command(cmd)
                else:
                    speak("Bạn không có quyền thực hiện lệnh này.")

        except KeyboardInterrupt:
            print("Chương trình kết thúc.")
            break

if __name__ == "__main__":
    main_loop()
