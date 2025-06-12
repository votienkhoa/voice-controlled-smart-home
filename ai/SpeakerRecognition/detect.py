import os
import torch
import torchaudio
import librosa
import numpy as np
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from collections import Counter
import torch.nn.functional as F
speakers = ['dung', 'huy', 'khoa', 'thuong']
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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

def predict_speaker(audio_file, model, device):
    waveform, sample_rate = torchaudio.load(audio_file)
    mel_spec = extract_mel_spectrogram(waveform.numpy().squeeze())
    mel_spec = torch.tensor(mel_spec).float().unsqueeze(0).to(device)  

    model.eval()
    with torch.no_grad():
        output = model(mel_spec)  # Logits
        probabilities = F.softmax(output, dim=1)  # Chuyển thành xác suất
        pred = torch.argmax(probabilities, dim=1).item()  # Nhãn dự đoán
        prob_list = probabilities[0].cpu().numpy()  # Danh sách xác suất

    return speakers[pred], prob_list

# Tải mô hình
input_dim = 256  # n_mels
num_classes = len(speakers)
model = TransformerSpeakerID(input_dim=input_dim, num_classes=num_classes).to(device)
# model.load_state_dict(torch.load('/media/thuongnv/New Volume/Code/Github/voice-controlled-smart-home/ai/SpeakerRecognition/speaker_recognition_full_model.pth'))
model = torch.load('/home/pbl/voice-controlled-smart-home/ai/SpeakerRecognition/speaker_recognition_full_model_undersampling.pth', weights_only=False)
model.eval()
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import time

def record_audio(filename='recorded.wav', duration=3, fs=16000):
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(filename, fs, audio)
    print(f"Saved recording to {filename}")
    return filename

def recognize_speaker(filename, model, device, speakers):
    predicted_speaker, probabilities = predict_speaker(filename, model, device)

    print(f'Predicted speaker: {predicted_speaker}')
    print('Probabilities:')
    for speaker, prob in zip(speakers, probabilities):
        print(f'{speaker}: {prob * 100:.2f}%')

if __name__ == "__main__":
    duration_seconds = 3
    output_file = "recorded.wav"
    
    recorded_file = record_audio(output_file, duration=duration_seconds)
    recognize_speaker(recorded_file, model, device, speakers)
