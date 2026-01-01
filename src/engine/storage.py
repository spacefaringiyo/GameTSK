import json
import urllib.request
import os
import glob
from src.core.utils import generate_hash, generate_auto_name
from src.core.config import STATS_FILE, SETTINGS_FILE, DATA_FILE, SCENARIOS_DIR

class Storage:
    def __init__(self):
        self.data = self.load_data()


    def load_data(self):
        CURRENT_VERSION = 2
        default_structure = {
            "version": CURRENT_VERSION,
            "recents": [],   
            "imported": [],  
            "local_scenarios": {}, # Renamed from favorites
            "stars": {             # NEW: Stores hashes of pinned items per tab
                "RECENT": [],
                "LOCAL": [],
                "ONLINE": [],
                "IMPORT": []
            }
        }
        
        if not os.path.exists(DATA_FILE):
            # --- FACTORY PRESETS GENERATION ---
            # If no DB exists, we create one with these starters in Favorites
            
            presets = [
                
            ]

            for p in presets:
                h = generate_hash(p['data'])
                # FIX: Use 'local_scenarios' here instead of 'favorites'
                default_structure['local_scenarios'][h] = p
            return default_structure
            
        try:
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                # --- FUTURE PROOFING: MIGRATION LOGIC ---
                file_v = d.get("version", 0)
                
                if file_v < CURRENT_VERSION:
                    print(f"Upgrading data from v{file_v} to v{CURRENT_VERSION}")
                    # Here you can add specific logic for future updates
                    # For now, we just ensure version key is updated
                    d["version"] = CURRENT_VERSION
                
                # Ensure missing keys (from any version) are filled from defaults
                for k, v in default_structure.items():
                    if k not in d: d[k] = v
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

    # --- local_scenarios Management ---

    def toggle_favorite(self, config_data, custom_name=None):
        h = generate_hash(config_data)
        
        # Check if exists (Migration support: checks dict keys)
        if h in self.data['local_scenarios']:
            # REMOVE
            del self.data['local_scenarios'][h]
        else:
            # ADD - Now stores the FULL DATA
            self.data['local_scenarios'][h] = {
                "name": custom_name if custom_name else "Favorite",
                "data": config_data
            }
        self.save_data()

    def update_favorite_name(self, config_data, new_name):
        h = generate_hash(config_data)
        if h in self.data['local_scenarios']:
            # Update just the name field
            entry = self.data['local_scenarios'][h]
            # Handle legacy string format if present, convert to new format
            if isinstance(entry, str):
                self.data['local_scenarios'][h] = {"name": new_name, "data": config_data}
            else:
                entry['name'] = new_name
            self.save_data()

    def is_favorite(self, config_data):
        h = generate_hash(config_data)
        return h in self.data['local_scenarios']

    def get_display_name(self, config_data):
        # 1. Priority: Explicit Name (Wrapper OR Flat)
        # If the data itself claims a name, we use it immediately.
        # This fixes the inconsistency between Wrapper vs Flat formats.
        if isinstance(config_data, dict) and config_data.get("name"):
            return config_data["name"]
            
        # 2. Database Lookup (Fallback for nameless physics)
        # If the data has no name, we check if we recognize the physics hash.
        # (e.g. You pasted raw code that happens to match a local file)
        h = generate_hash(config_data)
        if h in self.data['local_scenarios']:
            val = self.data['local_scenarios'][h]
            if isinstance(val, dict):
                return val.get('name', 'Unknown') # Removed "★ " prefix
            else:
                return str(val) # Legacy string format support

        # 3. Last Resort: Auto-Generated Description
        # e.g. "↔ 500→500 ±75"
        return generate_auto_name(config_data)
    
    def update_favorite_name(self, config_data, new_name):
        h = generate_hash(config_data)
        
        # We delete and re-insert to:
        # 1. Ensure the data structure is rebuilt correctly ({name, data})
        # 2. Move it to the END of the dictionary (which appears at TOP in Browser)
        
        if h in self.data['local_scenarios']:
            del self.data['local_scenarios'][h]
            
        self.data['local_scenarios'][h] = {
            "name": new_name,
            "data": config_data
        }
        self.save_data()

    # --- Global Audio / Stats (Same as before) ---
    
    def load_global_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return {"hit_enabled": True, "miss_enabled": False, "hit_vol": 0.3, "miss_vol": 0.3,
                    "hit_freq": 150, "miss_freq": 100, "tick_rate": 20, "last_active_tab": 0 }
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

    def get_custom_scenarios(self):
    #"""Scans the scenarios/ folder for .json files"""
        if not os.path.exists(SCENARIOS_DIR):
            os.makedirs(SCENARIOS_DIR)
        
        results = []
        # Find all .json files
        files = glob.glob(os.path.join(SCENARIOS_DIR, "*.json"))
        
        for fpath in files:
            try:
                with open(fpath, 'r') as f:
                    content = json.load(f)
                    
                # Logic: Is this a full wrapper or just the data?
                # Case A: User pasted { "name": "X", "data": {...} }
                if "data" in content and "name" in content:
                    results.append(content["data"])
                # Case B: User pasted raw config { "start_speed": ... }
                else:
                    # We treat the whole file as the data
                    results.append(content)
                    
            except Exception as e:
                print(f"Failed to load {fpath}: {e}")
                
        return results
    
    # Changed to accept target_url
    def get_online_scenarios(self, target_url):
        if not target_url:
            return [{"name": "⚠ No URL Configured", "data": {}}]

        try:
            with urllib.request.urlopen(target_url, timeout=3) as url:
                data = json.loads(url.read().decode())
                return data
                
        except Exception as e:
            print(f"Online Fetch Error: {e}")
            return [
                {"name": "⚠ Connection Failed", "data": {}},
                {"name": "Retry later...", "data": {}}
            ]
        
    def toggle_star(self, tab_name, config_data):
        """Pins/Unpins an item in a specific tab"""
        h = generate_hash(config_data)
        tab_stars = self.data["stars"].get(tab_name, [])
        
        if h in tab_stars:
            tab_stars.remove(h)
        else:
            tab_stars.append(h)
        
        self.data["stars"][tab_name] = tab_stars
        self.save_data()

    def is_starred(self, tab_name, config_data):
        h = generate_hash(config_data)
        return h in self.data["stars"].get(tab_name, [])
    
    def save_to_local(self, config_data, custom_name=None):
        """Formerly toggle_favorite - saves a config to the local library"""
        h = generate_hash(config_data)
        self.data['local_scenarios'][h] = {
            "name": custom_name if custom_name else "New Scenario",
            "data": config_data.copy()
        }
        self.save_data()

    def is_local(self, config_data):
        h = generate_hash(config_data)
        return h in self.data['local_scenarios']

    def delete_local(self, config_data):
        h = generate_hash(config_data)
        if h in self.data['local_scenarios']:
            del self.data['local_scenarios'][h]
            self.save_data()