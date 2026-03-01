"""
Example custom actions and extensions for SpeakUp.

This file demonstrates how to extend SpeakUp with additional functionality.
Copy and adapt these examples to your needs.
"""

import subprocess
import webbrowser
import time
from pathlib import Path
from loguru import logger
import pyautogui

# Example 1: Open website shortcuts
def open_website(url: str, wait_time: float = 2.0):
    """
    Open a website in the default browser.
    
    Example command: "Open GitHub"
    Add to executor: elif "open github" in step_lower:
                        self._open_website("https://github.com")
    """
    try:
        webbrowser.open(url)
        time.sleep(wait_time)
        logger.info(f"Opened website: {url}")
    except Exception as e:
        logger.error(f"Failed to open website: {e}")

# Example 2: Create a new Python project
def create_python_project(project_name: str, project_path: str = None):
    """
    Create a new Python project with virtual environment.
    
    Example command: "Create a new Python project called myapp"
    """
    if project_path is None:
        project_path = Path.home() / "Projects" / project_name
    else:
        project_path = Path(project_path) / project_name
    
    try:
        # Create project folder
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create virtual environment
        subprocess.run([
            "python", "-m", "venv",
            str(project_path / "venv")
        ], check=True)
        
        # Create project files
        (project_path / "main.py").write_text("# Your Python code here\n\nif __name__ == '__main__':\n    print('Hello, World!')\n")
        (project_path / "requirements.txt").write_text("# Add your dependencies here\n")
        (project_path / ".gitignore").write_text("venv/\n__pycache__/\n*.pyc\n.env\n")
        
        logger.info(f"Created Python project: {project_path}")
        return str(project_path)
    except Exception as e:
        logger.error(f"Failed to create Python project: {e}")
        return None

# Example 3: Create a React project
def create_react_project(project_name: str):
    """
    Create a new React project using Create React App.
    
    Example command: "Create a new React project called my-app"
    """
    try:
        command = f"npx create-react-app {project_name}"
        subprocess.run(command, shell=True, check=True)
        logger.info(f"Created React project: {project_name}")
    except Exception as e:
        logger.error(f"Failed to create React project: {e}")

# Example 4: Search the web
def web_search(query: str, engine: str = "google"):
    """
    Open a web search in the default browser.
    
    Example command: "Search for Python documentation"
    """
    try:
        if engine == "google":
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        elif engine == "bing":
            url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        else:
            url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        
        webbrowser.open(url)
        logger.info(f"Searched for: {query}")
    except Exception as e:
        logger.error(f"Failed to search: {e}")

# Example 5: Send keyboard shortcut
def send_key_combination(keys: str):
    """
    Send a keyboard key combination.
    
    Example commands:
    - "Save the file" -> Send Ctrl+S
    - "Undo the last action" -> Send Ctrl+Z
    """
    key_map = {
        "save": "ctrl+s",
        "copy": "ctrl+c",
        "paste": "ctrl+v",
        "undo": "ctrl+z",
        "redo": "ctrl+y",
        "select all": "ctrl+a",
        "new tab": "ctrl+t",
        "close tab": "ctrl+w",
        "close window": "alt+f4",
    }
    
    try:
        shortcut = key_map.get(keys.lower(), keys.lower())
        key_list = shortcut.split("+")
        pyautogui.hotkey(*key_list)
        logger.info(f"Pressed keys: {shortcut}")
    except Exception as e:
        logger.error(f"Failed to press keys: {e}")

# Example 6: Read and process file content
def read_and_summarize_file(file_path: str) -> str:
    """
    Read a text file and return its content.
    
    Example command: "Read my todo list"
    """
    try:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            logger.info(f"Read file: {file_path}")
            return content
        else:
            logger.warning(f"File not found: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return None

# Example 7: Open multiple applications in sequence
def open_development_stack():
    """
    Open a complete development environment.
    
    Example command: "Setup my development environment"
    """
    apps = [
        ("VS Code", "code"),
        ("Terminal", "cmd.exe"),
        ("Browser", "chrome"),
    ]
    
    try:
        for app_name, executable in apps:
            logger.info(f"Opening {app_name}...")
            subprocess.Popen(executable, shell=True)
            time.sleep(2)  # Wait between opening apps
        logger.info("Development stack opened")
    except Exception as e:
        logger.error(f"Failed to open development stack: {e}")

# Example 8: Navigate and interact with browser
def google_search_and_click(query: str, result_index: int = 0):
    """
    Search Google and click the Nth result.
    
    Example command: "Search for Python and click the first result"
    
    Note: This is a simplified example. For real automation,
    use Selenium or pyautogui with image recognition.
    """
    try:
        # Open search
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        time.sleep(3)
        
        # In real scenario, use Selenium or pyautogui
        # to click the specific result
        logger.info(f"Searched: {query}")
    except Exception as e:
        logger.error(f"Failed to search and click: {e}")

# Example 9: Run a custom script
def run_custom_script(script_path: str):
    """
    Run a custom Python or batch script.
    
    Example command: "Run my backup script"
    """
    try:
        if script_path.endswith(".py"):
            subprocess.run(["python", script_path], check=True)
        elif script_path.endswith(".bat"):
            subprocess.run([script_path], shell=True, check=True)
        logger.info(f"Script executed: {script_path}")
    except Exception as e:
        logger.error(f"Failed to run script: {e}")

# Example 10: Download file
def download_file(url: str, save_to: str = None):
    """
    Download a file from URL.
    
    Example command: "Download the latest Python"
    
    Requires: pip install requests
    """
    try:
        import requests
        
        if save_to is None:
            save_to = Path.home() / "Downloads" / Path(url).name
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_to, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded: {url} -> {save_to}")
    except Exception as e:
        logger.error(f"Failed to download file: {e}")

# Example 11: List and organize files
def organize_downloads_folder():
    """
    Organize Downloads folder by file type.
    
    Example command: "Organize my Downloads folder"
    """
    try:
        downloads = Path.home() / "Downloads"
        
        # Create category folders
        categories = {
            "Images": [".jpg", ".png", ".gif", ".bmp"],
            "Documents": [".pdf", ".docx", ".xlsx", ".pptx", ".txt"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov"],
            "Audio": [".mp3", ".wav", ".m4a", ".flac"],
            "Archives": [".zip", ".rar", ".7z", ".tar"],
        }
        
        for category, extensions in categories.items():
            cat_folder = downloads / category
            cat_folder.mkdir(exist_ok=True)
            
            # Move files to category folders
            for file in downloads.glob("*"):
                if file.is_file() and file.suffix.lower() in extensions:
                    file.rename(cat_folder / file.name)
        
        logger.info("Downloads folder organized")
    except Exception as e:
        logger.error(f"Failed to organize downloads: {e}")

# Example 12: System information
def get_system_info():
    """
    Get system information using psutil.
    
    Example command: "Tell me my system information"
    
    Requires: pip install psutil
    """
    try:
        import psutil
        
        info = {
            "CPU Usage": f"{psutil.cpu_percent()}%",
            "Memory Usage": f"{psutil.virtual_memory().percent}%",
            "Disk Usage": f"{psutil.disk_usage('/').percent}%",
            "Boot Time": time.ctime(psutil.boot_time()),
        }
        
        logger.info(f"System Info: {info}")
        return info
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return None

# ============================================================================
# HOW TO INTEGRATE THESE INTO THE EXECUTOR
# ============================================================================
"""
1. Add to actions/executor.py in the execute_step() method:

   elif "open github" in step_lower:
       self._open_website("https://github.com")
   
   elif "create python project" in step_lower:
       project_name = self._extract_text_from_step(step, "create python project")
       create_python_project(project_name)
   
   elif "search for" in step_lower:
       query = self._extract_text_from_step(step, "search for")
       web_search(query)

2. Or add as methods in the StepExecutor class:

   def _open_github(self):
       open_website("https://github.com")
   
   def _create_python_project(self, name: str):
       create_python_project(name)

3. Then in execute_step():

   elif "open github" in step_lower:
       self._open_github()
   
   elif "create python project" in step_lower:
       name = self._extract_text_from_step(step, "create python project")
       self._create_python_project(name)

4. Update core/prompts.py to inform the LLM about these new capabilities:

   SYSTEM_INSTRUCTION = '''
   ... existing instructions ...
   
   NEW CAPABILITIES:
   - Create Python projects with virtual environments
   - Create React projects
   - Organize files by type
   - Run custom scripts
   - Download files
   ...
   '''

5. Test by saying:
   "Create a new Python project called my_app"
   "Create a React project"
   "Organize my downloads"
"""

if __name__ == "__main__":
    # Test examples
    print("SpeakUp Examples Module")
    print("=" * 50)
    print("These are example functions that can be integrated")
    print("into the main SpeakUp executor.")
    print("\nSee comments above for integration instructions.")
