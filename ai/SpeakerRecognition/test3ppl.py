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
MODEL_PATH = "/home/thuongnv/Downloads/classifier_model.pkl"
NORMALIZER_PATH = "/home/thuongnv/Downloads/normalizer.pkl"
PRETRAINED_DIR = "pretrained_ecapa"
SAMPLE_RATE = 16000
SEG_SECONDS = 4.0
HOP_SECONDS = 1.0
RECORD_PATH = "recorded.wav"
VAD_THRESHOLD = 0.0  # Đặt = 0 để tắt VAD hoàn toàn

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
def load_segments(path, sr=SAMPLE_RATE, seg_s=SEG_SECONDS, hop_s=HOP_SECONDS, threshold=VAD_THRESHOLD):
    y, _ = librosa.load(path, sr=sr)
    seg_len = int(seg_s * sr)
    hop_len = int(hop_s * sr)
    segments = []
    for start in range(0, len(y) - seg_len + 1, hop_len):
        seg = y[start:start + seg_len]
        rms = np.sqrt(np.mean(seg ** 2))
        if rms > threshold:
            segments.append(seg)
    return segments

# ─── 4. Hàm trích embedding cho mỗi segment ───────────────────────────
def get_embedding(seg):
    sig = torch.tensor(seg).unsqueeze(0)
    emb = encoder.encode_batch(sig.to(device))
    return emb.squeeze(0).cpu().numpy()

# ─── 5. Hàm phân tích file, in xác suất từng segment và thống kê ──────
def predict_file(file_path, classifier_model, normalizer,
                 seg_s=SEG_SECONDS, hop_s=HOP_SECONDS, sr=SAMPLE_RATE):
    # Segment + VAD
    segments = load_segments(file_path, sr, seg_s, hop_s)
    if not segments:
        raise ValueError("Không tìm thấy segment có giọng nói trong file.")

    # Embedding -> Normalize -> Predict
    embs = np.vstack([get_embedding(seg) for seg in segments])
    embs_norm = normalizer.transform(embs)

    # Xác suất từng segment
    proba = classifier_model.predict_proba(embs_norm)
    classes = classifier_model.classes_

    print("=== Xác suất từng segment ===")
    for i, prob in enumerate(proba):
        print(f"Segment {i+1}:")
        for cls, p in zip(classes, prob):
            print(f"  {cls}: {p*100:.2f}%")
        print()

    # Tổng hợp đa số phiếu
    preds = classifier_model.predict(embs_norm)
    counts = Counter(preds)
    vote = counts.most_common(1)[0][0]
    percentages = {cls: cnt / len(preds) * 100 for cls, cnt in counts.items()}
    return vote, percentages

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

    # Nhận diện speaker và %
    speaker, percents = predict_file(
        RECORD_PATH,
        classifier_model=classifier_model,
        normalizer=normalizer,
        seg_s=SEG_SECONDS,
        hop_s=HOP_SECONDS,
        sr=SAMPLE_RATE
    )
    print(f"\nSpeaker được dự đoán: {speaker}")
    print("\n=== Phần trăm vote theo segment ===")
    for cls, pct in sorted(percents.items(), key=lambda x: -x[1]):
        print(f"  {cls}: {pct:.2f}%")

if __name__ == "__main__":
    main()
