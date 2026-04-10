"""
Streamlit-free motor anomaly pipeline: preprocessing, inference, visualization.
Safe to import from a future FastAPI/GRPC service.
"""
from __future__ import annotations

import io
import logging
import time
from typing import Any, Dict, Optional, Tuple

import librosa
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


def load_audio_from_path(path_str: str) -> Tuple[np.ndarray, int]:
    """Load waveform from disk (no caching — caller owns caching policy)."""
    audio, sr = librosa.load(path_str, sr=None)
    return audio, int(sr)


def mel_scaled_spec_from_audio(audio: np.ndarray, sr: int, scaler) -> Tuple[np.ndarray, np.ndarray]:
    """Mel 128×44 + scaler (same math as production model). Returns (orig_spec (128,44), model_input (1,44,128))."""
    mel = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
    db = librosa.power_to_db(mel, ref=np.max)

    db_norm = (db - db.min()) / (db.max() - db.min() + 1e-6)
    pad_width = max(0, 44 - db_norm.shape[1])
    db_norm = np.pad(db_norm, ((0, 0), (0, pad_width)))[:, :44]

    flattened = db_norm.reshape(1, -1)
    scaled = np.clip(scaler.transform(flattened), 0, 1)
    spec_2d = scaled.reshape(1, 128, 44)
    model_input = np.transpose(spec_2d, (0, 2, 1)).astype(np.float32, copy=False)
    orig_spec = spec_2d[0].astype(np.float32, copy=False)
    return orig_spec, model_input


def run_autoencoder(model, model_input: np.ndarray) -> Tuple[np.ndarray, float]:
    recon = model.predict(model_input, verbose=0)
    mse = float(np.mean(np.square(model_input - recon)))
    return recon, mse


def recon_to_recon_spec(recon: np.ndarray) -> np.ndarray:
    return np.transpose(recon[0], (1, 0)).astype(np.float32, copy=False)


def run_full_inference(
    audio: np.ndarray,
    sr: int,
    model,
    scaler,
    timings_ms: Optional[Dict[str, Any]] = None,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Single forward pass: mel + scale + predict + MSE.
    Returns (mse, recon_spec, orig_spec). orig_spec avoids a second mel pass for visualization.

    If timings_ms is a dict, writes preprocess_ms and inference_ms (wall time, milliseconds).
    """
    t0 = time.perf_counter()
    orig_spec, model_input = mel_scaled_spec_from_audio(audio, sr, scaler)
    if timings_ms is not None:
        timings_ms["preprocess_ms"] = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    recon, mse = run_autoencoder(model, model_input)
    recon_spec = recon_to_recon_spec(recon)
    if timings_ms is not None:
        timings_ms["inference_ms"] = (time.perf_counter() - t0) * 1000.0

    return mse, recon_spec, orig_spec


def spectrogram_comparison_png(orig_spec: np.ndarray, recon_spec: np.ndarray, dpi: int = 110) -> bytes:
    diff = 1.0 - np.abs(orig_spec - recon_spec)
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    ax[0].imshow(orig_spec, aspect="auto", origin="lower", cmap="magma")
    ax[0].set_title("Actual Sound")
    ax[1].imshow(recon_spec, aspect="auto", origin="lower", cmap="magma")
    ax[1].set_title("AI Prediction")
    ax[2].imshow(diff, aspect="auto", origin="lower", cmap="gray", vmin=0, vmax=1)
    ax[2].set_title("Anomaly Heatmap")
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def validate_audio(audio: np.ndarray, sr: int) -> Tuple[bool, str]:
    if audio.size == 0:
        return False, "Audio is empty."
    if sr <= 0:
        return False, "Invalid sample rate."
    return True, ""


def log_timings(path_str: str, *, audio_ms: float, preprocess_ms: float, inference_ms: float, viz_ms: float) -> None:
    logger.info(
        "motor_pipeline timings path=%s audio_ms=%.2f preprocess_ms=%.2f inference_ms=%.2f viz_ms=%.2f",
        path_str,
        audio_ms,
        preprocess_ms,
        inference_ms,
        viz_ms,
    )
