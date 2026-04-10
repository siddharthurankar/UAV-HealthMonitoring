# -*- coding: utf-8 -*-
import numpy as np
import os
import librosa
import tensorflow as tf
import joblib

# --- Updated Configuration ---
# Pointing to the new EXPO/Motor subfolders
test_files_dir = r'C:\Users\chawl\OneDrive - University of Cincinnati\Senior Design 1\Prissha\EXPO\Motor\Test_Files'
expo_dir = r'C:\Users\chawl\OneDrive - University of Cincinnati\Senior Design 1\Prissha\EXPO\Motor\ExpoModel'

# Load components
model_path = os.path.join(expo_dir, 'Autoencoder_Final.h5')
scaler_path = os.path.join(expo_dir, 'scaler.pkl')
threshold_path = os.path.join(expo_dir, 'threshold.txt')

if not os.path.exists(model_path):
    print(f"Error: Model not found at {model_path}")
    exit()

# Load the Model with the MSE fix
model = tf.keras.models.load_model(model_path, 
                                   custom_objects={'mse': tf.keras.losses.MeanSquaredError()})

# Load the Scaler
scaler = joblib.load(scaler_path)

# Load the Threshold value
with open(threshold_path, 'r') as f:
    THRESHOLD = float(f.read())

print(f"Model, Scaler, and Threshold ({THRESHOLD:.6f}) loaded successfully.")

def process_file(path):
    # 1. Load Audio
    audio, sr = librosa.load(path, sr=None)
    
    # 2. Generate Mel Spectrogram
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
    db = librosa.power_to_db(mel, ref=np.max)
    
    # 3. Handle Local Min-Max scaling (Crucial to match training pipeline)
    db_min = db.min()
    db_max = db.max()
    db_local_norm = (db - db_min) / (db_max - db_min + 1e-6)
    
    # 4. Force Shape (128 rows x 44 columns)
    if db_local_norm.shape[1] < 44:
        db_local_norm = np.pad(db_local_norm, ((0, 0), (0, 44 - db_local_norm.shape[1])))
    else:
        db_local_norm = db_local_norm[:, :44]
    
    # 5. Apply the TRAINED Global Scaler
    flattened = db_local_norm.reshape(1, -1)
    scaled = scaler.transform(flattened)
    
    # 6. Safety Clip (Ensures values stay between 0 and 1)
    scaled = np.clip(scaled, 0, 1)
    
    # 7. Final Reshape and Transpose for Model Input (1, 44, 128)
    spec_norm = scaled.reshape(1, 128, 44)
    return np.transpose(spec_norm, (0, 2, 1))

# --- Interactive Terminal ---
print("\n" + "="*30)
print("MOTOR HEALTH DIAGNOSTIC TOOL")
print("="*30)

while True:
    name = input("\nEnter file (e.g. H558 or F044) or 'exit': ").strip()
    if name.lower() == 'exit': 
        break
    
    # Add .wav if missing
    path = os.path.join(test_files_dir, name + (".wav" if not name.lower().endswith(".wav") else ""))
    
    if os.path.exists(path):
        # Preprocess
        input_data = process_file(path)
        
        # Predict
        reconstruction = model.predict(input_data, verbose=0)
        
        # Calculate Reconstruction Error (MSE)
        mse = np.mean(np.square(input_data - reconstruction))
        
        print(f"--- Results for {name} ---")
        print(f"MSE Error:      {mse:.6f}")
        print(f"Threshold:      {THRESHOLD:.6f}")
        
        if mse > THRESHOLD:
            print(f"FINAL STATUS: [ FAULTY ]")
        else:
            print(f"FINAL STATUS: [ HEALTHY ]")
            
        # Debugging info
        print(f"Data Consistency Check: Min={input_data.min():.2f}, Max={input_data.max():.2f}")
    else:
        print(f"File '{name}' not found in {test_files_dir}")