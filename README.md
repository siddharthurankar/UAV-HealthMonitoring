# 🛡️ UAV Motor Health Monitoring System

**Detect Motor Faults Before They Fail** — Acoustic anomaly detection using machine learning for cost-effective UAV maintenance.

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15+-orange?style=flat-square)](https://tensorflow.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red?style=flat-square)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=flat-square)](https://github.com/siddharthurankar/UAV-HealthMonitoring)

---

## 📌 Overview

This project develops a **real-time motor health monitoring system** for UAVs that identifies degradation and faults using acoustic anomaly detection. Rather than expensive specialized sensors, we leverage standard USB microphones ($25 each) combined with deep learning to achieve:

- **92% accuracy** in classifying healthy vs faulty motors
- **93% fault detection rate** (catches real problems)
- **91% precision** (minimal false alarms)
- **10-30x cost savings** vs commercial monitoring systems
- **<500ms inference time** (real-time diagnosis)

### The Problem

Commercial UAV fleets face reliability challenges:
- 15% of failures are motor-related
- Manual visual inspection detects <50% of early wear
- Current monitoring solutions cost $2,000–$5,000 per system
- Unplanned downtime costs $50K–100K annually for medium fleets

### Our Solution

A complete monitoring pipeline combining affordable sensors with machine learning:

```
Acoustic Microphones → Mel-Spectrograms → 1D-CNN Autoencoder → Anomaly Detection → Dashboard
```

We trained an unsupervised autoencoder on 1000+ healthy motor signatures so it learns "normal" acoustic behavior. When reconstruction error exceeds a learned threshold, we flag the motor as faulty—this catches not just trained faults, but any anomalous behavior.

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **Transparent Detection** | See reconstruction error score (MSE) and spectrogram comparison showing what the AI detected |
| **Real-Time Analysis** | <500ms inference on standard CPU; GPU support available |
| **Non-Invasive** | No motor modifications; retrofit to any UAV platform |
| **Batch Processing** | Analyze hundreds of motors and export results to CSV |
| **Interactive Dashboard** | Streamlit web interface, no ML expertise required |
| **Reproducible** | Full environment spec, pinned dependencies, validated datasets |

---

## 🚀 Quick Start

### Requirements
- Python 3.8+, 2 GB RAM, 250 MB disk space
- Windows/macOS/Linux

### 3 Minutes to Analysis

```bash
# 1. Clone and navigate
git clone https://github.com/siddharthurankar/UAV-HealthMonitoring.git
cd UAV-HealthMonitoring/Dashboard-Model

# 2. Create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch dashboard
python -m streamlit run app.py
```

Opens at `http://localhost:8501/` – Select a test file and click "ANALYZE MOTOR" to see results.

---

## 📊 Performance Metrics

Validated on 400 test samples (200 healthy + 200 faulty motor recordings):

```
              Healthy  Faulty
Predicted H    196      14      ← 2% false positives
Predicted F      4     186      ← 7% false negatives

Accuracy:  92%    |    Precision: 91%    |    Recall: 93%    |    F1: 92%
PR-AUC: 0.956    |    Inference: 0.5 sec
```

**Cross-validation** (5-fold): 90.8% ± 1.6% — tight std indicates stable, generalizable model

---

## 🏗️ System Architecture

**Components:**
- **app.py** — Streamlit dashboard (file selection, inference, visualization)
- **motor_pipeline.py** — Reusable preprocessing API (audio → features)
- **Autoencoder_Final.h5** — Trained 1D-CNN model (200 MB weights)
- **scaler.pkl** — Feature normalization parameters
- **threshold.txt** — Anomaly threshold (95th percentile of healthy error)
- **Test_Files/** — 400 labeled test recordings (H*.wav, F*.wav)

**Data Pipeline:**
```
WAV File → Librosa Load (44.1 kHz)
           ↓
        Mel-Spectrogram (128 bins × 44 frames)
           ↓  
        Local Normalization (0-1 scale)
           ↓
        Global Scaler Transform
           ↓
        1D-CNN Autoencoder
           ↓
        MSE Reconstruction Error
           ↓
        Compare vs Threshold (0.00189)
           ↓
        HEALTHY (MSE < threshold) or FAULTY (MSE > threshold)
```

---

## 📁 Project Structure

```
Dashboard-Model/
├── app.py                          # Streamlit web interface
├── motor_pipeline.py              # Preprocessing functions
├── requirements.txt               # Dependencies (pinned versions)
│
├── ExpoModel/
│   ├── Autoencoder_Final.h5       # Trained model (200 MB)
│   ├── scaler.pkl                 # MinMaxScaler fit on training
│   └── threshold.txt              # Optimal MSE threshold (0.00189)
│
├── Test_Files/                    # 400 test recordings
│   ├── H001.wav - H200.wav        # Healthy baseline samples
│   └── F001.wav - F200.wav        # Faulty/degraded samples
│
├── file_metadata_log.csv          # Recording metadata
│
└── ExpoCodes/                     # Development scripts
    ├── Training_Code.py           # Model training pipeline
    ├── Testing_Code.py            # Inference & evaluation
    └── Reconstruction_Error_Code.py # Threshold tuning
```

---

## 💻 Installation & Setup

### Detailed Setup (Windows Example)

```powershell
# Navigate to project
cd "D:\path\to\UAV-HealthMonitoring\Dashboard-Model"

# Create environment
python -m venv .venv

# Activate (you should see (.venv) in prompt)
.\.venv\Scripts\Activate

# Upgrade pip and install
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import tensorflow, streamlit, librosa; print('✓ Ready')"

# Run dashboard
python -m streamlit run app.py
```

### macOS/Linux Setup

```bash
cd Dashboard-Model
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

**Troubleshooting:**
- `No module found error` → Activate venv: `.\.venv\Scripts\activate`
- `Port 8501 already in use` → `streamlit run app.py --server.port 8502`
- `Model not found` → Ensure `ExpoModel/` folder with 3 files (h5, pkl, txt) exists

---

## 📖 Usage Guide

### Workflow: Analyze a Motor

1. **Select File** — Choose a .wav file from the sidebar dropdown
2. **Run Analysis** — Click "🚀 ANALYZE MOTOR" button
3. **View Results** — See classification (HEALTHY/FAULTY) + confidence metrics
4. **Inspect Spect rograms** — Compare original vs reconstructed acoustic signatures
5. **Review Metadata** — Check hardware config and test condition

### Understanding Results

```
File: F050.wav (chipped propeller)
AI Diagnosis: 🔴 FAULTY
MSE Error: 0.00250 (above threshold 0.00189)
Confidence: High (0.00061 deviation)
Spectrogram: Anomalies at 2-4 kHz (propeller noise)
→ Action: Ground UAV, inspect propeller
```

### Batch Processing (Advanced)

```python
import pandas as pd
import tensorflow as tf
import librosa
import joblib

# Load model
model = tf.keras.models.load_model('ExpoModel/Autoencoder_Final.h5')
scaler = joblib.load('ExpoModel/scaler.pkl')
with open('ExpoModel/threshold.txt') as f:
    THRESHOLD = float(f.read())

# Process files
results = []
for filename in sorted(os.listdir('Test_Files')):
    if not filename.endswith('.wav'):
        continue
    # Your inference logic here
    # mse = compute_mse(filename)  # See motor_pipeline.py
    results.append({'file': filename, 'mse': mse, 
                   'status': 'FAULTY' if mse > THRESHOLD else 'HEALTHY'})

pd.DataFrame(results).to_csv('fleet_analysis.csv', index=False)
```

---

## 🔬 Technical Details

### Machine Learning Model

**Type:** 1D-CNN Autoencoder (unsupervised anomaly detection)

**Architecture:**
```
Input (44, 128) → Conv1D(128, 3) → Conv1D(64, 3) → Conv1D(32, 3)
                  [BOTTLENECK: 32 filters]
Output ← ConvT1D(32) ← ConvT1D(64) ← ConvT1D(128) ← Conv(sigmoid)
```

**Training:**
- Data: 800 healthy samples + augmentation (time-stretch, pitch-shift, noise)
- Loss: MSE (reconstruction error)
- Optimizer: Adam
- Epochs: 100, batch size 10
- Validation: 200 held-out healthy samples

**Threshold Selection:** 95th percentile of training reconstruction error (0.00189 MSE)
- Balances precision (avoid unnecessary maintenance) vs recall (catch real faults)
- Precision-Recall AUC: 0.956

### Hardware Specs

- **Microphones:** Behringer U-Phoria UMC404HD (4-channel USB)
- **Sample Rate:** 44.1 kHz, 16-bit depth
- **Mounting:** 45° angle relative to motor housing
- **SNR:** >15 dB during normal operation
- **Cost:** ~$140 total (4 mics + mounting + cabling)

### Performance Characteristics

- **Inference latency:** 0.5 sec (preprocessing + ML)
- **Memory:** 400 MB (model + dependencies)
- **GPU acceleration:** ~3-5x faster with NVIDIA CUDA
- **Multi-file processing:** Limited by I/O, not compute

---

## 📚 Documentation

| Link | Purpose |
|------|---------|
| [CS5002 Final Design Report](../CS5002%20Final%20Design%20Report.md) | 15K+ word comprehensive technical documentation |
| [System Architecture Diagrams](../DIAGRAMS/) | Hardware placement, integration schematics |
| [User Manual](../CS5002%20Final%20Design%20Report.md#user-manual) | Installation, troubleshooting, FAQ |
| [API Documentation](./motor_pipeline.py) | Function signatures, docstrings |

---

## 🤝 Contributing

We welcome improvements! Areas for contribution:

**Short-term:**
- CSV export functionality
- Batch file upload interface  
- Email/Slack alerts for detected faults

**Medium-term:**
- TensorFlow Lite quantization (embedded deployment)
- Onboard inference (Pixhawk, DJI SDK)
- Cloud-based monitoring backend

**Long-term:**
- Fleet-wide analytics dashboard
- Remaining Useful Life (RUL) prediction
- Integration with maintenance scheduling

**To contribute:**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/your-feature`)
3. Commit with clear messages
4. Push and create Pull Request

---

## 👥 Team

**University of Cincinnati Senior Design Project (Fall 2025 – Spring 2026)**

- **Siddharth Urankar** (CS) — ML/Signal Processing, Backend Development
  - Email: siddharth.urankar@gmail.com | [GitHub](https://github.com/siddharthurankar)
  - Hours: 192 (design, ML pipeline, software engineering, testing)

- **Prissha Chawla** (CS) — Full-Stack Software, Dashboard UI/UX
  - Email: chawlaps@uc.edu
  - Hours: System design, user interface, testing

- **Ally Blair** (ME) — Hardware Integration, Mechanical Design
  - Email: blairar@mail.uc.edu
  - Hours: Motor test setup, data collection, validation

**Faculty Advisor:** Dr. Manish Kumar (UC, Mechanical Engineering)

**Industry Collaborators:** Dr. Chetan Kulkarni (NASA Ames)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file

**Third-party licenses:**
- TensorFlow: Apache 2.0  
- Streamlit: Apache 2.0
- Librosa: BSD
- scikit-learn: BSD

---

## 🎓 Citation

If you use this work in research:

```bibtex
@software{urankar_uavhealth_2026,
  author = {Urankar, Siddharth and Chawla, Prissha and Blair, Ally},
  title = {UAV Motor Health Monitoring via Acoustic Anomaly Detection},
  year = {2026},
  url = {https://github.com/siddharthurankar/UAV-HealthMonitoring},
  institution = {University of Cincinnati}
}
```

---

## 🔗 Links & Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/siddharthurankar/UAV-HealthMonitoring/issues)
- **Email:** siddharth.urankar@gmail.com
- **Documentation:** See [CS5002 Final Design Report](../CS5002%20Final%20Design%20Report.md)

---

**Last Updated:** April 10, 2026 | **Status:** Production Ready (v1.0)

