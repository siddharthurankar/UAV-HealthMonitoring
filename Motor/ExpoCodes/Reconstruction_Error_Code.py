# -*- coding: utf-8 -*-
import numpy as np
import os
import librosa
import tensorflow as tf
import joblib
import matplotlib.pyplot as plt

# --- Updated Configuration ---
test_files_dir = r'C:\Users\chawl\OneDrive - University of Cincinnati\Senior Design 1\Prissha\EXPO\Motor\Test_Files'
expo_dir = r'C:\Users\chawl\OneDrive - University of Cincinnati\Senior Design 1\Prissha\EXPO\Motor\ExpoModel'

model_path = os.path.join(expo_dir, 'Autoencoder_Final.h5')
scaler_path = os.path.join(expo_dir, 'scaler.pkl')

# --- 1. Load Model and Scaler ---
if not os.path.exists(model_path):
    print(f"ERROR: Model file not found at {model_path}")
    print(f"Please check: {expo_dir}")
    exit()

try:
    # Attempting load with mse mapping
    model = tf.keras.models.load_model(
        model_path, 
        custom_objects={'mse': tf.keras.losses.MeanSquaredError()}
    )
except:
    # Fallback load if custom_objects fails
    model = tf.keras.models.load_model(model_path, compile=False)
    model.compile(optimizer='adam', loss='mse')

scaler = joblib.load(scaler_path)
print("Model and Scaler loaded successfully.")

def get_comparison_data(path):
    # Load and generate spectrogram
    audio, sr = librosa.load(path, sr=None)
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
    db = librosa.power_to_db(mel, ref=np.max)
    
    # Local Normalization (0 to 1 based on this specific file)
    db_local = (db - db.min()) / (db.max() - db.min() + 1e-6)
    
    # Force Shape to (128, 44)
    if db_local.shape[1] < 44:
        db_local = np.pad(db_local, ((0, 0), (0, 44 - db_local.shape[1])), mode='constant')
    else:
        db_local = db_local[:, :44]
    
    # Global Scaling (Apply the training Min/Max)
    flattened = db_local.reshape(1, -1)
    scaled = scaler.transform(flattened)
    scaled = np.clip(scaled, 0, 1)
    
    # Reshape for model input
    original_spec_2d = scaled.reshape(1, 128, 44)
    model_input = np.transpose(original_spec_2d, (0, 2, 1))
    
    return original_spec_2d[0], model_input

# --- 2. Interactive Loop ---
print("\n--- Spectrogram Difference Analyzer ---")
print("Enter the file name (e.g., H109 or F044). Type 'exit' to quit.")

while True:
    file_to_view = input("\nFile name to analyze: ").strip()
    if file_to_view.lower() == 'exit':
        break

    # Construct file path
    if not file_to_view.lower().endswith('.wav'):
        file_name = file_to_view + ".wav"
    else:
        file_name = file_to_view

    path = os.path.join(test_files_dir, file_name)

    if os.path.exists(path):
        # Process the file
        orig_2d, model_in = get_comparison_data(path)
        
        # Get Reconstruction from Autoencoder
        recon_model_out = model.predict(model_in, verbose=0)
        
        # Convert back to 128x44 image format
        recon_2d = np.transpose(recon_model_out[0], (1, 0))
        
        # Calculate Difference (Residual Map)
        # Higher difference = Darker pixels
        # Formula: 1 - |Original - Reconstructed|
        diff = 1.0 - np.abs(orig_2d - recon_2d)
        
        # --- 3. Plotting ---
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        
        # Plot 1: Original
        axes[0].imshow(orig_2d, aspect='auto', origin='lower', cmap='magma')
        axes[0].set_title(f'Original Spectrogram: {file_name}')
        axes[0].set_ylabel('Frequency Bins')
        axes[0].set_xlabel('Time Frames')
        
        # Plot 2: Reconstructed
        axes[1].imshow(recon_2d, aspect='auto', origin='lower', cmap='magma')
        axes[1].set_title('Reconstructed (Healthy Baseline)')
        axes[1].set_xlabel('Time Frames')
        
        # Plot 3: Error Map
        im = axes[2].imshow(diff, aspect='auto', origin='lower', cmap='gray', vmin=0, vmax=1)
        axes[2].set_title('Anomalies (Black = High Error)')
        axes[2].set_xlabel('Time Frames')
        
        # Add colorbar to the Error Map
        cbar = fig.colorbar(im, ax=axes[2])
        cbar.set_label('Similarity (1.0 = Healthy Match)')
        
        plt.tight_layout()
        plt.show()
    else:
        print(f"Error: File '{file_name}' not found in {test_files_dir}")