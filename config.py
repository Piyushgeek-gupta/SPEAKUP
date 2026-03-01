"""
Configuration and initialization module for SpeakUp
"""

from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.absolute()
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create necessary directories
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Model configuration
QWEN_MODEL_PATH = MODELS_DIR / "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
WHISPER_MODEL_SIZE = "base.en"  # or "small", "medium", "large"

# LLM Configuration
LLM_CONFIG = {
    "n_ctx": 4096,           # Context window size
    "n_gpu_layers": 0,       # Set >0 if you have CUDA/Metal support
    "n_threads": 8,          # Number of CPU threads
    "temperature": 0.3,      # Lower = more deterministic
    "max_tokens": 1024,
}

# TTS Configuration
TTS_CONFIG = {
    "rate": 150,             # Speaking rate (50-300)
    "volume": 0.9,           # Volume (0.0-1.0)
}

# STT Configuration
STT_CONFIG = {
    "sample_rate": 16000,    # Sample rate in Hz
    "channels": 1,           # Mono audio
    "duration": 10.0,        # Max recording duration
}

# Hotkey configuration
HOTKEY_CONFIG = {
    "hotkey": "alt+v",        # Hold Alt+V to record voice
}

# Audio configuration
AUDIO_CONFIG = {
    "input_device": None,    # None = default device
    "record_sample_rate": 16000,
}

def get_model_path():
    """Get the full path to the Qwen model."""
    return QWEN_MODEL_PATH

def verify_model_exists():
    """Check if the Qwen model file exists."""
    if not QWEN_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at {QWEN_MODEL_PATH}\n"
            f"Please download Qwen2.5-7B-Instruct-Q4_K_M.gguf and place it in {MODELS_DIR}"
        )
    return True

def initialize_configuration():
    """Initialize and validate configuration at startup."""
    try:
        verify_model_exists()
        return True
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}")
        return False
