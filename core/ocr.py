"""
OCR Module - Uses Tesseract OCR to read screen and get coordinates.
Enables intelligent clicking and typing based on visual analysis of the screen.
"""

import pytesseract
import pyautogui
from PIL import Image
import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from typing import Dict, List, Tuple, Optional

# Configure pytesseract path (update if Tesseract not in PATH)
# pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenAnalyzer:
    """
    Analyzes screen using Tesseract OCR to extract text and coordinates.
    Enables intelligent interaction with any application.
    """
    
    def __init__(self):
        self.last_screenshot = None
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"Screen size: {self.screen_width}x{self.screen_height}")
    
    def take_screenshot(self) -> Image.Image:
        """
        Capture current screen and return as PIL Image.
        
        Returns:
            PIL.Image: Screenshot of current screen
        """
        try:
            screenshot = pyautogui.screenshot()
            self.last_screenshot = screenshot
            logger.debug("Screenshot captured successfully")
            return screenshot
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None
    
    def extract_text_with_coordinates(self, image: Image.Image = None) -> Dict:
        """
        Extract text and coordinates from image using Tesseract.
        
        Args:
            image: PIL Image (uses last screenshot if not provided)
        
        Returns:
            Dict with text elements and their coordinates:
            {
                "text": [{"text": "...", "x": 100, "y": 50, "width": 50, "height": 20}, ...],
                "raw_text": "Full extracted text",
                "confidence": average_confidence
            }
        """
        if image is None:
            image = self.take_screenshot()
        
        if image is None:
            return {"text": [], "raw_text": "", "confidence": 0}
        
        try:
            # Get detailed OCR data with coordinates
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume single block of text
            )
            
            # Extract text with coordinates
            text_elements = []
            confidences = []
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                confidence = int(ocr_data['conf'][i])
                
                # Skip low confidence or empty text
                if confidence < 30 or not text:
                    continue
                
                element = {
                    "text": text,
                    "x": ocr_data['left'][i],
                    "y": ocr_data['top'][i],
                    "width": ocr_data['width'][i],
                    "height": ocr_data['height'][i],
                    "confidence": confidence,
                    "center_x": ocr_data['left'][i] + ocr_data['width'][i] // 2,
                    "center_y": ocr_data['top'][i] + ocr_data['height'][i] // 2
                }
                
                text_elements.append(element)
                confidences.append(confidence)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Get full text
            raw_text = pytesseract.image_to_string(image)
            
            logger.debug(f"Extracted {len(text_elements)} text elements with avg confidence {avg_confidence:.1f}%")
            
            return {
                "text": text_elements,
                "raw_text": raw_text,
                "confidence": avg_confidence
            }
        
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {"text": [], "raw_text": "", "confidence": 0}
    
    def find_text_on_screen(self, search_text: str, image: Image.Image = None) -> Optional[Dict]:
        """
        Find specific text on screen and return its coordinates.
        
        Args:
            search_text: Text to search for (case-insensitive, partial match)
            image: PIL Image (uses last screenshot if not provided)
        
        Returns:
            Dict with matched element and coordinates, or None if not found
        """
        if image is None:
            image = self.take_screenshot()
        
        ocr_result = self.extract_text_with_coordinates(image)
        search_text_lower = search_text.lower()
        
        # First try exact match (after stripping)
        for element in ocr_result["text"]:
            if element["text"].lower() == search_text_lower:
                logger.info(f"Found exact match for '{search_text}' at ({element['center_x']}, {element['center_y']})")
                return element
        
        # Then try partial match
        for element in ocr_result["text"]:
            if search_text_lower in element["text"].lower():
                logger.info(f"Found partial match for '{search_text}' at ({element['center_x']}, {element['center_y']})")
                return element
        
        logger.warning(f"Text '{search_text}' not found on screen")
        return None
    
    def find_buttons(self, image: Image.Image = None) -> List[Dict]:
        """
        Detect button-like UI elements (typically all-caps, short text).
        
        Args:
            image: PIL Image (uses last screenshot if not provided)
        
        Returns:
            List of detected buttons with coordinates
        """
        if image is None:
            image = self.take_screenshot()
        
        ocr_result = self.extract_text_with_coordinates(image)
        buttons = []
        
        for element in ocr_result["text"]:
            text = element["text"]
            # Buttons are usually short, uppercase text
            if len(text) <= 20 and (text.isupper() or text in [
                "OK", "Save", "Cancel", "Delete", "Edit", "Add", "Next", 
                "Back", "Submit", "Login", "Sign Up", "Close", "Done", "Yes", "No"
            ]):
                element["type"] = "button"
                buttons.append(element)
        
        logger.info(f"Detected {len(buttons)} potential buttons")
        return buttons
    
    def find_input_fields(self, image: Image.Image = None) -> List[Dict]:
        """
        Detect text input fields by looking for underlines and empty spaces.
        
        Args:
            image: PIL Image (uses last screenshot if not provided)
        
        Returns:
            List of detected input fields with coordinates
        """
        if image is None:
            image = self.take_screenshot()
        
        try:
            # Convert to grayscale and detect lines (potential input field underlines)
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            
            # Detect horizontal lines
            edges = cv2.Canny(cv_image, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=5)
            
            input_fields = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Horizontal lines (potential input field underlines)
                    if abs(y2 - y1) < 5:  # Nearly horizontal
                        input_fields.append({
                            "type": "input_field",
                            "x": min(x1, x2),
                            "y": y1,
                            "width": abs(x2 - x1),
                            "height": 30,  # Estimate height
                            "center_x": (x1 + x2) // 2,
                            "center_y": y1 + 15
                        })
            
            # Remove duplicates (merge nearby fields)
            merged_fields = []
            for field in input_fields:
                is_duplicate = False
                for merged in merged_fields:
                    if abs(field["center_y"] - merged["center_y"]) < 30:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    merged_fields.append(field)
            
            logger.info(f"Detected {len(merged_fields)} potential input fields")
            return merged_fields
        
        except Exception as e:
            logger.warning(f"Input field detection failed: {e}")
            return []
    
    def get_screen_content(self) -> Dict:
        """
        Get comprehensive analysis of current screen including text and UI elements.
        
        Returns:
            Dict with:
            - text: List of all text elements with coordinates
            - buttons: List of detected buttons
            - input_fields: List of detected input fields
            - raw_text: Full extracted text
        """
        image = self.take_screenshot()
        
        if image is None:
            return {
                "text": [],
                "buttons": [],
                "input_fields": [],
                "raw_text": ""
            }
        
        return {
            "text": self.extract_text_with_coordinates(image)["text"],
            "buttons": self.find_buttons(image),
            "input_fields": self.find_input_fields(image),
            "raw_text": self.extract_text_with_coordinates(image)["raw_text"]
        }
    
    def click_on_text(self, search_text: str, offset_x: int = 0, offset_y: int = 0) -> bool:
        """
        Find text on screen and click on it.
        
        Args:
            search_text: Text to search for and click on
            offset_x: X offset from element center
            offset_y: Y offset from element center
        
        Returns:
            bool: True if clicked successfully, False if text not found
        """
        element = self.find_text_on_screen(search_text)
        
        if element:
            click_x = element["center_x"] + offset_x
            click_y = element["center_y"] + offset_y
            
            # Clamp coordinates to screen bounds
            click_x = max(0, min(click_x, self.screen_width - 1))
            click_y = max(0, min(click_y, self.screen_height - 1))
            
            logger.info(f"Clicking on '{search_text}' at ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            return True
        
        return False
    
    def type_in_field(self, field_text: str, search_label: str = None) -> bool:
        """
        Click on input field (optionally by label) and type text.
        
        Args:
            field_text: Text to type
            search_label: Label above field to search for (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if search_label:
            # If label provided, find it and click in field below it
            if not self.click_on_text(search_label):
                logger.warning(f"Could not find label '{search_label}'")
                # Try clicking on first input field anyway
                fields = self.find_input_fields()
                if fields:
                    pyautogui.click(fields[0]["center_x"], fields[0]["center_y"])
                else:
                    return False
        else:
            # Find first available input field
            fields = self.find_input_fields()
            if not fields:
                logger.warning("No input fields detected on screen")
                return False
            pyautogui.click(fields[0]["center_x"], fields[0]["center_y"])
        
        # Wait a moment for field to be focused
        import time
        time.sleep(0.3)
        
        # Clear existing text and type
        pyautogui.hotkey('ctrl', 'a')  # Select all
        import time
        time.sleep(0.1)
        pyautogui.typewrite(field_text, interval=0.05)
        
        logger.info(f"Typed '{field_text}' in field")
        return True
    
    def get_context_for_command(self, command: str) -> str:
        """
        Analyze screen and provide visual context for LLM decision making.
        
        Args:
            command: The user's command/intent
        
        Returns:
            str: Formatted context about current screen state
        """
        content = self.get_screen_content()
        
        lines = [
            "=== CURRENT SCREEN ANALYSIS ===",
            f"Time: {__import__('datetime').datetime.now().strftime('%H:%M:%S')}",
            "",
            "TEXT ELEMENTS ON SCREEN:",
        ]
        
        # Add visible text elements
        for elem in content["text"][:20]:  # Limit to first 20
            lines.append(f"  - '{elem['text']}' at ({elem['center_x']}, {elem['center_y']})")
        
        if len(content["text"]) > 20:
            lines.append(f"  ... and {len(content['text']) - 20} more text elements")
        
        # Add buttons
        if content["buttons"]:
            lines.append("")
            lines.append("CLICKABLE BUTTONS:")
            for btn in content["buttons"]:
                lines.append(f"  - Button: '{btn['text']}' at ({btn['center_x']}, {btn['center_y']})")
        
        # Add input fields
        if content["input_fields"]:
            lines.append("")
            lines.append("INPUT FIELDS:")
            for field in content["input_fields"]:
                lines.append(f"  - Field at ({field['center_x']}, {field['center_y']})")
        
        lines.extend([
            "",
            "FULL VISIBLE TEXT:",
            content["raw_text"][:500],  # First 500 chars
            "",
            f"USER COMMAND: {command}",
            "TASK: Use coordinates above to decide where to click or type."
        ])
        
        return "\n".join(lines)


# Global analyzer instance
_analyzer = None

def get_analyzer() -> ScreenAnalyzer:
    """Get or create global screen analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ScreenAnalyzer()
    return _analyzer

def take_screenshot():
    """Convenience function to take screenshot."""
    return get_analyzer().take_screenshot()

def extract_text_with_coordinates(image=None):
    """Convenience function to extract text with coordinates."""
    return get_analyzer().extract_text_with_coordinates(image)

def find_text_on_screen(search_text: str, image=None):
    """Convenience function to find text on screen."""
    return get_analyzer().find_text_on_screen(search_text, image)

def find_buttons(image=None):
    """Convenience function to find buttons."""
    return get_analyzer().find_buttons(image)

def find_input_fields(image=None):
    """Convenience function to find input fields."""
    return get_analyzer().find_input_fields(image)

def get_screen_content():
    """Convenience function to get full screen content."""
    return get_analyzer().get_screen_content()

def click_on_text(search_text: str, offset_x: int = 0, offset_y: int = 0):
    """Convenience function to click on text."""
    return get_analyzer().click_on_text(search_text, offset_x, offset_y)

def type_in_field(field_text: str, search_label: str = None):
    """Convenience function to type in field."""
    return get_analyzer().type_in_field(field_text, search_label)

def get_context_for_command(command: str):
    """Convenience function to get visual context."""
    return get_analyzer().get_context_for_command(command)
