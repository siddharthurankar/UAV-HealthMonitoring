import streamlit as st
import os
import numpy as np
import librosa
import tensorflow as tf
import joblib
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Motor Health AI Diagnostic", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border: 1px solid #eee; }
    .status-text { font-size: 28px; font-weight: bold; text-align: center; margin-top: 10px; }
    .metadata-box { background-color: #f1f3f6; padding: 15px; border-radius: 10px; border-left: 5px solid #004d40; margin-bottom: 10px; }
    .label-healthy { color: #28a745; font-weight: bold; border: 1px solid #28a745; padding: 2px 8px; border-radius: 5px; background: #e8f5e9; }
    .label-faulty { color: #dc3545; font-weight: bold; border: 1px solid #dc3545; padding: 2px 8px; border-radius: 5px; background: #ffebee; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if 'history' not in st.session_state: st.session_state.history = []

# --- 3. PATHS & ASSETS ---
BASE_DIR = Path(__file__).resolve().parent
TEST_FILES_DIR = BASE_DIR / "Test_Files"
EXPO_DIR = BASE_DIR / "ExpoModel"
METADATA_PATH = BASE_DIR / "file_metadata_log.csv"

@st.cache_resource(show_spinner="Initializing Neural Engine...")
def load_assets():
    model = tf.keras.models.load_model(EXPO_DIR / 'Autoencoder_Final.h5', 
                                       custom_objects={'mse': tf.keras.losses.MeanSquaredError()})
    scaler = joblib.load(EXPO_DIR / 'scaler.pkl')
    with open(EXPO_DIR / 'threshold.txt', 'r') as f:
        threshold = float(f.read().strip())
    
    # Load Metadata CSV
    if METADATA_PATH.exists():
        metadata_df = pd.read_csv(METADATA_PATH)
    else:
        metadata_df = None
        
    return model, scaler, threshold, metadata_df

# --- 4. FIXED PROCESSING LOGIC ---
def analyze_sound(path, scaler, model):
    audio, sr = librosa.load(str(path), sr=None)
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
    db = librosa.power_to_db(mel, ref=np.max)
    
    db_norm = (db - db.min()) / (db.max() - db.min() + 1e-6)
    pad_width = max(0, 44 - db_norm.shape[1])
    db_norm = np.pad(db_norm, ((0, 0), (0, pad_width)))[:, :44]
    
    flattened = db_norm.reshape(1, -1)
    scaled = np.clip(scaler.transform(flattened), 0, 1)
    spec_2d = scaled.reshape(1, 128, 44)
    model_input = np.transpose(spec_2d, (0, 2, 1))
    
    recon = model.predict(model_input, verbose=0)
    mse = float(np.mean(np.square(model_input - recon)))
    return spec_2d[0], recon, mse

# --- 5. SIDEBAR: THE JUDGE'S PANEL ---
with st.sidebar:
    st.image("UC.png", width=120)
    st.title("EXPO Control Panel")
    
    with st.expander("🎓 Project Credits", expanded=True):
        st.write("**University of Cincinnati**")
        st.write("Senior Design - Class of 2026")
        st.write("*Acoustic Anomaly Detection Team*")

    st.divider()
    
    all_files = sorted([f for f in os.listdir(TEST_FILES_DIR) if f.endswith(".wav")])
    selected_file = st.selectbox("📁 Select Motor Audio File", all_files, key="file_selector")
    
    run_btn = st.button("🚀 ANALYZE MOTOR", use_container_width=True, type="primary")
    
    if st.button("Clear Session History"):
        st.session_state.history = []
        st.rerun()

# --- 6. MAIN DASHBOARD ---
st.title("🛡️ Motor Health Monitoring Dashboard")
st.caption("Real-Time Sound Signature Analysis using Neural Reconstruction")

model, scaler, THRESHOLD, metadata_df = load_assets()

if run_btn:
    file_path = TEST_FILES_DIR / selected_file
    
    # 1. AI Analysis
    orig_spec, recon_out, mse = analyze_sound(file_path, scaler, model)
    status = "FAULTY" if mse > THRESHOLD else "HEALTHY"
    status_color = "#dc3545" if status == "FAULTY" else "#28a745"
    
    # 2. Source Metadata Lookup
    orig_status = "HEALTHY" if selected_file.upper().startswith('H') else "FAULTY"
    orig_class = "label-healthy" if orig_status == "HEALTHY" else "label-faulty"
    
    motor_info = "N/A"
    prop_info = "N/A"
    cond_num = "N/A"
    cond_desc = "Unknown Condition"
    
    if metadata_df is not None:
        match = metadata_df[metadata_df['filename'] == selected_file]
        if not match.empty:
            motor_info = match.iloc[0]['motor']
            prop_info = match.iloc[0]['propeller']
            cond_num = match.iloc[0]['condition']
            cond_desc = match.iloc[0]['condition_desc']

    # --- Metrics display ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-card'><p style='margin:0;color:#666;'>AI Diagnosis</p><div class='status-text' style='color:{status_color}'>{status}</div></div>", unsafe_allow_html=True)
    with m2:
        st.metric("Reconstruction Error (MSE)", f"{mse:.6f}", delta=f"{mse - THRESHOLD:.6f}" if status=="FAULTY" else None, delta_color="inverse")
    with m3:
        st.metric("Healthy Threshold", f"{THRESHOLD:.6f}")

    # --- New Metadata Section ---
    st.markdown("### 📋 Source Metadata & Recording Context")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metadata-box">
            <b>Original Lab Status:</b> <br>
            <span class="{orig_class}">{orig_status}</span>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metadata-box">
            <b>Hardware Configuration:</b> <br>
            Motor: <code>{motor_info}</code> | Propeller: <code>{prop_info}</code>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metadata-box">
            <b>Condition #{cond_num}:</b> <br>
            {cond_desc}
        </div>
        """, unsafe_allow_html=True)

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