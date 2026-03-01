"""
Speech-to-Text module for capturing and transcribing voice input.
"""

import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
from loguru import logger

# Initialize Whisper model once
_whisper_model = None

def load_stt_model(model_size: str = "base.en"):
    """
    Load the Whisper model for STT.
    
    Args:
        model_size: Model size ('tiny', 'base', 'small', 'medium', 'large')
        
    Returns:
        WhisperModel instance
    """
    global _whisper_model
    
    if _whisper_model is not None:
        return _whisper_model
    
    logger.info(f"Loading Whisper model: {model_size}")
    try:
        _whisper_model = WhisperModel(model_size, device="cpu")
        logger.info("Whisper model loaded successfully")
        return _whisper_model
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {e}")
        raise

def listen_for_audio(duration: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
    """
    Record audio from the microphone.
    
    Args:
        duration: Duration in seconds to record
        sample_rate: Sample rate in Hz (16000 is standard for Whisper)
        
    Returns:
        numpy array containing audio data
    """
    logger.info(f"Recording audio for {duration} seconds...")
    
    try:
        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        logger.info("Audio recording completed")
        return audio
    except Exception as e:
        logger.error(f"Error recording audio: {e}")
        raise

def transcribe_audio(audio: np.ndarray) -> str:
    """
    Transcribe audio to text using Whisper.
    
    Args:
        audio: numpy array of audio data
        
    Returns:
        Transcribed text
    """
    model = load_stt_model()
    logger.info("Transcribing audio...")
    
    try:
        # Convert float32 to proper format if needed
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Ensure audio is in [-1, 1] range
        max_val = np.max(np.abs(audio))
        if max_val > 1:
            audio = audio / max_val
        
        # Transcribe
        segments, info = model.transcribe(
            audio,
            vad_filter=True,      # Use Voice Activity Detection
            language="en"
        )
        
        # Combine all segments
        full_text = " ".join([segment.text for segment in segments])
        logger.info(f"Transcribed: {full_text}")
        return full_text.strip()
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise

def record_and_transcribe(duration: float = 5.0) -> str:
    """
    Record audio and transcribe in one call.
    
    Args:
        duration: Duration in seconds to record
        
    Returns:
        Transcribed text
    """
    audio = listen_for_audio(duration)
    text = transcribe_audio(audio)
    return text

def unload_stt_model():
    """Unload the STT model to free up memory."""
    global _whisper_model
    if _whisper_model is not None:
        del _whisper_model
        _whisper_model = None
        logger.info("STT model unloaded")
