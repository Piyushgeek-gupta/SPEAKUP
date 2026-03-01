"""
LLM module for loading and interfacing with the Qwen model.
"""

import json
import os
from pathlib import Path
from llama_cpp import Llama
from loguru import logger
from core.prompts import get_system_instruction, get_user_instruction

# Model configuration
MODEL_PATH = Path("models/Qwen2.5-7B-Instruct-Q4_K_M.gguf")
_llm_instance = None

def load_model() -> Llama:
    """
    Load the Qwen model. Returns cached instance if already loaded.
    """
    global _llm_instance
    
    if _llm_instance is not None:
        return _llm_instance
    
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH.absolute()}")
    
    logger.info(f"Loading model from {MODEL_PATH}")
    
    try:
        _llm_instance = Llama(
            model_path=str(MODEL_PATH.absolute()),
            n_ctx=4096,           # Context window
            n_gpu_layers=0,       # Set to >0 if you have CUDA/Metal GPU support
            n_threads=8,          # CPU threads
            verbose=False
        )
        logger.info("Model loaded successfully")
        return _llm_instance
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def process_command(user_voice_input: str, conversation_context: str = "") -> dict:
    """
    Process a user voice command through the LLM with conversation context.
    
    Args:
        user_voice_input: The transcribed voice command from STT
        conversation_context: Previous conversation history for context
        
    Returns:
        dict with keys:
            - 'understood': bool - whether model clearly understood the command
            - 'action_steps': list - ordered steps to execute
            - 'clarification': str or None - question if clarification needed
    """
    llm = load_model()
    system_inst = get_system_instruction()
    
    # Include conversation context if available
    if conversation_context:
        user_inst = f"Previous conversation context:\n{conversation_context}\n\nNew user command: {user_voice_input}"
    else:
        user_inst = f"User command: {user_voice_input}"
    
    logger.info(f"Processing command: {user_voice_input}")
    if conversation_context:
        logger.debug(f"With conversation context from {len(conversation_context)} characters")
    
    try:
        full_prompt = f"{system_inst}\n\n{user_inst}"
        
        response = llm.create_completion(
            prompt=full_prompt,
            max_tokens=1024,
            temperature=0.3,  # Lower temperature for more deterministic output
            top_p=0.9,
            stop=["```\n"],
        )
        
        response_text = response["choices"][0]["text"].strip()
        logger.debug(f"LLM raw response: {response_text}")
        
        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                # Try to find JSON object directly
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
            else:
                json_str = response_text
                
            result = json.loads(json_str)
            logger.info(f"Parsed result: understood={result.get('understood')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Fallback: treat as action steps if it looks like text
            return {
                "understood": True,
                "action_steps": [line.strip() for line in response_text.split('\n') if line.strip()],
                "clarification": None
            }
            
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise

def process_clarification(clarification_answer: str, context: str = "") -> dict:
    """
    Process a clarification response from the user.
    
    Args:
        clarification_answer: User's response to clarification question
        context: Previous conversation context
        
    Returns:
        dict with action_steps and any remaining clarifications
    """
    llm = load_model()
    system_inst = get_system_instruction()
    
    logger.info(f"Processing clarification: {clarification_answer}")
    
    if context:
        prompt = f"{system_inst}\n\nPrevious context:\n{context}\n\nUser clarification: {clarification_answer}\n\nNow provide the complete action steps in JSON format."
    else:
        prompt = f"{system_inst}\n\nThe user has provided: {clarification_answer}\n\nPlease analyze and provide step-by-step instructions in the required JSON format."
    
    try:
        response = llm.create_completion(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.3,
            top_p=0.9,
        )
        
        response_text = response["choices"][0]["text"].strip()
        
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
            else:
                json_str = response_text
                
            result = json.loads(json_str)
            return result
            
        except json.JSONDecodeError:
            return {
                "understood": True,
                "action_steps": [line.strip() for line in response_text.split('\n') if line.strip()],
                "clarification": None
            }
            
    except Exception as e:
        logger.error(f"Error calling LLM for clarification: {e}")
        raise

def unload_model():
    """Unload the model to free up memory."""
    global _llm_instance
    if _llm_instance is not None:
        del _llm_instance
        _llm_instance = None
        logger.info("Model unloaded")
