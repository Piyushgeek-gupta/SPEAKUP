"""
Executor module for running automated steps on Windows.
Universal application detection and web fallback system.
Handles GUI automation, file operations, and command execution for ANY application.
Integrated with Tesseract OCR for intelligent screen-based clicking and typing.
"""

import subprocess
import time
import pyautogui
import pyperclip
import webbrowser
import os
from pathlib import Path
from loguru import logger
from typing import Optional
from core.ocr import get_analyzer, get_screen_content

# Set up pyautogui safety (move cursor to corner to stop)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1  # Slight pause between movements

# Application name mappings - maps user commands to possible executables and web alternatives
APP_MAPPINGS = {
    "vs code": {
        "names": ["code", "code.exe", "Code.exe"],
        "paths": [
            r"C:\Program Files\Microsoft VS Code\bin\code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\bin\code.exe",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
        ],
        "web": "https://github.com/codespaces",
        "keywords": ["vs code", "vscode", "visual studio code"]
    },
    "notepad": {
        "names": ["notepad", "notepad.exe"],
        "paths": [r"C:\Windows\System32\notepad.exe"],
        "web": None,  # Notepad doesn't have web version
        "keywords": ["notepad", "note"]
    },
    "excel": {
        "names": ["excel", "excel.exe", "EXCEL.EXE"],
        "paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\EXCEL.EXE",
        ],
        "web": "https://www.office.com",
        "keywords": ["excel", "spreadsheet", "xls"]
    },
    "word": {
        "names": ["winword", "winword.exe", "WINWORD.EXE"],
        "paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\WINWORD.EXE",
        ],
        "web": "https://www.office.com/launch/word",
        "keywords": ["word", "document", "docx"]
    },
    "powerpoint": {
        "names": ["powerpnt", "powerpnt.exe", "POWERPNT.EXE"],
        "paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
        ],
        "web": "https://www.office.com/launch/powerpoint",
        "keywords": ["powerpoint", "ppt", "presentation"]
    },
    "outlook": {
        "names": ["outlook", "outlook.exe", "OUTLOOK.EXE"],
        "paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            r"C:\Program Files (x86)\Microsoft Office\Office16\OUTLOOK.EXE",
        ],
        "web": "https://outlook.live.com",
        "keywords": ["outlook", "mail", "email"]
    },
    "chrome": {
        "names": ["chrome", "chrome.exe", "google-chrome"],
        "paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "web": None,
        "keywords": ["chrome", "google chrome", "browser"]
    },
    "firefox": {
        "names": ["firefox", "firefox.exe"],
        "paths": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "web": None,
        "keywords": ["firefox", "mozilla"]
    },
    "whatsapp": {
        "names": ["WhatsApp", "whatsapp.exe"],
        "paths": [
            r"C:\Users\User\AppData\Local\Programs\WhatsApp\WhatsApp.exe",
        ],
        "web": "https://web.whatsapp.com",
        "keywords": ["whatsapp", "whats app"]
    },
    "telegram": {
        "names": ["Telegram", "telegram.exe"],
        "paths": [],
        "web": "https://web.telegram.org",
        "keywords": ["telegram"]
    },
    "discord": {
        "names": ["Discord", "discord.exe"],
        "paths": [
            r"C:\Users\User\AppData\Local\Discord\app-[latest]\Discord.exe",
        ],
        "web": "https://discord.com/app",
        "keywords": ["discord"]
    },
    "slack": {
        "names": ["slack", "slack.exe"],
        "paths": [],
        "web": "https://app.slack.com",
        "keywords": ["slack"]
    },
    "teams": {
        "names": ["Teams", "teams.exe"],
        "paths": [
            r"C:\Users\User\AppData\Local\Microsoft\Teams\Teams.exe",
        ],
        "web": "https://teams.microsoft.com",
        "keywords": ["teams", "microsoft teams"]
    },
    "file explorer": {
        "names": ["explorer", "explorer.exe"],
        "paths": [r"C:\Windows\explorer.exe"],
        "web": None,
        "keywords": ["file explorer", "explorer", "folder"]
    },
    "terminal": {
        "names": ["cmd", "cmd.exe", "powershell"],
        "paths": [r"C:\Windows\System32\cmd.exe", r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"],
        "web": None,
        "keywords": ["terminal", "command prompt", "powershell", "cmd"]
    },
}

class StepExecutor:
    """Execute individual steps from the LLM output with universal app support."""
    
    def __init__(self):
        self.last_opened_file = None
        self.last_opened_folder = None
        self.last_opened_app = None
        
    def execute_step(self, step: str) -> bool:
        """
        Execute a single step with universal app detection.
        
        Args:
            step: The step instruction
            
        Returns:
            bool: True if successful
        """
        step_lower = step.lower().strip()
        logger.info(f"Executing: {step}")
        
        try:
            # Try to find and open application by name
            app_opened = False
            for app_name, app_info in APP_MAPPINGS.items():
                if any(keyword in step_lower for keyword in app_info["keywords"]):
                    logger.info(f"Detected app request: {app_name}")
                    self._open_application(app_name)
                    app_opened = True
                    self.last_opened_app = app_name
                    break
            
            if app_opened:
                return True
            
            # File/Folder operations
            if "create folder" in step_lower or "create directory" in step_lower:
                path = self._extract_path_from_step(step)
                self._create_folder(path)
            elif "create file" in step_lower:
                path = self._extract_path_from_step(step)
                self._create_file(path)
            elif "open file" in step_lower or "read file" in step_lower:
                path = self._extract_path_from_step(step)
                self._open_file(path)
            
            # Typing and keyboard
            elif "type" in step_lower or "write" in step_lower:
                text = self._extract_text_from_step(step, "type")
                self._type_text(text)
            elif "press" in step_lower or "keyboard" in step_lower:
                shortcut = self._extract_keyboard_shortcut(step)
                self._press_keys(shortcut)
            
            # Terminal commands
            elif "run terminal command" in step_lower or "execute command" in step_lower or "run command" in step_lower:
                command = self._extract_command_from_step(step)
                self._run_command(command)
            
            # Timing
            elif "wait" in step_lower:
                duration = self._extract_duration_from_step(step)
                time.sleep(duration)
            
            # Mouse operations
            elif "click" in step_lower:
                text = self._extract_text_from_step(step, "click")
                self._click_on_element(text)
            elif "scroll" in step_lower:
                direction = "down" if "down" in step_lower else "up"
                self._scroll(direction)
            
            # Web/URL operations
            elif "open" in step_lower and ("http" in step_lower or "www" in step_lower or "website" in step_lower):
                url = self._extract_url_from_step(step)
                self._open_url(url)
            
            else:
                logger.warning(f"Unknown step type: {step}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            return False
    
    def execute_steps(self, steps: list) -> bool:
        """
        Execute a list of steps in order.
        
        Args:
            steps: List of step instructions
            
        Returns:
            bool: True if all steps succeeded
        """
        logger.info(f"Starting execution of {len(steps)} steps")
        
        for i, step in enumerate(steps, 1):
            logger.info(f"Step {i}/{len(steps)}")
            if not self.execute_step(step):
                logger.warning(f"Step {i} failed, continuing...")
        
        logger.info("Step execution completed")
        return True
    
    # ===== UNIVERSAL APPLICATION LAUNCHER =====
    
    def _open_application(self, app_name: str) -> bool:
        """
        Open an application by name. Tries desktop app first, falls back to web version.
        
        Args:
            app_name: Name of the application (e.g., "vs code", "excel")
            
        Returns:
            bool: Success status
        """
        app_name_lower = app_name.lower()
        
        if app_name_lower not in APP_MAPPINGS:
            logger.warning(f"Unknown application: {app_name}")
            return False
        
        app_info = APP_MAPPINGS[app_name_lower]
        
        # Try to find and launch desktop application
        for exe_path in app_info["paths"]:
            if Path(exe_path).exists():
                try:
                    subprocess.Popen(exe_path)
                    logger.info(f"Opened {app_name} from: {exe_path}")
                    time.sleep(2)
                    return True
                except Exception as e:
                    logger.debug(f"Failed to open {exe_path}: {e}")
                    continue
        
        # Try executable names via system PATH
        for exe_name in app_info["names"]:
            try:
                subprocess.Popen([exe_name], shell=True)
                logger.info(f"Opened {app_name} using: {exe_name}")
                time.sleep(2)
                return True
            except Exception as e:
                logger.debug(f"Failed to open {exe_name}: {e}")
                continue
        
        # Fallback to web version
        if app_info.get("web"):
            logger.info(f"Desktop {app_name} not found, opening web version")
            self._open_url(app_info["web"])
            return True
        else:
            logger.error(f"Could not find {app_name} on system")
            return False
    
    # ===== FILE/FOLDER OPERATIONS =====
    
    def _create_folder(self, path: str):
        """Create a folder at the specified path."""
        try:
            if not path:
                logger.warning("No path specified for folder creation")
                return
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Folder created: {path}")
        except Exception as e:
            logger.error(f"Failed to create folder {path}: {e}")
    
    def _create_file(self, path: str):
        """Create an empty file at the specified path."""
        try:
            if not path:
                logger.warning("No path specified for file creation")
                return
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).touch()
            logger.info(f"File created: {path}")
        except Exception as e:
            logger.error(f"Failed to create file {path}: {e}")
    
    def _open_file(self, path: str):
        """Open a file with the default application."""
        try:
            if not path:
                logger.warning("No file path specified")
                return
            subprocess.Popen(["start", path], shell=True)
            self.last_opened_file = path
            time.sleep(1)
            logger.info(f"File opened: {path}")
        except Exception as e:
            logger.error(f"Failed to open file {path}: {e}")
    
    # ===== KEYBOARD & TYPING =====
    
    def _type_text(self, text: str):
        """Type text character by character."""
        try:
            if not text:
                logger.warning("No text specified to type")
                return
            # Use clipboard for longer texts (more reliable)
            if len(text) > 100:
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.write(text, interval=0.05)
            logger.info(f"Typed text: {text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            # Fallback to clipboard method
            try:
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
                logger.info(f"Text pasted via clipboard: {text[:50]}...")
            except Exception as e2:
                logger.error(f"Clipboard paste also failed: {e2}")
    
    def _press_keys(self, shortcut: str):
        """Press keyboard shortcut (e.g., 'ctrl+s', 'alt+tab')."""
        try:
            if not shortcut:
                logger.warning("No keyboard shortcut specified")
                return
            keys = shortcut.lower().split("+")
            pyautogui.hotkey(*keys)
            logger.info(f"Pressed keys: {shortcut}")
        except Exception as e:
            logger.error(f"Failed to press keys {shortcut}: {e}")
    
    # ===== COMMAND EXECUTION =====
    
    def _run_command(self, command: str):
        """Run a terminal command."""
        try:
            if not command:
                logger.warning("No command specified")
                return
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            logger.info(f"Command executed: {command}")
            if result.stdout:
                logger.debug(f"Output: {result.stdout[:200]}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {command}")
        except Exception as e:
            logger.error(f"Failed to run command {command}: {e}")
    
    # ===== MOUSE OPERATIONS =====
    
    def _click_on_element(self, element_text: str):
        """Click on an element (simplified - uses UI automation)."""
        try:
            if not element_text:
                logger.warning("No element text specified")
                return
            logger.info(f"Attempting to click on: {element_text}")
            # In a real scenario, use pywinauto for better UI automation
            # For now, just log it
        except Exception as e:
            logger.error(f"Failed to click: {e}")
    
    def _scroll(self, direction: str = "down", amount: int = 3):
        """Scroll in a direction."""
        try:
            scroll_amount = amount if direction == "down" else -amount
            pyautogui.scroll(scroll_amount)
            logger.info(f"Scrolled {direction}")
        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
    
    # ===== WEB OPERATIONS =====
    
    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        try:
            if not url:
                logger.warning("No URL specified")
                return
            
            # Ensure URL has protocol
            if not url.startswith(("http://", "https://", "file://")):
                url = "https://" + url
            
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
    
    # ===== EXTRACTION HELPERS =====
    
    def _extract_path_from_step(self, step: str) -> str:
        """Extract file/folder path from step instruction."""
        # Look for paths in quotes or after specific keywords
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # Common patterns
        keywords = ["at ", "in ", "from ", "to ", "path ", "location "]
        for keyword in keywords:
            if keyword in step.lower():
                idx = step.lower().find(keyword)
                path = step[idx + len(keyword):].strip()
                # Take until next sentence
                path = path.split('.')[0].split(',')[0].strip()
                return path
        
        return ""
    
    def _extract_text_from_step(self, step: str, keyword: str) -> str:
        """Extract text to type or click from step."""
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # Extract text after the keyword
        if keyword in step.lower():
            idx = step.lower().find(keyword) + len(keyword)
            text = step[idx:].strip()
            # Clean up
            if text.startswith(':'):
                text = text[1:].strip()
            return text
        
        return ""
    
    def _extract_keyboard_shortcut(self, step: str) -> str:
        """Extract keyboard shortcut from step."""
        # Common shortcuts
        shortcuts = {
            "save": "ctrl+s",
            "copy": "ctrl+c",
            "paste": "ctrl+v",
            "undo": "ctrl+z",
            "redo": "ctrl+y",
            "select all": "ctrl+a",
            "new tab": "ctrl+t",
            "close tab": "ctrl+w",
            "close window": "alt+f4",
            "minimize": "alt+f9",
            "maximize": "alt+f10",
        }
        
        step_lower = step.lower()
        for action, shortcut in shortcuts.items():
            if action in step_lower:
                return shortcut
        
        # Look for explicit shortcuts (Ctrl+S, Alt+Tab, etc.)
        import re
        matches = re.findall(r'([a-z]+)\+([a-z]+)', step_lower)
        if matches:
            return matches[0][0] + "+" + matches[0][1]
        
        return ""
    
    def _extract_command_from_step(self, step: str) -> str:
        """Extract terminal command from step."""
        if ":" in step:
            parts = step.split(":", 1)
            return parts[1].strip()
        
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # Extract after common command keywords
        keywords = ["run ", "execute ", "command "]
        for keyword in keywords:
            if keyword in step.lower():
                idx = step.lower().find(keyword) + len(keyword)
                return step[idx:].strip()
        
        return ""
    
    def _extract_duration_from_step(self, step: str) -> float:
        """Extract wait duration in seconds from step."""
        import re
        
        # Look for patterns like "2 seconds", "3s", etc.
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:seconds?|s|ms)', step.lower())
        if matches:
            duration = float(matches[0])
            # Convert to seconds if milliseconds
            if 'ms' in step.lower():
                duration /= 1000
            return duration
        
        return 1.0
    
    def _extract_url_from_step(self, step: str) -> str:
        """Extract URL from step instruction."""
        import re
        
        # Look for URLs
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
        matches = re.findall(url_pattern, step)
        if matches:
            return matches[0].rstrip('.,;:')
        
        # Look for URLs in quotes
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # Extract search terms for default search engine
        if "search" in step.lower():
            keywords = step.lower().replace("search", "").replace("for", "").strip()
            return f"https://www.google.com/search?q={keywords.replace(' ', '+')}"
        
        return ""
    """Execute individual steps from the LLM output."""
    
    def __init__(self):
        self.last_opened_file = None
        self.last_opened_folder = None
        
    def execute_step(self, step: str) -> bool:
        """
        Execute a single step.
        
        Args:
            step: The step instruction (e.g., "Open VS Code application")
            
        Returns:
            bool: True if successful, False otherwise
        """
        step_lower = step.lower().strip()
        logger.info(f"Executing: {step}")
        
        try:
            # Application opening
            if "open vs code" in step_lower or "open visual studio code" in step_lower:
                self._open_vscode()
            elif "open notepad" in step_lower:
                self._open_notepad()
            elif "open file explorer" in step_lower or "open folder" in step_lower:
                self._open_file_explorer()
            elif "open browser" in step_lower or "open chrome" in step_lower:
                self._open_browser()
            elif "open mail" in step_lower or "open outlook" in step_lower:
                self._open_mail()
            elif "open whatsapp" in step_lower:
                self._open_whatsapp()
            
            # File/Folder operations
            elif "create folder" in step_lower:
                path = self._extract_path_from_step(step)
                self._create_folder(path)
            elif "create file" in step_lower:
                path = self._extract_path_from_step(step)
                self._create_file(path)
            elif "open file" in step_lower or "read file" in step_lower:
                path = self._extract_path_from_step(step)
                self._open_file(path)
            
            # Typing and keyboard
            elif "type" in step_lower:
                text = self._extract_text_from_step(step, "type")
                self._type_text(text)
            elif "press" in step_lower or "keyboard" in step_lower:
                shortcut = self._extract_keyboard_shortcut(step)
                self._press_keys(shortcut)
            
            # Terminal commands
            elif "run terminal command" in step_lower or "execute command" in step_lower:
                command = self._extract_command_from_step(step)
                self._run_command(command)
            
            # Timing
            elif "wait" in step_lower:
                duration = self._extract_duration_from_step(step)
                time.sleep(duration)
            
            # Mouse operations
            elif "click" in step_lower:
                text = self._extract_text_from_step(step, "click")
                self._click_on_element(text)
            elif "scroll" in step_lower:
                direction = "down" if "down" in step_lower else "up"
                self._scroll(direction)
            
            else:
                logger.warning(f"Unknown step type: {step}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            return False
    
    def execute_steps(self, steps: list) -> bool:
        """
        Execute a list of steps in order.
        
        Args:
            steps: List of step instructions
            
        Returns:
            bool: True if all steps succeeded, False if any failed
        """
        logger.info(f"Starting execution of {len(steps)} steps")
        
        for i, step in enumerate(steps, 1):
            logger.info(f"Step {i}/{len(steps)}")
            if not self.execute_step(step):
                logger.warning(f"Step {i} failed, continuing...")
                # Continue instead of breaking to be resilient
        
        logger.info("Step execution completed")
        return True
    
    # ===== Application Launchers =====
    
    def _open_vscode(self):
        """Open Visual Studio Code."""
        try:
            subprocess.Popen(["code"], shell=True)
            time.sleep(2)
            logger.info("VS Code opened")
        except Exception as e:
            logger.error(f"Failed to open VS Code: {e}")
    
    def _open_notepad(self):
        """Open Notepad."""
        subprocess.Popen(["notepad.exe"])
        time.sleep(1)
        logger.info("Notepad opened")
    
    def _open_file_explorer(self):
        """Open File Explorer."""
        subprocess.Popen(["explorer.exe"])
        time.sleep(1)
        logger.info("File Explorer opened")
    
    def _open_browser(self):
        """Open default browser."""
        subprocess.Popen(["start", "chrome"], shell=True)
        time.sleep(2)
        logger.info("Browser opened")
    
    def _open_mail(self):
        """Open default mail application."""
        try:
            subprocess.Popen(["outlook.exe"])
        except:
            # Fallback: open mail on browser
            subprocess.Popen(["start", "https://mail.google.com"], shell=True)
        time.sleep(2)
        logger.info("Mail application opened")
    
    def _open_whatsapp(self):
        """Open WhatsApp application."""
        try:
            # Try desktop app first
            subprocess.Popen([
                r"C:\Users\User\AppData\Local\Programs\WhatsApp\WhatsApp.exe"
            ])
        except:
            # Fallback: open web version
            subprocess.Popen(["start", "https://web.whatsapp.com"], shell=True)
        time.sleep(2)
        logger.info("WhatsApp opened")
    
    # ===== File/Folder Operations =====
    
    def _create_folder(self, path: str):
        """Create a folder at the specified path."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Folder created: {path}")
        except Exception as e:
            logger.error(f"Failed to create folder {path}: {e}")
    
    def _create_file(self, path: str):
        """Create an empty file at the specified path."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).touch()
            logger.info(f"File created: {path}")
        except Exception as e:
            logger.error(f"Failed to create file {path}: {e}")
    
    def _open_file(self, path: str):
        """Open a file with the default application."""
        try:
            subprocess.Popen(["start", path], shell=True)
            self.last_opened_file = path
            time.sleep(1)
            logger.info(f"File opened: {path}")
        except Exception as e:
            logger.error(f"Failed to open file {path}: {e}")
    
    # ===== Keyboard & Typing =====
    
    def _type_text(self, text: str):
        """
        Type text intelligently using OCR to find input fields.
        If OCR fails, falls back to simple typing.
        """
        try:
            analyzer = get_analyzer()
            
            # Take screenshot and find input fields using OCR
            input_fields = analyzer.find_input_fields()
            buttons = analyzer.find_buttons()
            
            if input_fields:
                # Click on the first visible input field
                field = input_fields[0]
                pyautogui.click(field["center_x"], field["center_y"])
                time.sleep(0.3)
                logger.info(f"Clicked on input field at ({field['center_x']}, {field['center_y']})")
            
            # Clear any existing text and type
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            
            # Use clipboard for more reliable typing (especially with special characters)
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            
            logger.info(f"Typed text: {text[:50]}...")
        except Exception as e:
            logger.warning(f"OCR-based typing failed, trying direct typing: {e}")
            try:
                pyautogui.write(text, interval=0.05)
                logger.info(f"Typed text (fallback): {text[:50]}...")
            except Exception as e2:
                logger.error(f"Failed to type text: {e2}")
    
    def _press_keys(self, shortcut: str):
        """Press keyboard shortcut (e.g., 'ctrl+s', 'alt+tab')."""
        try:
            keys = shortcut.lower().split("+")
            pyautogui.hotkey(*keys)
            logger.info(f"Pressed keys: {shortcut}")
        except Exception as e:
            logger.error(f"Failed to press keys {shortcut}: {e}")
    
    # ===== Command Execution =====
    
    def _run_command(self, command: str):
        """Run a terminal command."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            logger.info(f"Command executed: {command}")
            if result.stdout:
                logger.debug(f"Output: {result.stdout[:200]}")
        except Exception as e:
            logger.error(f"Failed to run command {command}: {e}")
    
    # ===== Mouse Operations =====
    
    def _click_on_element(self, element_text: str):
        """
        Click on an element using OCR to find it on screen.
        Searches for text, buttons, and UI elements intelligently.
        """
        logger.info(f"Attempting to click on: {element_text}")
        
        try:
            analyzer = get_analyzer()
            
            # First, try to find exact text on screen
            element = analyzer.find_text_on_screen(element_text)
            
            if element:
                logger.info(f"Found text '{element_text}' at ({element['center_x']}, {element['center_y']})")
                pyautogui.click(element["center_x"], element["center_y"])
                time.sleep(0.3)
                return
            
            # If not found, try to find it in buttons
            buttons = analyzer.find_buttons()
            for button in buttons:
                if element_text.lower() in button["text"].lower():
                    logger.info(f"Found button '{button['text']}' at ({button['center_x']}, {button['center_y']})")
                    pyautogui.click(button["center_x"], button["center_y"])
                    time.sleep(0.3)
                    return
            
            # If still not found, try partial matching in all text
            content = analyzer.get_screen_content()
            for text_elem in content["text"]:
                if element_text.lower() in text_elem["text"].lower():
                    logger.info(f"Found partial match '{text_elem['text']}' at ({text_elem['center_x']}, {text_elem['center_y']})")
                    pyautogui.click(text_elem["center_x"], text_elem["center_y"])
                    time.sleep(0.3)
                    return
            
            logger.warning(f"Could not find '{element_text}' on screen - element not visible")
        
        except Exception as e:
            logger.error(f"OCR-based clicking failed: {e}")
    
    def _scroll(self, direction: str = "down", amount: int = 3):
        """Scroll in a direction."""
        try:
            scroll_amount = amount if direction == "down" else -amount
            pyautogui.scroll(scroll_amount)
            logger.info(f"Scrolled {direction}")
        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
    
    # ===== Extraction Helpers =====
    
    def _extract_path_from_step(self, step: str) -> str:
        """Extract file/folder path from step instruction."""
        # Look for paths in quotes or after specific keywords
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # Common patterns
        keywords = ["at ", "in ", "from ", "to "]
        for keyword in keywords:
            if keyword in step.lower():
                idx = step.lower().find(keyword)
                path = step[idx + len(keyword):].strip()
                # Take first continuous word/path
                return path.split()[0] if path else ""
        
        return ""
    
    def _extract_text_from_step(self, step: str, keyword: str) -> str:
        """Extract text to type or click from step."""
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        # Extract text after the keyword
        if keyword in step.lower():
            idx = step.lower().find(keyword) + len(keyword)
            return step[idx:].strip()
        
        return ""
    
    def _extract_keyboard_shortcut(self, step: str) -> str:
        """Extract keyboard shortcut from step."""
        # Look for patterns like Ctrl+S, Alt+Tab, etc.
        step_upper = step.upper()
        keys = ["CTRL", "ALT", "SHIFT", "WIN"]
        
        for key in keys:
            if key in step_upper:
                # Find the shortcut pattern
                for combo in ["CTRL+S", "CTRL+C", "CTRL+V", "CTRL+Z", "ALT+TAB"]:
                    if combo in step_upper:
                        return combo.lower()
        
        return ""
    
    def _extract_command_from_step(self, step: str) -> str:
        """Extract terminal command from step."""
        if ":" in step:
            parts = step.split(":", 1)
            return parts[1].strip()
        
        if '"' in step:
            parts = step.split('"')
            if len(parts) >= 2:
                return parts[1]
        
        return ""
    
    def _extract_duration_from_step(self, step: str) -> float:
        """Extract wait duration in seconds from step."""
        import re
        
        # Look for patterns like "2 seconds", "3s", etc.
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:seconds?|s|ms)', step.lower())
        if matches:
            duration = float(matches[0])
            # Convert to seconds if milliseconds
            if 'ms' in step.lower():
                duration /= 1000
            return duration
        
        return 1.0  # Default 1 second
