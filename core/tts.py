"""
Text-to-Speech module for audio feedback from the assistant.
"""

import pyttsx3
from loguru import logger

# Initialize TTS engine once
_tts_engine = None

def initialize_tts():
    """Initialize the TTS engine with optimal settings."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty('rate', 150)        # Speaking rate (150-200 is normal)
        _tts_engine.setProperty('volume', 0.9)      # Volume (0.0 to 1.0)
        logger.info("TTS engine initialized")
    return _tts_engine

def speak(text: str, wait: bool = True) -> None:
    """
    Speak the given text using TTS.
    
    Args:
        text: Text to speak
        wait: If True, wait for speech to finish before returning
    """
    engine = initialize_tts()
    logger.info(f"Speaking: {text[:100]}...")
    
    try:
        engine.say(text)
        if wait:
            engine.runAndWait()
        logger.debug("Speech completed")
    except Exception as e:
        logger.error(f"Error during speech: {e}")

def speak_async(text: str) -> None:
    """
    Speak text without waiting for completion (non-blocking).
    
    Args:
        text: Text to speak
    """
    speak(text, wait=False)

def stop_speaking() -> None:
    """Stop any ongoing speech."""
    engine = initialize_tts()
    engine.stop()
    logger.info("Speech stopped")

def set_voice_properties(rate: int = 150, volume: float = 0.9) -> None:
    """
    Set TTS engine properties.
    
    Args:
        rate: Speaking rate (50-300, default 150)
        volume: Volume level (0.0-1.0, default 0.9)
    """
    engine = initialize_tts()
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)
    logger.info(f"TTS properties set: rate={rate}, volume={volume}")

def cleanup_tts():
    """Clean up TTS engine resources."""
    global _tts_engine
    if _tts_engine is not None:
        try:
            _tts_engine.stop()
            del _tts_engine
            _tts_engine = None
            logger.info("TTS engine cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up TTS: {e}")
