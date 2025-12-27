import json
import os
from .config import BASE_DIR, STATS_FILE, SETTINGS_FILE
from .utils import generate_hash, generate_auto_name

DATA_FILE = os.path.join(BASE_DIR, "tosoku_data.json")

class Storage:
    def __init__(self):
        self.data = self.load_data()

    def load_data(self):
        # 1. Define Standard Structure
        default_structure = {
            "recents": [],   
            "imported": [],  
            "favorites": {}  
        }
        
        # 2. Check if file exists
        if not os.path.exists(DATA_FILE):
            # --- FACTORY PRESETS GENERATION ---
            # If no DB exists, we create one with these starters in Favorites
            
            presets = [
                # 1. Standard Horizontal Tracking
                {
                    "name": "Standard Horizontal",
                    "data": {"start_speed": 500, "end_speed": 500, "tolerance": 75, "duration": 10, "smoothing": 75, "zoom_scale": 2, "warmup_time": 1, "directions": [False, False, True, True]}
                },
                # 2. Slow Micro-Control
                {
                    "name": "Micro Control",
                    "data": {"start_speed": 150, "end_speed": 150, "tolerance": 20, "duration": 10, "smoothing": 75, "zoom_scale": 2, "warmup_time": 1, "directions": [True, True, True, True]}
                },
                # 3. Vertical Strafe
                {
                    "name": "Vertical Speed",
                    "data": {"start_speed": 500, "end_speed": 500, "tolerance": 100, "duration": 10, "smoothing": 75, "zoom_scale": 2, "warmup_time": 1, "directions": [True, True, False, False]}
                },
                # 4. Acceleration Test (Ramp)
                {
                    "name": "Accel Ramp Test",
                    "data": {"start_speed": 100, "end_speed": 1000, "tolerance": 100, "duration": 10, "smoothing": 75, "zoom_scale": 2, "warmup_time": 1, "directions": [False, False, True, True]}
                }
            ]
            
            # Inject into structure
            for p in presets:
                h = generate_hash(p['data'])
                default_structure['favorites'][h] = p
                
            return default_structure
            
        # 3. Normal Load
        try:
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                for k in default_structure:
                    if k not in d: d[k] = default_structure[k]
                return d
        except:
            return default_structure

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    # --- List Management ---

    def _push_to_list(self, list_key, config_data, limit=30):
        """Generic function to add to Recents or Imported"""
        # Add timestamp/hash info
        cfg = config_data.copy()
        cfg_hash = generate_hash(cfg)
        cfg['hash'] = cfg_hash
        
        # Remove if duplicate exists (move to top)
        self.data[list_key] = [c for c in self.data[list_key] if generate_hash(c) != cfg_hash]
        
        # Insert at Top
        self.data[list_key].insert(0, cfg)
        
        # Cap size
        self.data[list_key] = self.data[list_key][:limit]
        self.save_data()

    def add_recent(self, config_data):
        self._push_to_list("recents", config_data)

    def add_imported(self, config_data):
        self._push_to_list("imported", config_data)

    # --- Favorites Management ---

    def toggle_favorite(self, config_data, custom_name=None):
        h = generate_hash(config_data)
        
        # Check if exists (Migration support: checks dict keys)
        if h in self.data['favorites']:
            # REMOVE
            del self.data['favorites'][h]
        else:
            # ADD - Now stores the FULL DATA
            self.data['favorites'][h] = {
                "name": custom_name if custom_name else "Favorite",
                "data": config_data
            }
        self.save_data()

    def update_favorite_name(self, config_data, new_name):
        h = generate_hash(config_data)
        if h in self.data['favorites']:
            # Update just the name field
            entry = self.data['favorites'][h]
            # Handle legacy string format if present, convert to new format
            if isinstance(entry, str):
                self.data['favorites'][h] = {"name": new_name, "data": config_data}
            else:
                entry['name'] = new_name
            self.save_data()

    def is_favorite(self, config_data):
        h = generate_hash(config_data)
        return h in self.data['favorites']

    def get_display_name(self, config_data):
        h = generate_hash(config_data)
        if h in self.data['favorites']:
            val = self.data['favorites'][h]
            # Robust check for new dict format vs old string format
            if isinstance(val, dict):
                return "★ " + val.get('name', 'Unknown')
            else:
                return "★ " + str(val)
        return generate_auto_name(config_data)
    
    def update_favorite_name(self, config_data, new_name):
        h = generate_hash(config_data)
        
        # We delete and re-insert to:
        # 1. Ensure the data structure is rebuilt correctly ({name, data})
        # 2. Move it to the END of the dictionary (which appears at TOP in Browser)
        
        if h in self.data['favorites']:
            del self.data['favorites'][h]
            
        self.data['favorites'][h] = {
            "name": new_name,
            "data": config_data
        }
        self.save_data()

    # --- Global Audio / Stats (Same as before) ---
    
    def load_global_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return {"hit_enabled": True, "miss_enabled": False, "hit_vol": 0.3, "miss_vol": 0.3,
                    "hit_freq": 150, "miss_freq": 100, "tick_rate": 20, "last_active_tab": 1 }
        try:
            with open(SETTINGS_FILE, 'r') as f: return json.load(f)
        except: return {}

    def save_global_settings(self, data):
        with open(SETTINGS_FILE, 'w') as f: json.dump(data, f, indent=4)

    def load_stats(self):
        if not os.path.exists(STATS_FILE): return []
        try:
            with open(STATS_FILE, 'r') as f: return json.load(f)
        except: return []

    def save_run(self, entry):
        history = self.load_stats()
        history.insert(0, entry)
        history = history[:100]
        with open(STATS_FILE, 'w') as f: json.dump(history, f, indent=4)

    def get_high_score(self, config_hash):
        history = self.load_stats()
        # Filter history for matches. Handle old records missing 'hash' safely.
        scores = [e.get('score', 0) for e in history if e.get('hash') == config_hash]
        if not scores:
            return 0.0
        return max(scores)
