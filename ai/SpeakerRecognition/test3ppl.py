#!/usr/bin/env python3

import os
import numpy as np
import librosa
import joblib
import sounddevice as sd
import soundfile as sf
import torch
from speechbrain.pretrained import EncoderClassifier
from collections import Counter

# ─── Cấu hình đường dẫn và tham số ─────────────────────────────────────
MODEL_PATH = "classifier_model.pkl"
NORMALIZER_PATH = "normalizer.pkl"
PRETRAINED_DIR = "pretrained_ecapa"
SAMPLE_RATE = 16000
SEG_SECONDS = 2.0
HOP_SECONDS = 1.0
RECORD_PATH = "recorded.wav"

# ─── 1. Load model classifier và normalizer ───────────────────────────
classifier_model = joblib.load(MODEL_PATH)
normalizer = joblib.load(NORMALIZER_PATH)

# ─── 2. Load pre-trained ECAPA-TDNN để trích embedding ───────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
encoder = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir=PRETRAINED_DIR,
    run_opts={"device": device}
)

# ─── 3. Hàm segment + VAD filter ───────────────────────────────────────
def load_segments(path, sr=SAMPLE_RATE, seg_s=SEG_SECONDS, hop_s=HOP_SECONDS):
    y, _ = librosa.load(path, sr=sr)
    seg_len = int(seg_s * sr)
    hop_len = int(hop_s * sr)
    segments = []
    for start in range(0, len(y) - seg_len + 1, hop_len):
        seg = y[start:start + seg_len]
        rms = np.sqrt(np.mean(seg ** 2))
        if rms > 0.01:
            segments.append(seg)
    return segments

# ─── 4. Hàm trích embedding cho mỗi segment ───────────────────────────
def get_embedding(seg):
    sig = torch.tensor(seg).unsqueeze(0)
    emb = encoder.encode_batch(sig.to(device))
    return emb.squeeze(0).cpu().numpy()

# ─── 5. Hàm phân tích file và vote để nhận diện speaker ──────────────
def predict_file(file_path, classifier_model, normalizer, seg_s=SEG_SECONDS, hop_s=HOP_SECONDS, sr=SAMPLE_RATE):
    segments = load_segments(file_path, sr, seg_s, hop_s)
    if not segments:
        raise ValueError("Không tìm thấy segment có giọng nói trong file.")

    embs = np.vstack([get_embedding(seg) for seg in segments])
    embs_norm = normalizer.transform(embs)
    preds = classifier_model.predict(embs_norm)
    vote = Counter(preds).most_common(1)[0][0]
    return vote

# ─── 6. Hàm ghi âm từ micro và lưu file WAV ────────────────────────────
def record_audio(file_path, duration, sr=SAMPLE_RATE):
    print(f"Đang ghi âm trong {duration:.1f} giây...")
    recording = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    sf.write(file_path, recording, sr)
    print(f"Lưu file ghi âm: {file_path}")

# ─── 7. Hàm chính ──────────────────────────────────────────────────────
def main():
    # Ghi âm SEG_SECONDS giây
    record_audio(RECORD_PATH, SEG_SECONDS)

    # Nhận diện speaker
    speaker = predict_file(
        RECORD_PATH,
        classifier_model=classifier_model,
        normalizer=normalizer,
        seg_s=SEG_SECONDS,
        hop_s=HOP_SECONDS,
        sr=SAMPLE_RATE
    )
    print(f"Speaker được dự đoán: {speaker}")

if __name__ == "__main__":
    main()
