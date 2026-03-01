"""
Main orchestration pipeline for SpeakUp voice-controlled Windows automation.

Pipeline:
1. Hold Alt+V -> Start listening to voice input
2. Release Alt+V -> Process voice command through LLM
3. LLM response -> If clarification needed, ask user via TTS and listen for response
4. Action steps -> Execute steps using Windows automation libraries
5. Maintain conversation history for follow-up commands
"""

import sys
import time
from loguru import logger
from typing import Optional, List
import threading

from core.hotkey import setup_hotkey, wait_for_hotkey, cleanup_hotkey, is_hotkey_pressed, get_press_duration
from core.stt import record_and_transcribe, listen_for_audio, transcribe_audio
from core.llm import process_command, process_clarification, load_model
from core.tts import speak, cleanup_tts
from actions.executor import StepExecutor

# Configure logging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "speakup.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Global state
_is_recording = False
_current_audio = None
_executor = StepExecutor()
_conversation_history: List[str] = []  # Maintain context across commands
_recording_thread = None
_recorded_audio = None

def maintain_conversation_context(new_command: str) -> str:
    """
    Maintain conversation history for follow-up commands.
    
    Args:
        new_command: The new voice command
        
    Returns:
        Formatted conversation context
    """
    global _conversation_history
    
    # Keep last 5 commands for context (to avoid token overflow)
    _conversation_history.append(f"User: {new_command}")
    if len(_conversation_history) > 10:  # Keep 5 exchanges (user + response)
        _conversation_history.pop(0)
    
    # Format as conversation context
    context = "\n".join(_conversation_history)
    return context

def on_hotkey_while_held():
    """Callback while Alt+V is held - record voice continuously."""
    global _is_recording, _recorded_audio
    
    _is_recording = True
    logger.info("🎤 Alt+V held - Recording voice input...")
    speak("Listening...", wait=False)
    
    try:
        # Record audio while key is held
        # This function will continuously record until the key is released
        from core.stt import listen_for_audio
        
        # Record for a reasonable max duration (e.g., 15 seconds)
        # But it will be interrupted when hotkey is released
        max_duration = 15.0
        start_time = time.time()
        
        while _is_recording and (time.time() - start_time) < max_duration:
            # Keep checking if key is still pressed
            if not is_hotkey_pressed():
                logger.debug("Hotkey released, stopping recording")
                break
            time.sleep(0.1)
        
        logger.debug("Recording phase complete")
        
    except Exception as e:
        logger.error(f"Error during recording: {e}")
    finally:
        _is_recording = False

def on_hotkey_released():
    """Callback when Alt+V is released - process the recorded command."""
    global _is_recording, _recorded_audio
    
    if not _is_recording:
        return  # Already processed or wasn't recording
    
    _is_recording = False
    logger.info("🛑 Alt+V released - Processing voice command...")
    
    try:
        # Record audio (from the moment it was pressed)
        speak("Processing your command...", wait=True)
        logger.info("Recording audio input...")
        
        # Record for up to 10 seconds
        audio = listen_for_audio(duration=10)
        
        # Transcribe
        logger.info("Transcribing audio...")
        user_command = transcribe_audio(audio)
        
        if not user_command or user_command.strip() == "":
            speak("I didn't catch that. Please try again.")
            logger.warning("No speech detected")
            return
        
        # Add to conversation history
        context = maintain_conversation_context(user_command)
        
        logger.info(f"📝 User command: {user_command}")
        speak(f"You said: {user_command}", wait=True)
        
        # Process command through LLM with conversation history
        process_command_with_llm(user_command, context)
        
    except Exception as e:
        logger.error(f"Error processing hotkey release: {e}")
        speak("Sorry, there was an error processing your command.")

def process_command_with_llm(user_command: str, conversation_context: str = ""):
    """
    Process the user command through the LLM with visual context from OCR.
    Handle clarifications and execute steps.
    
    Args:
        user_command: The voice command
        conversation_context: Previous conversation history for context
    """
    global _conversation_history
    
    logger.info("🤖 Sending command to LLM...")
    
    # Get visual context from screen using OCR
    try:
        from core.ocr import get_context_for_command
        visual_context = get_context_for_command(user_command)
        combined_context = f"{conversation_context}\n\n{visual_context}"
        logger.debug("Visual context from OCR added to command")
    except Exception as e:
        logger.warning(f"Failed to get OCR context: {e}")
        combined_context = conversation_context
    
    try:
        # Combine current command with conversation context and visual context
        if conversation_context:
            # Remove the current command from context (it's already in conversation_context)
            context_lines = conversation_context.split('\n')
            # Take all but the last one (which is the current command we just added)
            previous_context = '\n'.join(context_lines[:-1]) if len(context_lines) > 1 else ""
            combined_input = f"Previous conversation:\n{previous_context}\n\nNew command: {user_command}" if previous_context else user_command
        else:
            combined_input = user_command
        
        # Get action steps from LLM with visual context
        result = process_command(combined_input, combined_context if combined_context else conversation_context)
        
        understood = result.get("understood", False)
        action_steps = result.get("action_steps", [])
        clarification = result.get("clarification", None)
        
        logger.debug(f"LLM Result: understood={understood}, steps={len(action_steps)}, clarification={clarification}")
        
        # Handle clarification if needed
        if not understood and clarification:
            logger.info(f"❓ LLM asks: {clarification}")
            speak(clarification, wait=True)
            
            # Listen for user's response
            logger.info("Listening for clarification response...")
            speak("Please answer:", wait=False)
            time.sleep(0.5)
            
            clarification_response = record_and_transcribe(duration=5)
            logger.info(f"Clarification response: {clarification_response}")
            
            # Add clarification to history
            _conversation_history.append(f"Assistant: {clarification}")
            _conversation_history.append(f"User: {clarification_response}")
            
            # Reprocess with clarification
            result = process_clarification(clarification_response, combined_input)
            understood = result.get("understood", True)
            action_steps = result.get("action_steps", [])
            clarification = result.get("clarification", None)
            
            if clarification:
                logger.warning(f"Still asking: {clarification}")
                speak(f"I still need more info: {clarification}")
                return
        
        # Execute the action steps
        if action_steps and understood:
            logger.info(f"✅ Got {len(action_steps)} steps to execute")
            speak(f"I'll execute {len(action_steps)} steps for you.")
            
            logger.info("Starting step execution...")
            for i, step in enumerate(action_steps, 1):
                logger.info(f"Step {i}: {step}")
            
            execute_steps(action_steps)
            
            # Add successful completion to history
            _conversation_history.append(f"System: Executed {len(action_steps)} steps successfully")
            
            speak("All steps completed successfully!")
            logger.info("✨ Execution finished")
        else:
            logger.warning("No action steps to execute")
            speak("I couldn't determine what to do. Please try again.")
    
    except Exception as e:
        logger.error(f"Error in LLM processing: {e}")
        speak(f"Error: {str(e)}")

def execute_steps(steps: list):
    """
    Execute the action steps from the LLM.
    
    Args:
        steps: List of action step instructions
    """
    logger.info(f"🚀 Executing {len(steps)} steps...")
    
    try:
        for i, step in enumerate(steps, 1):
            logger.info(f"Step {i}/{len(steps)}: {step}")
            speak(f"Executing step {i}: {step}", wait=False)
            
            if not _executor.execute_step(step):
                logger.warning(f"Step {i} failed to execute properly")
            
            # Small delay between steps
            time.sleep(0.5)
        
        logger.info("All steps executed")
        
    except Exception as e:
        logger.error(f"Error executing steps: {e}")
        raise

def main():
    """Main entry point for the SpeakUp application."""
    logger.info("=" * 60)
    logger.info("SpeakUp - Voice-Controlled Windows Automation")
    logger.info("=" * 60)
    
    try:
        # Load models at startup (this might take a moment)
        logger.info("⏳ Loading LLM and STT models...")
        speak("Loading models, please wait...", wait=False)
        load_model()  # Load LLM
        
        logger.info("✅ Models loaded successfully")
        speak("Ready! Hold Alt+V and speak your command.", wait=True)
        
        # Setup hotkey listener
        setup_hotkey(on_while_held=on_hotkey_while_held)
        
        logger.info("👂 Listening for hotkey (Alt+V)...")
        logger.info("Hold Alt+V to record voice, release to process")
        logger.info("Press Ctrl+C to exit")
        
        # Wait for hotkey events
        wait_for_hotkey()
        
    except KeyboardInterrupt:
        logger.info("Shutdown initiated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        speak(f"Error: {e}")
    finally:
        logger.info("Cleaning up resources...")
        cleanup_hotkey()
        cleanup_tts()
        logger.info("SpeakUp stopped")

if __name__ == "__main__":
    main()
