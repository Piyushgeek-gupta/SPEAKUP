"""
Hotkey module for detecting Alt+V key press and release.
Recording happens while the key is held down.
"""

import keyboard
import threading
import time
from loguru import logger
from typing import Callable, Optional

# Global state
_is_pressed = False
_press_time = None

def setup_hotkey(on_while_held: Callable) -> None:
    """
    Setup the hotkey listener for Alt+V.
    Records voice while the key is held down.
    
    Args:
        on_while_held: Callback function that runs while hotkey is held
    """
    global _is_pressed, _press_time
    
    logger.info("Setting up hotkey listener for Alt+V...")
    logger.info("Hold Alt+V to record, release to process")
    
    def _on_key_press(event: keyboard.KeyboardEvent):
        """Handle Alt+V press - start recording immediately."""
        global _is_pressed, _press_time
        
        # Only trigger on 'v' key with alt modifier
        if event.name == 'v' and keyboard.is_pressed('alt'):
            if not _is_pressed:
                _is_pressed = True
                _press_time = time.time()
                logger.debug("Alt+V pressed - Starting voice recording...")
                # Start recording in a thread
                threading.Thread(target=on_while_held, daemon=True).start()
    
    def _on_key_release(event: keyboard.KeyboardEvent):
        """Handle Alt+V release - stop recording."""
        global _is_pressed
        
        if event.name == 'v' and not keyboard.is_pressed('alt'):
            if _is_pressed:
                _is_pressed = False
                logger.debug("Alt+V released - Stopping voice recording")
    
    try:
        # Register listeners
        keyboard.on_press(callback=_on_key_press)
        keyboard.on_release(callback=_on_key_release)
        logger.info("Alt+V hotkey listener setup complete")
    except Exception as e:
        logger.error(f"Failed to setup hotkey: {e}")
        raise

def wait_for_hotkey() -> None:
    """
    Block and wait for keyboard events.
    This should be called in the main thread.
    """
    logger.info("Waiting for hotkey (Alt+V)... Press Ctrl+C to exit")
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        logger.info("Keyboard listener stopped")

def cleanup_hotkey() -> None:
    """Clean up hotkey listeners."""
    try:
        keyboard.clear_all_hotkeys()
        logger.info("Hotkey listeners cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up hotkeys: {e}")

def is_hotkey_pressed() -> bool:
    """Check if the hotkey is currently pressed."""
    return _is_pressed

def get_press_duration() -> float:
    """Get how long the hotkey has been held in seconds."""
    global _press_time
    if _press_time is not None and _is_pressed:
        return time.time() - _press_time
    return 0.0
