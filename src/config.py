import pygame
import os
import sys # Need sys

# Paths
# Check if we are running as a compiled exe (Frozen) or a script
if getattr(sys, 'frozen', False):
    # If EXE: The "Base Dir" is where the EXE file sits
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If Script: The "Base Dir" is the parent of the 'src' folder
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
STATS_FILE = os.path.join(BASE_DIR, "tosoku_stats.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

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