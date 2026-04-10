from __future__ import annotations

import contextvars
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

from motor_pipeline import (
    load_audio_from_path,
    log_timings,
    run_full_inference,
    spectrogram_comparison_png,
    validate_audio,
)

# =============================================================================
# A) CONFIG & PATHS
# =============================================================================
CODE_VERSION = "v1"
BASE_DIR = Path(__file__).resolve().parent
TEST_FILES_DIR = BASE_DIR / "Test_Files"
EXPO_DIR = BASE_DIR / "ExpoModel"
METADATA_PATH = BASE_DIR / "file_metadata_log.csv"
MODEL_VERSION_FILE = EXPO_DIR / "model_version.txt"


def list_wav_files_shuffled() -> list[str]:
    files = [f for f in os.listdir(TEST_FILES_DIR) if f.endswith(".wav")]
    random.shuffle(files)
    return files


# True only while st.cache_data user function body runs (cache MISS). Unset via reset before each call.
_ANALYSIS_CACHE_BODY_EXECUTED: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "analysis_cache_body_executed", default=False
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _mark_analysis_cache_body_executed() -> None:
    _ANALYSIS_CACHE_BODY_EXECUTED.set(True)


def infer_cache_hit_from_execution_marker() -> bool:
    """HIT iff cached_analyze body did not run (marker stayed False)."""
    return not _ANALYSIS_CACHE_BODY_EXECUTED.get()


# =============================================================================
# B) SESSION STATE
# =============================================================================
def _init_session_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_analysis" not in st.session_state:
        st.session_state.last_analysis = None
    if "played_filenames" not in st.session_state:
        st.session_state.played_filenames = set()
    if "trigger_autoplay_for" not in st.session_state:
        st.session_state.trigger_autoplay_for = None
    if "f16_last_viz_regen_ms" not in st.session_state:
        st.session_state.f16_last_viz_regen_ms = None
    if "f16_viz_convert_ms" not in st.session_state:
        st.session_state.f16_viz_convert_ms = None
    if "f16_viz_mpl_ms" not in st.session_state:
        st.session_state.f16_viz_mpl_ms = None
    if "analyzed_filenames" not in st.session_state:
        st.session_state.analyzed_filenames = set()
    if "wav_file_order" not in st.session_state:
        st.session_state.wav_file_order = list_wav_files_shuffled()


_init_session_state()


def clear_session():
    st.session_state.history = []
    st.session_state.last_analysis = None
    st.session_state.played_filenames = set()
    st.session_state.trigger_autoplay_for = None
    st.session_state.f16_last_viz_regen_ms = None
    st.session_state.f16_viz_convert_ms = None
    st.session_state.f16_viz_mpl_ms = None
    st.session_state.analyzed_filenames = set()
    st.session_state.wav_file_order = list_wav_files_shuffled()


# =============================================================================
# C) PAGE SETUP (lightweight; no TF at import)
# =============================================================================
st.set_page_config(page_title="Motor Health AI Diagnostic", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); border: 1px solid #eee; }
    .status-text { font-size: 28px; font-weight: bold; text-align: center; margin-top: 10px; }
    .metadata-box { background-color: #f1f3f6; padding: 15px; border-radius: 10px; border-left: 5px solid #004d40; margin-bottom: 10px; }
    .label-healthy { color: #28a745; font-weight: bold; border: 1px solid #28a745; padding: 2px 8px; border-radius: 5px; background: #e8f5e9; }
    .label-faulty { color: #dc3545; font-weight: bold; border: 1px solid #dc3545; padding: 2px 8px; border-radius: 5px; background: #ffebee; }
    .file-locked { color: #9e9e9e !important; text-decoration: line-through; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# D) DATA LOADING & CACHE KEYS (Streamlit layer only)
# =============================================================================
def read_model_version_label() -> str:
    if MODEL_VERSION_FILE.exists():
        return MODEL_VERSION_FILE.read_text(encoding="utf-8").strip() or "unknown"
    return "unknown"


def get_runtime_fingerprint() -> str:
    """Lightweight env slice for cache invalidation across Python / TF upgrades."""
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    try:
        import importlib.metadata as im

        tf_ver = im.version("tensorflow")
    except Exception:
        tf_ver = "unknown"
    return f"py:{py}|tf:{tf_ver}"


def get_analysis_cache_key() -> str:
    """ML cache fingerprint: code + runtime + on-disk model assets. Metadata CSV is excluded."""
    parts = [
        f"code:{CODE_VERSION}",
        get_runtime_fingerprint(),
        read_model_version_label(),
    ]
    for rel in ("Autoencoder_Final.h5", "scaler.pkl", "threshold.txt"):
        p = EXPO_DIR / rel
        parts.append(f"{rel}:{p.stat().st_mtime_ns}" if p.exists() else f"{rel}:missing")
    return "|".join(parts)


@st.cache_resource(show_spinner="Initializing Neural Engine...")
def load_assets():
    import tensorflow as tf
    import joblib

    model = tf.keras.models.load_model(
        EXPO_DIR / "Autoencoder_Final.h5",
        custom_objects={"mse": tf.keras.losses.MeanSquaredError()},
    )
    scaler = joblib.load(EXPO_DIR / "scaler.pkl")
    with open(EXPO_DIR / "threshold.txt", "r") as f:
        threshold = float(f.read().strip())
    return model, scaler, threshold


def metadata_mtime_ns() -> int:
    return int(METADATA_PATH.stat().st_mtime_ns) if METADATA_PATH.exists() else 0


@st.cache_data(show_spinner=False, max_entries=8)
def load_metadata_cached(meta_mtime_ns: int) -> Optional[pd.DataFrame]:
    """CSV read cached until metadata file mtime changes (keyed by meta_mtime_ns)."""
    if not METADATA_PATH.exists():
        return None
    _ = meta_mtime_ns
    return pd.read_csv(METADATA_PATH)


def lookup_recording_metadata(selected_file: str, metadata_df) -> dict:
    motor_info = prop_info = "N/A"
    cond_num = "N/A"
    cond_desc = "Unknown Condition"
    if metadata_df is not None:
        match = metadata_df[metadata_df["filename"] == selected_file]
        if not match.empty:
            motor_info = match.iloc[0]["motor"]
            prop_info = match.iloc[0]["propeller"]
            cond_num = match.iloc[0]["condition"]
            cond_desc = match.iloc[0]["condition_desc"]
    return {
        "motor_info": motor_info,
        "prop_info": prop_info,
        "cond_num": cond_num,
        "cond_desc": cond_desc,
    }


def env_warm_start_enabled() -> bool:
    return os.environ.get("MOTOR_AI_WARM_START", "").strip().lower() in ("1", "true", "yes")


# =============================================================================
# E) PURE COMPUTE (no load_assets, no logging, no metadata)
# =============================================================================
def compute_analysis_payload(
    path_str: str,
    model,
    scaler,
    threshold: float,
    viz_mode: str,
) -> dict:
    """
    Load audio → mel + scaler + inference + viz artifact. Caller supplies model artifacts.
    """
    timings: Dict[str, Any] = {}
    t0 = time.perf_counter()
    audio, sr = load_audio_from_path(path_str)
    timings["audio_load_ms"] = (time.perf_counter() - t0) * 1000.0

    ok, err_msg = validate_audio(audio, sr)
    if not ok:
        raise ValueError(err_msg)

    inf_timings: dict = {}
    mse, recon_spec, orig_spec = run_full_inference(audio, sr, model, scaler, timings_ms=inf_timings)
    timings["preprocess_ms"] = inf_timings.get("preprocess_ms", 0.0)
    timings["inference_ms"] = inf_timings.get("inference_ms", 0.0)

    t_v0 = time.perf_counter()
    if viz_mode == "png":
        viz_png = spectrogram_comparison_png(orig_spec, recon_spec)
        orig_f16 = recon_f16 = None
    else:
        viz_png = None
        orig_f16 = orig_spec.astype("float16")
        recon_f16 = recon_spec.astype("float16")
    timings["viz_ms"] = (time.perf_counter() - t_v0) * 1000.0

    timings["total_compute_ms"] = (
        timings["audio_load_ms"]
        + timings["preprocess_ms"]
        + timings["inference_ms"]
        + timings["viz_ms"]
    )
    timings["cache_created_at"] = time.time()

    selected_file = Path(path_str).name
    status = "FAULTY" if mse > threshold else "HEALTHY"
    status_color = "#dc3545" if status == "FAULTY" else "#28a745"
    orig_status = "HEALTHY" if selected_file.upper().startswith("H") else "FAULTY"
    orig_class = "label-healthy" if orig_status == "HEALTHY" else "label-faulty"

    return {
        "selected_file": selected_file,
        "file_path": path_str,
        "mse": mse,
        "threshold": threshold,
        "status": status,
        "status_color": status_color,
        "orig_status": orig_status,
        "orig_class": orig_class,
        "viz_mode": viz_mode,
        "viz_png": viz_png,
        "orig_spec_f16": orig_f16,
        "recon_spec_f16": recon_f16,
        "timings_ms": timings,
    }


# max_entries: lower ⇒ less RAM/disk for serialized cache blobs; higher ⇒ fewer recomputes when
# many distinct (path, mtime, key, viz) combinations are used. Tune for deployment footprint.
@st.cache_data(show_spinner="Analyzing...", max_entries=48)
def cached_analyze(path_str: str, audio_mtime_ns: int, analysis_cache_key: str, viz_mode: str) -> dict:
    """
    Cacheable layer only: marks execution (for HIT/MISS detection), loads assets, delegates to pure compute.
    Not hashable: model/scaler stay inside; identity captured by analysis_cache_key.
    """
    _mark_analysis_cache_body_executed()
    model, scaler, threshold = load_assets()
    return compute_analysis_payload(path_str, model, scaler, threshold, viz_mode)


def merge_metadata_into_payload(ml_payload: dict, metadata_df: Optional[pd.DataFrame]) -> dict:
    meta = lookup_recording_metadata(ml_payload["selected_file"], metadata_df)
    return {**ml_payload, **meta}


def record_analysis_observability(
    path_str: str,
    *,
    cache_hit: bool,
    wall_ms: float,
    payload: dict,
    strict_debug: bool,
) -> None:
    """Logging outside st.cache_data."""
    t = payload.get("timings_ms") or {}
    compute_ms = float(t.get("total_compute_ms", 0.0))
    if strict_debug:
        logger.info(
            "STRICT_DEBUG record_analysis_observability path=%s cache_hit=%s wall_ms=%.2f cache_created_at=%s",
            path_str,
            cache_hit,
            wall_ms,
            t.get("cache_created_at"),
        )
    if cache_hit:
        logger.info(
            "analysis_done path=%s cache_hit=True wall_ms=%.2f",
            path_str,
            wall_ms,
        )
    else:
        log_timings(
            path_str,
            audio_ms=float(t.get("audio_load_ms", 0.0)),
            preprocess_ms=float(t.get("preprocess_ms", 0.0)),
            inference_ms=float(t.get("inference_ms", 0.0)),
            viz_ms=float(t.get("viz_ms", 0.0)),
        )
        logger.info(
            "analysis_done path=%s cache_hit=False wall_ms=%.2f compute_ms=%.2f cache_created_at=%s",
            path_str,
            wall_ms,
            compute_ms,
            t.get("cache_created_at"),
        )


def pack_last_analysis(
    cached: dict,
    *,
    from_cache: bool,
    wall_total_ms: float,
    cache_key: str,
) -> dict:
    return {
        "selected_file": cached["selected_file"],
        "file_path": cached["file_path"],
        "mse": cached["mse"],
        "threshold": cached["threshold"],
        "status": cached["status"],
        "status_color": cached["status_color"],
        "orig_status": cached["orig_status"],
        "orig_class": cached["orig_class"],
        "motor_info": cached["motor_info"],
        "prop_info": cached["prop_info"],
        "cond_num": cached["cond_num"],
        "cond_desc": cached["cond_desc"],
        "viz_mode": cached["viz_mode"],
        "viz_png": cached["viz_png"],
        "orig_spec_f16": cached["orig_spec_f16"],
        "recon_spec_f16": cached["recon_spec_f16"],
        "from_cache": from_cache,
        "wall_total_ms": wall_total_ms,
        "timings_ms": cached.get("timings_ms"),
        "cache_key": cache_key,
    }


# =============================================================================
# F) UI RENDERING
# =============================================================================
def _viz_bytes_for_display_detailed(data: dict) -> Tuple[bytes, Dict[str, float]]:
    """Returns (png_bytes, timing_ms dict); timing keys only for f16 regeneration path."""
    if data["viz_mode"] == "png" and data.get("viz_png"):
        return data["viz_png"], {}
    t0 = time.perf_counter()
    o = data["orig_spec_f16"].astype("float32")
    r = data["recon_spec_f16"].astype("float32")
    convert_ms = (time.perf_counter() - t0) * 1000.0
    t1 = time.perf_counter()
    png = spectrogram_comparison_png(o, r)
    mpl_ms = (time.perf_counter() - t1) * 1000.0
    return png, {"f16_to_float32_ms": convert_ms, "matplotlib_png_ms": mpl_ms}


def render_dashboard_from_analysis(
    data: dict,
    *,
    allow_autoplay: bool,
    debug_mode: bool = False,
    strict_debug: bool = False,
):
    status = data["status"]
    status_color = data["status_color"]
    mse = data["mse"]
    THRESHOLD = data["threshold"]
    selected_file = data["selected_file"]
    file_path = data["file_path"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"<div class='metric-card'><p style='margin:0;color:#666;'>AI Diagnosis</p>"
            f"<div class='status-text' style='color:{status_color}'>{status}</div></div>",
            unsafe_allow_html=True,
        )
    with m2:
        st.metric(
            "Reconstruction Error (MSE)",
            f"{mse:.6f}",
            delta=f"{mse - THRESHOLD:.6f}" if status == "FAULTY" else None,
            delta_color="inverse",
        )
    with m3:
        st.metric("Healthy Threshold", f"{THRESHOLD:.6f}")
    with m4:
        wall = data.get("wall_total_ms")
        if wall is not None:
            st.metric("Total analysis (wall)", f"{wall:.1f} ms")

    src = data.get("from_cache")
    if src is not None:
        st.caption(
            f"**Cache:** {'HIT (disk cache)' if src else 'MISS (computed)'}  ·  "
            f"**Viz:** `{data.get('viz_mode', 'png')}`"
        )

    st.markdown("### 📋 Source Metadata & Recording Context")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
        <div class="metadata-box">
            <b>Original Lab Status:</b> <br>
            <span class="{data['orig_class']}">{data['orig_status']}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
        <div class="metadata-box">
            <b>Hardware Configuration:</b> <br>
            Motor: <code>{data['motor_info']}</code> | Propeller: <code>{data['prop_info']}</code>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
        <div class="metadata-box">
            <b>Condition #{data['cond_num']}:</b> <br>
            {data['cond_desc']}
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.divider()

    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("🔊 Audio Playback")
        played = st.session_state.played_filenames
        do_autoplay = False
        if allow_autoplay:
            if selected_file not in played:
                do_autoplay = True
                played.add(selected_file)
            else:
                st.info(
                    "This file was already played once this session. Use the player controls to listen again."
                )
        st.audio(file_path, autoplay=do_autoplay)
        st.markdown(f"**Analyzing File:** `{selected_file}`")
        st.info(
            "**Explanation:** The AI compares this sound to a mathematical model of a healthy motor. "
            "High error indicates mechanical irregularity."
        )

    with col_r:
        st.subheader("📊 Neural Signature Comparison")
        if data.get("viz_mode") == "f16":
            img_bytes, vdet = _viz_bytes_for_display_detailed(data)
            c_ms = vdet.get("f16_to_float32_ms", 0.0)
            m_ms = vdet.get("matplotlib_png_ms", 0.0)
            total_v = c_ms + m_ms
            st.session_state.f16_last_viz_regen_ms = total_v
            st.session_state.f16_viz_convert_ms = c_ms
            st.session_state.f16_viz_mpl_ms = m_ms
            cap = f"Regenerated spectrogram PNG from float16 tensors: **{total_v:.2f} ms** (this rerun)."
            if debug_mode:
                cap += f"  _(f16→float32: {c_ms:.2f} ms · matplotlib: {m_ms:.2f} ms)_"
            st.caption(cap)
        else:
            st.session_state.f16_last_viz_regen_ms = None
            st.session_state.f16_viz_convert_ms = None
            st.session_state.f16_viz_mpl_ms = None
            img_bytes, _ = _viz_bytes_for_display_detailed(data)
        st.image(img_bytes, use_container_width=True)

    with st.expander("Performance & timings", expanded=False):
        tm = data.get("timings_ms") or {}
        if tm:
            st.write(
                f"- Audio load: **{tm.get('audio_load_ms', 0):.2f} ms**\n"
                f"- Preprocess (mel + scale): **{tm.get('preprocess_ms', 0):.2f} ms**\n"
                f"- Model inference: **{tm.get('inference_ms', 0):.2f} ms**\n"
                f"- Visualization (at analysis / cache fill): **{tm.get('viz_ms', 0):.2f} ms**\n"
                f"- Sum (compute components): **{tm.get('total_compute_ms', 0):.2f} ms**"
            )
            if data.get("from_cache"):
                st.caption("Component timings are from the run that first populated this cache entry.")
        else:
            st.caption("No per-component timings available for this result.")
        if data.get("viz_mode") == "f16" and st.session_state.get("f16_last_viz_regen_ms") is not None:
            st.write(
                f"- **Spectrogram PNG regen (this page view, f16 mode):** "
                f"**{st.session_state.f16_last_viz_regen_ms:.2f} ms**"
            )
            if debug_mode:
                st.caption(
                    f"Split: f16→float32 **{st.session_state.f16_viz_convert_ms:.2f} ms** · "
                    f"matplotlib PNG **{st.session_state.f16_viz_mpl_ms:.2f} ms**"
                )

    if debug_mode:
        with st.expander("Debug: at-a-glance (last result)", expanded=False):
            tm = data.get("timings_ms") or {}
            cca = tm.get("cache_created_at")
            vr = st.session_state.get("f16_last_viz_regen_ms")
            vr_s = f"{vr:.2f} ms" if vr is not None else "N/A (png mode)"
            ck = data.get("cache_key", "")
            dbg_viz = ""
            if data.get("viz_mode") == "f16" and st.session_state.get("f16_viz_convert_ms") is not None:
                dbg_viz = (
                    f"| **f16→float32 (this rerun)** | **{st.session_state.f16_viz_convert_ms:.2f} ms** |\n"
                    f"| **matplotlib PNG (this rerun)** | **{st.session_state.f16_viz_mpl_ms:.2f} ms** |\n"
                )
            st.markdown(
                f"| Field | Value |\n| --- | --- |\n"
                f"| **Cache** | **{'HIT' if data.get('from_cache') else 'MISS'}** |\n"
                f"| **Detection** | `ContextVar`: body **{'skipped' if data.get('from_cache') else 'executed'}** |\n"
                f"| **Wall (cached_analyze)** | **{data.get('wall_total_ms', 0):.2f} ms** |\n"
                f"| **Compute sum (payload)** | **{tm.get('total_compute_ms', 0):.2f} ms** |\n"
                f"| **Viz at cache fill** | **{tm.get('viz_ms', 0):.2f} ms** |\n"
                f"| **Viz regen total (f16)** | **{vr_s}** |\n"
                f"{dbg_viz}"
                f"| **cache_created_at** | `{cca}` |\n"
            )
            st.text_area("Full cache key (ML fingerprint)", value=ck, height=100, disabled=True)
            if strict_debug:
                st.code(
                    "Execution path (last ANALYZE):\n"
                    "1. reset ContextVar marker → False\n"
                    "2. cached_analyze() → on MISS: body runs → marker True → compute_analysis_payload()\n"
                    "                       on HIT: body skipped → marker stays False\n"
                    "3. infer_cache_hit_from_execution_marker() → not marker\n"
                    "4. load_metadata_cached() + merge_metadata_into_payload()\n"
                    "5. record_analysis_observability()\n",
                    language="text",
                )


# =============================================================================
# G) SIDEBAR & ORCHESTRATION
# =============================================================================
with st.sidebar:
    st.image("UC.png", width=120)
    st.title("EXPO Control Panel")

    with st.expander("🎓 Project Credits", expanded=True):
        st.write("**University of Cincinnati**")
        st.write("Senior Design - Class of 2026")
        st.write("*Acoustic Anomaly Detection Team*")

    st.divider()

    warm_start = st.checkbox(
        "Warm start (preload model at startup)",
        value=False,
        help="Loads TensorFlow and weights while enabled (or set env MOTOR_AI_WARM_START=1). After the first load, @st.cache_resource keeps this cheap on reruns.",
        key="warm_start",
    )

    viz_storage = st.radio(
        "Visualization storage",
        options=("png", "f16"),
        format_func=lambda x: "PNG in cache (faster display, more RAM)" if x == "png" else "Float16 arrays (less RAM, render on view)",
        index=0,
        key="viz_storage_mode",
    )

    debug_mode = st.checkbox("Debug (cache diagnostics)", value=False, key="debug_cache")
    strict_debug = st.checkbox(
        "Strict debug (execution path)",
        value=False,
        help="Logs step-by-step path to terminal; execution-path panel in Debug expander.",
        key="strict_debug",
        disabled=not debug_mode,
    )

    all_files = st.session_state.wav_file_order
    analyzed = st.session_state.analyzed_filenames
    available_files = [f for f in all_files if f not in analyzed]

    if analyzed:
        with st.expander("Already analyzed (locked this session)", expanded=False):
            st.caption("Each file can be run only once until you clear the session.")
            for name in sorted(analyzed):
                st.markdown(f'<p class="file-locked">{name}</p>', unsafe_allow_html=True)

    if not available_files:
        st.info("All audio files have been analyzed once this session. **Clear Session** to unlock them.")
        selected_file = None
    else:
        selected_file = st.selectbox(
            "📁 Select Motor Audio File",
            available_files,
            key="file_selector",
        )

    run_btn = st.button(
        "🚀 ANALYZE MOTOR",
        use_container_width=True,
        type="primary",
        disabled=not available_files,
    )

    if st.button("Clear Session", use_container_width=True):
        clear_session()
        st.rerun()

    if debug_mode:
        st.divider()
        st.subheader("Debug")
        ck = get_analysis_cache_key()
        st.text_area("Current ML cache key fingerprint", value=ck, height=120, disabled=True)
        st.caption(
            f"`CODE_VERSION={CODE_VERSION}` · HIT/MISS via **ContextVar** (not wall time) · "
            f"metadata **not** in ML key · runtime `{get_runtime_fingerprint()}`"
        )

if warm_start or env_warm_start_enabled():
    load_assets()

st.title("🛡️ Motor Health Monitoring Dashboard")
st.caption("Real-Time Sound Signature Analysis using Neural Reconstruction")

analysis_error = None

strict_debug_effective = bool(debug_mode and strict_debug)

if run_btn and selected_file is not None:
    file_path = TEST_FILES_DIR / selected_file
    path_str = str(file_path.resolve())
    cache_key = get_analysis_cache_key()
    try:
        mtime_ns = int(file_path.stat().st_mtime_ns)
    except OSError as e:
        analysis_error = str(e)
        mtime_ns = 0

    if analysis_error is None:
        tok = _ANALYSIS_CACHE_BODY_EXECUTED.set(False)
        try:
            if strict_debug_effective:
                logger.info(
                    "STRICT_DEBUG: reset marker → False; calling cached_analyze(%s, ...)",
                    path_str,
                )
            t_wall0 = time.perf_counter()
            ml_only = cached_analyze(path_str, mtime_ns, cache_key, viz_storage)
            wall_ms = (time.perf_counter() - t_wall0) * 1000.0
            cache_hit = infer_cache_hit_from_execution_marker()
            if strict_debug_effective:
                logger.info(
                    "STRICT_DEBUG: cached_analyze returned; body_executed=%s → cache_hit=%s wall_ms=%.2f",
                    _ANALYSIS_CACHE_BODY_EXECUTED.get(),
                    cache_hit,
                    wall_ms,
                )
            meta_df = load_metadata_cached(metadata_mtime_ns())
            cached = merge_metadata_into_payload(ml_only, meta_df)
            record_analysis_observability(
                path_str,
                cache_hit=cache_hit,
                wall_ms=wall_ms,
                payload=cached,
                strict_debug=strict_debug_effective,
            )
            st.session_state.last_analysis = pack_last_analysis(
                cached,
                from_cache=cache_hit,
                wall_total_ms=wall_ms,
                cache_key=cache_key,
            )
            st.session_state.trigger_autoplay_for = selected_file
            st.session_state.history.insert(
                0,
                {
                    "File": selected_file,
                    "Status": st.session_state.last_analysis["status"],
                    "MSE Score": f"{st.session_state.last_analysis['mse']:.6f}",
                },
            )
            st.session_state.analyzed_filenames.add(selected_file)
        except Exception as e:
            analysis_error = str(e)
            logger.exception("Analysis failed for %s", path_str)
        finally:
            _ANALYSIS_CACHE_BODY_EXECUTED.reset(tok)

if analysis_error:
    st.error(f"Could not analyze: {analysis_error}")

la = st.session_state.last_analysis
if la is not None:
    allow_ap = st.session_state.trigger_autoplay_for == la["selected_file"]
    if allow_ap:
        st.session_state.trigger_autoplay_for = None

    render_dashboard_from_analysis(
        la,
        allow_autoplay=allow_ap,
        debug_mode=debug_mode,
        strict_debug=strict_debug_effective,
    )

if st.session_state.history:
    st.divider()
    st.subheader("📋 Session Analysis Log")
    st.dataframe(st.session_state.history, use_container_width=True)
