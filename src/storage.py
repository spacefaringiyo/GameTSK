import json
import os
import glob
from .config import CONFIGS_DIR, STATS_FILE, BASE_DIR, SETTINGS_FILE

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

class Storage:
    def __init__(self):
        self.ensure_dirs()

    def ensure_dirs(self):
        if not os.path.exists(CONFIGS_DIR):
            os.makedirs(CONFIGS_DIR)
            default_conf = {
                "name": "Default",
                "smoothing": 15,
                "zoom_scale": 3,
                "start_speed": 500,
                "end_speed": 500,
                "tolerance": 50,
                "duration": 15
            }
            self.save_config("Default", default_conf)

    # --- Global Settings (Audio) ---
    def load_global_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            # Default Audio Settings
            return {
                "hit_enabled": True,
                "miss_enabled": False,
                "hit_vol": 0.3,
                "miss_vol": 0.3,
                "hit_freq": 150,
                "miss_freq": 100,
                "tick_rate": 20
            }
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_global_settings(self, data):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    # --- Config Management ---
    def list_configs(self):
        files = glob.glob(os.path.join(CONFIGS_DIR, "*.json"))
        # Sort alphabetically for better UX
        names = [os.path.splitext(os.path.basename(f))[0] for f in files]
        names.sort()
        return names

    def load_config(self, name):
        path = os.path.join(CONFIGS_DIR, f"{name}.json")
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {name}: {e}")
            return None

    def save_config(self, name, data):
        path = os.path.join(CONFIGS_DIR, f"{name}.json")
        data['name'] = name
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def delete_config(self, name):
        path = os.path.join(CONFIGS_DIR, f"{name}.json")
        if os.path.exists(path):
            os.remove(path)

    # --- Stats Management ---
    def load_stats(self):
        if not os.path.exists(STATS_FILE):
            return []
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []

    def save_run(self, entry):
        history = self.load_stats()
        history.insert(0, entry)
        history = history[:100] 
        with open(STATS_FILE, 'w') as f:
            json.dump(history, f, indent=4)