import streamlit as st
import os
import numpy as np
import librosa
import tensorflow as tf
import joblib
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Motor Health AI Diagnostic", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border: 1px solid #eee; }
    .status-text { font-size: 28px; font-weight: bold; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if 'history' not in st.session_state: st.session_state.history = []

# --- 3. PATHS & ASSETS ---
BASE_DIR = Path(__file__).resolve().parent
TEST_FILES_DIR = BASE_DIR / "Test_Files"
EXPO_DIR = BASE_DIR / "ExpoModel"

@st.cache_resource(show_spinner="Initializing Neural Engine...")
def load_assets():
    model = tf.keras.models.load_model(EXPO_DIR / 'Autoencoder_Final.h5', 
                                       custom_objects={'mse': tf.keras.losses.MeanSquaredError()})
    scaler = joblib.load(EXPO_DIR / 'scaler.pkl')
    with open(EXPO_DIR / 'threshold.txt', 'r') as f:
        threshold = float(f.read().strip())
    return model, scaler, threshold

# --- 4. FIXED PROCESSING LOGIC ---
def analyze_sound(path, scaler, model):
    audio, sr = librosa.load(str(path), sr=None)
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
    db = librosa.power_to_db(mel, ref=np.max)
    
    # Preprocessing
    db_norm = (db - db.min()) / (db.max() - db.min() + 1e-6)
    
    # FIX: Safety check for padding to prevent 'negative value' error
    pad_width = max(0, 44 - db_norm.shape[1])
    db_norm = np.pad(db_norm, ((0, 0), (0, pad_width)))[:, :44]
    
    flattened = db_norm.reshape(1, -1)
    scaled = np.clip(scaler.transform(flattened), 0, 1)
    spec_2d = scaled.reshape(1, 128, 44)
    model_in = np.transpose(spec_2d, (0, 2, 1))
    
    recon = model.predict(model_in, verbose=0)
    mse = float(np.mean(np.square(model_in - recon)))
    return spec_2d[0], recon, mse

# --- 5. SIDEBAR: THE JUDGE'S PANEL ---
with st.sidebar:
    st.image("https://brand.uc.edu/content/dam/brand/images/logos/bearcat-head/uc-bearcat-head-logo-red.png", width=120)
    st.title("EXPO Control Panel")
    
    with st.expander("🎓 Project Credits", expanded=True):
        st.write("**University of Cincinnati**")
        st.write("Senior Design - Class of 2026")
        st.write("*Acoustic Anomaly Detection Team*")

    st.divider()
    
    # Dropdown with persistent key to prevent 'jumping'
    all_files = sorted([f for f in os.listdir(TEST_FILES_DIR) if f.endswith(".wav")])
    selected_file = st.selectbox("📁 Select Motor Audio File", all_files, key="file_selector")
    
    run_btn = st.button("🚀 ANALYZE MOTOR", use_container_width=True, type="primary")
    
    if st.button("Clear Session History"):
        st.session_state.history = []
        st.rerun()

# --- 6. MAIN DASHBOARD ---
st.title("🛡️ Motor Health Monitoring Dashboard")
st.caption("Real-Time Sound Signature Analysis using Neural Reconstruction")

model, scaler, THRESHOLD = load_assets()

if run_btn:
    file_path = TEST_FILES_DIR / selected_file
    
    # Analysis execution
    orig_spec, recon_out, mse = analyze_sound(file_path, scaler, model)
    status = "FAULTY" if mse > THRESHOLD else "HEALTHY"
    status_color = "#dc3545" if status == "FAULTY" else "#28a745"
    
    # Metrics display
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-card'><p style='margin:0;color:#666;'>Diagnosis</p><div class='status-text' style='color:{status_color}'>{status}</div></div>", unsafe_allow_html=True)
    with m2:
        st.metric("Reconstruction Error (MSE)", f"{mse:.6f}", delta=f"{mse - THRESHOLD:.6f}" if status=="FAULTY" else None, delta_color="inverse")
    with m3:
        st.metric("Healthy Threshold", f"{THRESHOLD:.6f}")

    st.divider()
    
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("🔊 Audio Playback")
        st.audio(str(file_path), autoplay=True)
        st.markdown(f"**Analyzing File:** `{selected_file}`")
        st.info("**Science Note:** The AI compares this sound to a mathematical model of a healthy motor. High error indicates mechanical irregularity.")

    with col_r:
        st.subheader("📊 Neural Signature Comparison")
        recon_spec = np.transpose(recon_out[0], (1, 0))
        diff = 1.0 - np.abs(orig_spec - recon_spec) 

        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        ax[0].imshow(orig_spec, aspect='auto', origin='lower', cmap='magma'); ax[0].set_title("Actual Sound")
        ax[1].imshow(recon_spec, aspect='auto', origin='lower', cmap='magma'); ax[1].set_title("AI Prediction")
        ax[2].imshow(diff, aspect='auto', origin='lower', cmap='gray', vmin=0, vmax=1); ax[2].set_title("Anomaly Heatmap")
        plt.tight_layout()
        st.pyplot(fig)

    # History Log
    st.session_state.history.insert(0, {"File": selected_file, "Status": status, "MSE Score": f"{mse:.6f}"})

# --- 7. HISTORY TABLE ---
if st.session_state.history:
    st.divider()
    st.subheader("📋 Session Analysis Log")
    st.dataframe(st.session_state.history, use_container_width=True)