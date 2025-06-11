
import numpy as np
import librosa
import sounddevice as sd
import torch
import torch.nn as nn
import torch.nn.functional as F

# ===== Cấu hình =====
sample_rate = 16000            # Tần số lấy mẫu
segment_duration = 2.0         # Thời lượng mỗi đoạn ghi (giây)
segment_length = int(sample_rate * segment_duration)
n_mels = 40                    # Số dải Mel

# Đường dẫn đến các file model và embeddings đã được lưu trước đó
MODEL_PATH = "/media/thuongnv/New Volume/Code/Github/voice-controlled-smart-home/ai/SpeakerRecognition/best_model_9_Jun.pth"
EMB_PATH = "/media/thuongnv/New Volume/Code/Github/voice-controlled-smart-home/ai/SpeakerRecognition/speaker_embeddings_Jun_9.pth"

# ===== Định nghĩa mô hình =====
class SpeakerTransformer(nn.Module):
    def __init__(self, n_mels, embed_dim, num_heads, hidden_dim, num_layers, num_classes):
        super(SpeakerTransformer, self).__init__()
        self.input_proj = nn.Linear(n_mels, embed_dim)
        max_len = 1000
        pe = torch.zeros(max_len, embed_dim)
        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, embed_dim, 2, dtype=torch.float32) * -(np.log(10000.0) / embed_dim))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('positional_encoding', pe)
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(d_model=embed_dim, nhead=num_heads, dim_feedforward=hidden_dim,
                                                   dropout=0.1, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        # Fully-connected head
        self.fc = nn.Linear(embed_dim * 2, num_classes)

    def forward(self, x):
        # x shape: (batch, time, n_mels)
        x = self.input_proj(x)
        T = x.size(1)
        pe = self.positional_encoding[:T, :].unsqueeze(0)
        x = x + pe
        x = self.transformer_encoder(x)
        mean_vec = x.mean(dim=1)
        std_vec = x.std(dim=1)
        stats = torch.cat([mean_vec, std_vec], dim=1)
        return self.fc(stats)

    def get_embedding(self, x):
        x = self.input_proj(x)
        T = x.size(1)
        pe = self.positional_encoding[:T, :].unsqueeze(0)
        x = x + pe
        x = self.transformer_encoder(x)
        mean_vec = x.mean(dim=1)
        std_vec = x.std(dim=1)
        return torch.cat([mean_vec, std_vec], dim=1)

# ===== Hàm tiện ích =====
def extract_log_mel(segment: np.ndarray) -> np.ndarray:
    """Trích xuất log-Mel spectrogram và chuẩn hóa về [0,1]"""
    mel_spec = librosa.feature.melspectrogram(
        y=segment, sr=sample_rate, n_fft=512,
        hop_length=160, win_length=400, n_mels=n_mels
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)
    mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-6)
    return mel_norm.astype(np.float32)


def load_model_and_embeddings(model_path: str, emb_path: str, device: torch.device):
    """Nạp mô hình và embedding đã lưu trước"""
    ckpt = torch.load(model_path, map_location=device)
    label_to_index = ckpt['label_to_index']
    index_to_label = ckpt['index_to_label']
    # Tham số mô hình phải khớp với lúc huấn luyện
    embed_dim = 128
    num_heads = 4
    hidden_dim = 256
    num_layers = 3
    num_classes = len(label_to_index)
    model = SpeakerTransformer(n_mels, embed_dim, num_heads, hidden_dim, num_layers, num_classes)
    model.load_state_dict(ckpt['model_state_dict'])
    model.to(device).eval()
    speaker_embeddings = torch.load(emb_path, map_location=device)
    # Chuẩn hóa các embedding
    for name, emb in speaker_embeddings.items():
        speaker_embeddings[name] = F.normalize(emb, dim=0)
    return model, label_to_index, index_to_label, speaker_embeddings


def recognize_realtime():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model, label_to_index, index_to_label, speaker_embeddings = \
        load_model_and_embeddings(MODEL_PATH, EMB_PATH, device)

    print("=== Bắt đầu nhận diện speaker theo thời gian thực ===")
    try:
        while True:
            print("Ghi âm {} giây...".format(segment_duration))
            audio = sd.rec(segment_length, samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()
            signal = audio.flatten()
            # Trích đặc trưng
            mel = extract_log_mel(signal)
            mel = mel.T  # (time, n_mels)
            inp = torch.tensor(mel).unsqueeze(0).to(device)
            # Softmax classification
            with torch.no_grad():
                logits = model(inp)
                probs = torch.softmax(logits, dim=1).cpu().numpy().flatten()
                pred_idx = int(np.argmax(probs))
                softmax_name = index_to_label[pred_idx]
            # Cosine similarity
            with torch.no_grad():
                emb = model.get_embedding(inp).squeeze(0)
                emb_norm = F.normalize(emb, dim=0)
            sims = {name: float(F.cosine_similarity(emb_norm, ve, dim=0))
                    for name, ve in speaker_embeddings.items()}
            best_cosine = max(sims, key=sims.get)
            print(f"[Softmax] {softmax_name} ({probs[pred_idx]*100:.1f}%), "
                  f"[Cosine] {best_cosine} ({sims[best_cosine]:.4f})")
            print("-----------------------------------------")
    except KeyboardInterrupt:
        print("Dừng nhận diện realtime.")


if __name__ == "__main__":
    recognize_realtime()
