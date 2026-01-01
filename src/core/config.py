import os
import sys
import platform
from pathlib import Path

GAME_VERSION = "0.3" # Update this number before every release!
VERSION_URL = "https://raw.githubusercontent.com/spacefaringiyo/GameTSK/refs/heads/main/version"
CREDITS_URL = "https://raw.githubusercontent.com/spacefaringiyo/GameTSK/refs/heads/main/credits"
LINKS_URL = "https://raw.githubusercontent.com/spacefaringiyo/GameTSK/refs/heads/main/links.json"
SCENARIOS_OFFICIAL_URL = "https://raw.githubusercontent.com/spacefaringiyo/GameTSK/refs/heads/main/scenarios_official.json"
SCENARIOS_COMMUNITY_URL = "https://raw.githubusercontent.com/spacefaringiyo/GameTSK/refs/heads/main/scenarios_community.json"

def get_data_dir():
    """Finds the standard application data directory for the current OS."""
    app_name = "TosokuAimTrainer"
    home = Path.home()
    
    if platform.system() == "Windows":
        # Windows: C:/Users/Name/AppData/Roaming/TosokuAimTrainer
        base = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
    elif platform.system() == "Darwin":
        # macOS: ~/Library/Application Support/TosokuAimTrainer
        base = home / "Library/Application Support"
    else:
        # Linux: ~/.local/share/TosokuAimTrainer (XDG Standard)
        base = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
        
    data_path = base / app_name
    
    # Ensure the directory exists
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path

# --- NEW DATA PATHS ---
DATA_DIR = get_data_dir()
STATS_FILE = str(DATA_DIR / "tosoku_stats.json")
SETTINGS_FILE = str(DATA_DIR / "settings.json")
DATA_FILE = str(DATA_DIR / "tosoku_data.json")

# --- LEGACY SUPPORT (Move old files if they exist) ---
# This looks in the folder where the EXE/Script is and moves them to the new home.
if getattr(sys, 'frozen', False):
    OLD_BASE = Path(sys.executable).parent
else:
    OLD_BASE = Path(__file__).parent.parent.parent

for filename in ["tosoku_stats.json", "settings.json", "tosoku_data.json"]:
    old_file = OLD_BASE / filename
    new_file = DATA_DIR / filename
    if old_file.exists() and not new_file.exists():
        try:
            import shutil
            shutil.move(str(old_file), str(new_file))
            print(f"Migrated {filename} to {DATA_DIR}")
        except Exception as e:
            print(f"Migration error for {filename}: {e}")

# The folder for Online/Manual scenarios stays in the Game folder (Read only)
BASE_DIR = str(OLD_BASE)
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")

# Screen
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
TARGET_FPS = 144

# Colors
BG_COLOR = (20, 20, 20)
PANEL_COLOR = (30, 30, 30)
STATS_BG_COLOR = (15, 15, 25)

COLOR_PERFECT = (255, 215, 0)   # Gold
COLOR_FAST = (255, 50, 50)      # Red
COLOR_SLOW = (50, 150, 255)     # Blue
COLOR_ZONE_LINE = (100, 100, 100)
COLOR_REC = (255, 0, 0)

UI_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 200, 255)
TEXT_GRAY = (150, 150, 150)

# States
STATE_EDIT = 0
STATE_WARMUP = 1
STATE_CHALLENGE_IDLE = 2
STATE_CHALLENGE_RUN = 3
STATE_CHALLENGE_END = 4
STATE_STATS_VIEW = 5
STATE_SETTINGS = 6
STATE_MODAL = 99