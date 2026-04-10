# -*- coding: utf-8 -*-
import numpy as np
import os
import librosa
import soundfile as sf
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras import layers, models
from sklearn.metrics import confusion_matrix, precision_score, recall_score, precision_recall_curve, auc

SEED = 42

# --- Directories ---
healthy_dir = r'C:\Users\chawl\Downloads\Data\Data\Healthy'
extra_healthy_dir = r'C:\Users\chawl\Downloads\Data.zip\Data\Conflicting MH3'
faulty_dir = r'C:\Users\chawl\Downloads\Data\Data\Faulty'

# Output Locations
test_output_dir = r'C:\Users\chawl\OneDrive - University of Cincinnati\Senior Design 1\Prissha\Test_Files'
model_save_dir = r'C:\Users\chawl\OneDrive - University of Cincinnati\Senior Design 1\Prissha\ExpoModel'

for folder in [test_output_dir, model_save_dir]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# %% Load audio files
def load_data(directory, trim_duration=8):
    data, filenames = [], []
    if not os.path.exists(directory):
        return data, filenames
    for filename in os.listdir(directory):
        if filename.endswith('.wav'):
            file_path = os.path.join(directory, filename)
            audio, sr = librosa.load(file_path, sr=None)
            max_len = int(trim_duration * sr)
            audio = audio[:max_len]
            data.append((audio, sr))
            filenames.append(filename)
    return data, filenames

healthy_data, healthy_filenames = load_data(healthy_dir)
extra_h_data, extra_h_filenames = load_data(extra_healthy_dir)
faulty_data, faulty_filenames = load_data(faulty_dir)

all_healthy_data = healthy_data + extra_h_data
all_healthy_filenames = healthy_filenames + extra_h_filenames

# %% Synthetic Data Generation Logic
def generate_synthetic_data(audio, sr, num_copies=5):
    synthetic_results = []
    for i in range(num_copies):
        augmented_audio = audio.copy()
        if np.random.rand() > 0.5:
            augmented_audio = librosa.effects.time_stretch(augmented_audio, rate=np.random.uniform(0.99, 1.02))
        if np.random.rand() > 0.5:
            n_steps = np.random.uniform(-0.1, 0.1)
            augmented_audio = librosa.effects.pitch_shift(augmented_audio, sr=sr, n_steps=n_steps)
        if np.random.rand() > 0.5:
            noise = np.random.randn(len(augmented_audio)) * np.random.uniform(0.001, 0.002)
            augmented_audio += noise
        synthetic_results.append((augmented_audio, sr))
    return synthetic_results

# --- HEALTHY POOL (Target ~1000) ---
healthy_pool_audio, healthy_pool_filenames = list(all_healthy_data), list(all_healthy_filenames)
next_h_id = 109
h_copies = (1000 - len(all_healthy_filenames)) // len(all_healthy_filenames)
for (audio, sr) in all_healthy_data:
    synth_batch = generate_synthetic_data(audio, sr, num_copies=h_copies)
    for s_audio, s_sr in synth_batch:
        healthy_pool_audio.append((s_audio, s_sr))
        healthy_pool_filenames.append(f"H{next_h_id}.wav")
        next_h_id += 1

# --- FAULTY POOL (Target 200) ---
faulty_pool_audio, faulty_pool_filenames = list(faulty_data), list(faulty_filenames)
next_f_id = 82 
f_needed = 200 - len(faulty_filenames)
f_copies_per_file = int(np.ceil(f_needed / len(faulty_filenames)))

for (audio, sr) in faulty_data:
    if len(faulty_pool_filenames) >= 200: break
    synth_batch = generate_synthetic_data(audio, sr, num_copies=f_copies_per_file)
    for s_audio, s_sr in synth_batch:
        if len(faulty_pool_filenames) >= 200: break
        faulty_pool_audio.append((s_audio, s_sr))
        faulty_pool_filenames.append(f"F{next_f_id:03d}.wav")
        next_f_id += 1

# %% Process Spectrograms
def get_mel_spectrogram_image(audio, sr, max_time_frames=44, n_mels=128):
    mel_spectrogram = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=8000)
    mel_spectrogram_db = librosa.power_to_db(mel_spectrogram, ref=np.max)
    mel_spectrogram_db = (mel_spectrogram_db - mel_spectrogram_db.min()) / (mel_spectrogram_db.max() - mel_spectrogram_db.min() + 1e-6)
    if mel_spectrogram_db.shape[1] < max_time_frames:
        padding = np.zeros((n_mels, max_time_frames))
        padding[:, :mel_spectrogram_db.shape[1]] = mel_spectrogram_db
        return padding
    return mel_spectrogram_db[:, :max_time_frames]

healthy_x_img = np.array([get_mel_spectrogram_image(a, s) for a, s in healthy_pool_audio])
scaler = MinMaxScaler()
healthy_x_img_norm = scaler.fit_transform(healthy_x_img.reshape(-1, 128 * 44)).reshape(-1, 128, 44)

# %% Split (Healthy 200 for test)
X_train_val, X_test_h, y_train_val, y_test_h, train_val_files, test_files_h, train_val_audio, test_audio_h = train_test_split(
    healthy_x_img_norm, np.zeros(len(healthy_x_img_norm)), healthy_pool_filenames, healthy_pool_audio, 
    test_size=200, random_state=SEED
)

X_train, X_val, y_train, y_val, _, _, _, _ = train_test_split(
    X_train_val, y_train_val, train_val_files, train_val_audio, test_size=0.2, random_state=SEED
)

# %% SAVE TEST FILES (200 Healthy + 200 Faulty)
print(f"Exporting 400 test files to: {test_output_dir}")
for (audio, sr), fname in zip(test_audio_h, test_files_h):
    sf.write(os.path.join(test_output_dir, fname), audio, sr)
for (audio, sr), fname in zip(faulty_pool_audio, faulty_pool_filenames):
    sf.write(os.path.join(test_output_dir, fname), audio, sr)

# %% Prepare Test Data for Model
X_faulty_pool_raw = np.array([get_mel_spectrogram_image(a, s) for a, s in faulty_pool_audio])
X_test_f = scaler.transform(X_faulty_pool_raw.reshape(-1, 128 * 44)).reshape(-1, 128, 44)

X_test = np.concatenate((X_test_h, X_test_f), axis=0)
y_test = np.concatenate((np.zeros(200), np.ones(200)), axis=0)

# %% Windowing & Model
WINDOW_LENGTH, STRIDE = 44, 5
def window_data(data):
    windows = []
    for spec in data:
        for i in range(0, spec.shape[1] - WINDOW_LENGTH + 1, STRIDE):
            window = spec[:, i:i+WINDOW_LENGTH]
            if window.shape == (128, WINDOW_LENGTH):
                windows.append(window.T)
    return np.array(windows)

x_windows_train, x_windows_test = window_data(X_train), window_data(X_test)

def create_autoencoder(input_dim):
    inputs = layers.Input(shape=(input_dim, 128))
    x = layers.Conv1D(128, 3, activation='relu', padding='same')(inputs)
    x = layers.Conv1D(64, 3, activation='relu', padding='same')(x)
    x = layers.Conv1D(32, 3, activation='relu', padding='same')(x)
    x = layers.Conv1DTranspose(32, 3, activation='relu', padding='same')(x)
    x = layers.Conv1DTranspose(64, 3, activation='relu', padding='same')(x)
    x = layers.Conv1DTranspose(128, 3, activation='relu', padding='same')(x)
    outputs = layers.Conv1D(128, 3, activation='sigmoid', padding='same')(x)
    return models.Model(inputs, outputs)

autoencoder = create_autoencoder(x_windows_train.shape[1])
autoencoder.compile(optimizer='adam', loss='mse')
autoencoder.fit(x_windows_train, x_windows_train, epochs=100, batch_size=10, verbose=1)

# %% Save Trained Model
model_path = os.path.join(model_save_dir, 'Autoencoder_Final.h5')
autoencoder.save(model_path)
print(f"Model saved to {model_path}")

# %% Final Evaluation & Curves
X_test_recon = autoencoder.predict(x_windows_test)
recon_error = np.mean(np.square(x_windows_test - X_test_recon), axis=(1, 2))
train_recon = autoencoder.predict(x_windows_train)
train_error = np.mean(np.square(x_windows_train - train_recon), axis=(1, 2))
threshold_95 = np.percentile(train_error, 95)
y_pred = (recon_error > threshold_95).astype(int)

# Precision-Recall Curve
precision, recall, _ = precision_recall_curve(y_test, recon_error)
pr_auc = auc(recall, precision)

# Plotting PR Curve
plt.figure(figsize=(8, 6))
plt.plot(recall, precision, label=f'PR Curve (AUC = {pr_auc:.4f})', color='teal')
plt.scatter(recall_score(y_test, y_pred), precision_score(y_test, y_pred), color='red', label='95th Percentile Point')
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision-Recall Curve')
plt.legend()
plt.grid(True)
plt.show()

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Healthy', 'Faulty'], yticklabels=['Healthy', 'Faulty'])
plt.title('Confusion Matrix (200 Healthy vs 200 Faulty)')
plt.show()

print(f"\nFinal Results:\nPrecision: {precision_score(y_test, y_pred):.4f}\nRecall: {recall_score(y_test, y_pred):.4f}")
# %%

import joblib

# 1. Save the Scaler
scaler_path = os.path.join(model_save_dir, 'scaler.pkl')
joblib.dump(scaler, scaler_path)

# 2. Save the exact threshold value to a text file
threshold_path = os.path.join(model_save_dir, 'threshold.txt')
with open(threshold_path, 'w') as f:
    f.write(str(threshold_95))

print(f"Scaler and Threshold saved to {model_save_dir}")