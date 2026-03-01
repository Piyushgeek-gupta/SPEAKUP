"""
Core modules for SpeakUp voice control system.

Includes:
- hotkey: Hotkey detection and triggering
- stt: Speech-to-text transcription
- llm: Large language model inference
- tts: Text-to-speech audio feedback
- prompts: System and user instruction templates
"""

__version__ = "0.1.0"
__author__ = "SpeakUp Team"

from . import hotkey, stt, llm, tts, prompts

__all__ = ["hotkey", "stt", "llm", "tts", "prompts"]
