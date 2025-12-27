import pygame
import sys
import math
from datetime import datetime
from .config import *
from .engine import Engine
from .storage import Storage
from .ui import Slider, Button, TabbedBrowser, NameModal, Toggle, EditFavModal, SaveAsModal, ConfirmationModal, TextInput
from .audio import AudioEngine
from .utils import encode_config, decode_config, generate_hash


class TosokuApp:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        
        flags = pygame.SCALED
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags, vsync=1)
        pygame.display.set_caption("TSK AimTrainer Alpha v2.0 - UI Remaster")
        self.clock = pygame.time.Clock()
        
        pygame.key.set_repeat(400, 30)
        
        # --- FIX: CHANGE FONT ---
        # Consolas doesn't support the arrow/star symbols well.
        # We try a list of fonts. 'segoe ui symbol' is great on Windows for icons.
        # 'arial' is a safe backup.
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 60)
        
        self.engine = Engine()
        self.storage = Storage()
        self.audio = AudioEngine()
        # Load Settings into a variable so we can access them later
        self.global_settings = self.storage.load_global_settings()
        
        # Apply Audio immediately
        self.audio.update_settings(
            self.global_settings.get("hit_enabled", True),
            self.global_settings.get("miss_enabled", False),
            self.global_settings.get("hit_vol", 0.3),
            self.global_settings.get("miss_vol", 0.3),
            self.global_settings.get("hit_freq", 150),
            self.global_settings.get("miss_freq", 100),
            self.global_settings.get("tick_rate", 20)
        )
        
        self.state = STATE_EDIT
        self.modal = None
        
        self.init_ui()
        
        # Game Vars
        self.timer = 0.0
        self.time_in_zone = 0.0
        self.score = 0.0
        self.warmup_streak = 0.0
        self.warmup_best = 0.0
        self.warmup_total = 0.0
        self.is_pb = False
        self.cached_pb = 0.0

        if self.storage.data['recents']:
            self.load_config(self.storage.data['recents'][0])
        else:
            self.reset_to_default()

    def apply_global_settings(self):
        s = self.storage.load_global_settings()
        self.audio.update_settings(
            s.get("hit_enabled", True), s.get("miss_enabled", False),
            s.get("hit_vol", 0.3), s.get("miss_vol", 0.3),
            s.get("hit_freq", 400), s.get("miss_freq", 150),
            s.get("tick_rate", 10)
        )

    def init_ui(self):
        # PANEL LAYOUT
        # Base Y for the top row of sliders
        # Panel height ~240, so starts at SCREEN_HEIGHT - 240
        # Sliders start a bit lower to make room for Toggles
        base_y = SCREEN_HEIGHT - 170
        col_width = 260
        gap_y = 50 # Vertical space between rows
        
        # --- COLUMN A: PHYSICS (Left) ---
        # Matches: [SPEED] ±[TOL]
        x_a = 50
        self.sl_start = Slider(x_a, base_y, col_width, 10, 0, 2000, 500, "Start Speed")
        self.sl_end = Slider(x_a, base_y + gap_y, col_width, 10, 0, 2000, 500, "End Speed")
        self.sl_tol = Slider(x_a, base_y + gap_y * 2, col_width, 10, 10, 500, 50, "Tolerance")

        # --- COLUMN B: FEEL (Center) ---
        # Matches: (sm[S] z[Z])
        x_b = 470
        self.sl_smooth = Slider(x_b, base_y, col_width, 10, 1, 100, 15, "Smoothing")
        self.sl_zoom = Slider(x_b, base_y + gap_y, col_width, 10, 1, 20, 3, "Zoom")

        # --- COLUMN C: TIME (Right) ---
        # Matches: b[B] [D]s
        x_c = 890
        self.sl_warmup_time = Slider(x_c, base_y, col_width, 10, 0, 5, 0, "Start Buffer (s)")
        self.sl_dur = Slider(x_c, base_y + gap_y, col_width, 10, 1, 60, 15, "Duration")

        # --- DIRECTION TOGGLES ---
        # Placed above Column A (Physics)
        # Center X of Col A = 50 + 130 = 180
        tx, ty = 180, base_y - 60 
        self.tog_up = Toggle(tx, ty - 30, 40, 25, "UP")
        self.tog_down = Toggle(tx, ty, 40, 25, "DN")
        self.tog_left = Toggle(tx - 45, ty, 40, 25, "L")
        self.tog_right = Toggle(tx + 45, ty, 40, 25, "R")
        self.toggles = [self.tog_up, self.tog_down, self.tog_left, self.tog_right]

        # --- BROWSER (Top Center) ---
        browser_w = 800
        browser_h = 300 # Slightly shorter to accommodate taller panel
        bx = (SCREEN_WIDTH - browser_w) // 2
        by = 20
        self.browser = TabbedBrowser(bx, by, browser_w, browser_h, self.storage)
        
        # --- ACTION BUTTONS ---
        btn_y = by + browser_h + 10
        btn_w = 100
        start_x = (SCREEN_WIDTH - 320) // 2
        self.btn_copy = Button(start_x, btn_y, btn_w, 30, "COPY", "COPY")
        self.btn_paste = Button(start_x + 110, btn_y, btn_w, 30, "PASTE", "PASTE")
        self.btn_star = Button(start_x + 220, btn_y, btn_w, 30, "★ FAV", "STAR", color=(100, 80, 20))

        # --- PLAY BUTTONS ---
        # Adjusted Y to fit between Actions and Panel
        cy = SCREEN_HEIGHT // 2 + 110
        cx = SCREEN_WIDTH // 2
        self.btn_warmup = Button(cx - 150, cy, 140, 50, "WARMUP", "WARMUP", color=(50, 80, 50))
        self.btn_challenge = Button(cx + 10, cy, 140, 50, "CHALLENGE", "CHALLENGE", color=(80, 60, 20))

        # --- CORNER BUTTONS ---
        self.btn_stats = Button(20, 20, 100, 30, "STATS", "STATS")
        self.btn_settings = Button(20, 60, 100, 30, "AUDIO", "SETTINGS", color=(80, 80, 100))
        self.btn_back = Button(20, 20, 100, 30, "< BACK", "BACK")

        # Dummy Buttons
        self.txt_name = TextInput(0,0,0,0,""); self.btn_new = Button(0,0,0,0,"",""); self.btn_save = Button(0,0,0,0,"",""); self.btn_save_as = Button(0,0,0,0,"",""); self.btn_delete = Button(0,0,0,0,"",""); self.btn_load = Button(0,0,0,0,"","")

        self.sliders = [self.sl_smooth, self.sl_zoom, self.sl_start, self.sl_end, self.sl_tol, self.sl_dur, self.sl_warmup_time]
        
        # Settings Widgets (Audio)
        self.tog_hit = Toggle(400, 200, 60, 30, "ON", self.audio.hit_enabled)
        self.tog_miss = Toggle(700, 200, 60, 30, "ON", self.audio.miss_enabled)
        self.sl_hit_vol = Slider(300, 250, 250, 10, 0, 100, int(self.audio.hit_vol*100), "Volume")
        self.sl_miss_vol = Slider(600, 250, 250, 10, 0, 100, int(self.audio.miss_vol*100), "Volume")
        self.sl_hit_freq = Slider(300, 310, 250, 10, 100, 2000, self.audio.hit_freq, "Freq (Hz)")
        self.sl_miss_freq = Slider(600, 310, 250, 10, 100, 2000, self.audio.miss_freq, "Freq (Hz)")
        self.sl_tick_rate = Slider(450, 380, 300, 10, 0, 30, self.audio.tick_rate, "Tick Rate (Hz)")
        self.settings_widgets = [self.sl_hit_vol, self.sl_miss_vol, self.sl_hit_freq, self.sl_miss_freq, self.sl_tick_rate]

    def get_current_config_dict(self):
        return {
            "smoothing": self.sl_smooth.val,
            "zoom_scale": self.sl_zoom.val,
            "start_speed": self.sl_start.val,
            "end_speed": self.sl_end.val,
            "tolerance": self.sl_tol.val,
            "duration": self.sl_dur.val,
            "warmup_time": self.sl_warmup_time.val,
            "directions": [t.active for t in self.toggles]
        }

    def load_config(self, data):
        self.sl_smooth.set_val(data.get('smoothing', 15))
        self.sl_zoom.set_val(data.get('zoom_scale', 3))
        self.sl_start.set_val(data.get('start_speed', 500))
        self.sl_end.set_val(data.get('end_speed', 500))
        self.sl_tol.set_val(data.get('tolerance', 50))
        self.sl_dur.set_val(data.get('duration', 15))
        self.sl_warmup_time.set_val(data.get('warmup_time', 0))
        dirs = data.get('directions', [True, True, True, True])
        for i, t in enumerate(self.toggles): t.active = dirs[i]

    def reset_to_default(self):
        self.txt_name.text = "NewConfig"
        
        # A nice balanced starting point
        self.sl_smooth.set_val(75)
        self.sl_zoom.set_val(2)
        self.sl_start.set_val(500)
        self.sl_end.set_val(500)
        self.sl_tol.set_val(100)
        self.sl_dur.set_val(10) # 30s is standard for benchmarks
        self.sl_warmup_time.set_val(0)
        
        # Default to Horizontal Only (Standard tracking)
        self.tog_up.active = True
        self.tog_down.active = True
        self.tog_left.active = True
        self.tog_right.active = True

    # --- Actions ---
    def action_copy(self):
        code = encode_config(self.get_current_config_dict())
        if code:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, code.encode('utf-8'))
            print("Copied:", code)

    def action_paste(self):
        pygame.scrap.init()
        content = pygame.scrap.get(pygame.SCRAP_TEXT)
        if content:
            code = content.decode('utf-8').strip().strip('\x00') # Clean null bytes
            data = decode_config(code)
            if data:
                self.load_config(data)
                self.storage.add_imported(data) # Auto-add to history
                self.browser.refresh()

    def action_star(self):
        curr = self.get_current_config_dict()
        
        if self.storage.is_favorite(curr):
            # Already a favorite? Open EDIT/UNSTAR menu
            current_name = self.storage.get_display_name(curr).replace("★ ", "")
            self.modal = EditFavModal(SCREEN_WIDTH, SCREEN_HEIGHT, current_name, self.font)
            self.modal_type = "EDIT_FAV"
            self.state = STATE_MODAL
        else:
            # Not a favorite? Open NAME menu
            auto_name = self.storage.get_display_name(curr)
            self.modal = NameModal(SCREEN_WIDTH, SCREEN_HEIGHT, auto_name, self.font)
            self.modal_type = "ADD_FAV"
            self.state = STATE_MODAL

    def save_global_settings(self):
        data = {
            "hit_enabled": self.tog_hit.active,
            "miss_enabled": self.tog_miss.active,
            "hit_vol": self.sl_hit_vol.val / 100.0,
            "miss_vol": self.sl_miss_vol.val / 100.0,
            "hit_freq": self.sl_hit_freq.val,
            "miss_freq": self.sl_miss_freq.val,
            "tick_rate": self.sl_tick_rate.val,
            
            # NEW: Save current UI State
            "last_active_tab": self.browser.active_tab
        }
        self.storage.save_global_settings(data)
        
        # Update Audio Engine (just in case called from Settings menu)
        self.audio.update_settings(
            data["hit_enabled"], data["miss_enabled"],
            data["hit_vol"], data["miss_vol"],
            data["hit_freq"], data["miss_freq"],
            data["tick_rate"]
        )

    # --- Core Loops ---
    def run(self):
        while True:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_global_settings()
                pygame.quit(); sys.exit()

            # --- MODAL HANDLING ---
            if self.state == STATE_MODAL:
                if self.modal:
                    res = self.modal.handle_event(event)
                    
                    # 1. ADD FAVORITE (NameModal)
                    if self.modal_type == "ADD_FAV":
                        if res == "OK":
                            name = self.modal.get_text()
                            self.storage.toggle_favorite(self.get_current_config_dict(), name)
                            self.browser.refresh()
                            self.browser.active_tab = 1 # Switch to Fav tab
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""
                        elif res == "CANCEL" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""

                    # 2. EDIT FAVORITE (EditFavModal)
                    elif self.modal_type == "EDIT_FAV":
                        if res == "UPDATE":
                            new_name = self.modal.get_text()
                            self.storage.update_favorite_name(self.get_current_config_dict(), new_name)
                            self.browser.refresh()
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""
                        elif res == "UNSTAR":
                            self.storage.toggle_favorite(self.get_current_config_dict())
                            self.browser.refresh()
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""
                        elif res == "CANCEL" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""

                    # 3. SAVE AS (SaveAsModal)
                    elif self.modal_type == "SAVE_AS":
                        if res == "YES":
                            self.save_current_config(force_name=self.modal.get_text())
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""
                        elif res == "NO" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""

                    # 4. DELETE (ConfirmationModal)
                    elif self.modal_type == "DELETE":
                        if res == "YES":
                            target = self.txt_name.text
                            self.storage.delete_config(target)
                            self.browser.refresh()
                            self.reset_to_default()
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""
                        elif res == "NO" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            self.state = STATE_EDIT; self.modal = None; self.modal_type = ""
                return

            # --- SETTINGS MODE ---
            if self.state == STATE_SETTINGS:
                if self.btn_back.handle_event(event) == "BACK":
                    self.save_global_settings() 
                    self.state = STATE_EDIT
                
                changed = False
                if self.tog_hit.handle_event(event): changed = True
                if self.tog_miss.handle_event(event): changed = True
                for s in self.settings_widgets:
                    if s.handle_event(event): changed = True
                
                if changed:
                    self.audio.update_settings(
                        self.tog_hit.active, self.tog_miss.active,
                        self.sl_hit_vol.val/100.0, self.sl_miss_vol.val/100.0,
                        self.sl_hit_freq.val, self.sl_miss_freq.val,
                        self.sl_tick_rate.val
                    )
                return

            # --- EDIT/GAME INPUT ---
            is_typing = False
            if self.state == STATE_EDIT:
                self.txt_name.handle_event(event)
                is_typing = self.txt_name.active

            if event.type == pygame.KEYDOWN:
                # 1. ESC Logic
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_EDIT:
                        self.save_global_settings() # <--- Save before dying!
                        pygame.quit(); sys.exit()
                    else:
                        self.set_state(STATE_EDIT)
                        self.audio.stop_all()

                
                # 2. F11 Fullscreen Logic (REMOVED FOR STABILITY)
                # if event.key == pygame.K_F11: pass 

                # 3. Hotkeys
                if not is_typing:
                    if event.key == pygame.K_z:
                        if self.state in [STATE_CHALLENGE_IDLE, STATE_CHALLENGE_RUN, STATE_CHALLENGE_END]:
                            self.start_challenge()
                        elif self.state == STATE_WARMUP:
                            self.warmup_streak = 0; self.engine.reset_graph()
                    elif event.key == pygame.K_s and self.state == STATE_EDIT:
                        self.state = STATE_STATS_VIEW

            # --- EDIT MODE CLICKS ---
            if self.state == STATE_EDIT:
                # Main Navigation
                if self.btn_warmup.handle_event(event) == "WARMUP": self.set_state(STATE_WARMUP)
                if self.btn_challenge.handle_event(event) == "CHALLENGE": self.set_state(STATE_CHALLENGE_IDLE)
                if self.btn_stats.handle_event(event) == "STATS": self.state = STATE_STATS_VIEW
                if self.btn_settings.handle_event(event) == "SETTINGS": self.state = STATE_SETTINGS

                # Browser
                res = self.browser.handle_event(event)
                if isinstance(res, dict): 
                    self.load_config(res)
                    # Update the text box with the name
                    self.txt_name.text = self.storage.get_display_name(res).replace("★ ", "")


                # Actions
                if self.btn_copy.handle_event(event) == "COPY": self.action_copy()
                if self.btn_paste.handle_event(event) == "PASTE": self.action_paste()
                if self.btn_star.handle_event(event) == "STAR": self.action_star()

                # Legacy File Buttons (If still drawn)
                if self.btn_new.handle_event(event) == "NEW": self.reset_to_default()
                if self.btn_save.handle_event(event) == "SAVE": self.save_current_config()
                if self.btn_save_as.handle_event(event) == "SAVE_AS": self.open_save_as_modal()
                if self.btn_delete.handle_event(event) == "DELETE": self.open_delete_modal()

                # Controls
                for s in self.sliders: s.handle_event(event)
                changed = False
                for t in self.toggles:
                    if t.handle_event(event): changed = True
                # if changed: self.validate_toggles() # Disabled

            elif self.state == STATE_STATS_VIEW:
                if self.btn_back.handle_event(event) == "BACK": self.state = STATE_EDIT


    def set_state(self, new_state):
        self.state = new_state
        if new_state == STATE_EDIT:
            pygame.event.set_grab(False); pygame.mouse.set_visible(True)
        elif new_state in [STATE_WARMUP, STATE_CHALLENGE_IDLE]:
            pygame.event.set_grab(True); pygame.mouse.set_visible(False); pygame.mouse.get_rel()
            self.engine.reset_graph(); self.engine.reset_history()
            if new_state == STATE_WARMUP: self.warmup_streak = 0; self.warmup_best = 0; self.warmup_total = 0

    def start_challenge(self):
        self.state = STATE_CHALLENGE_RUN
        self.timer = -float(self.sl_warmup_time.val)
        self.time_in_zone = 0; self.score = 0
        self.engine.reset_graph(); pygame.mouse.get_rel()
        
        # AUTO SAVE TO RECENTS
        curr = self.get_current_config_dict()
        self.storage.add_recent(curr)
        self.browser.refresh()

    def update(self, dt):
        # --- MOUSE WATCHDOG ---
        # Ensures mouse stays locked if you Alt-Tab out and back in
        if self.state in [STATE_WARMUP, STATE_CHALLENGE_IDLE, STATE_CHALLENGE_RUN]:
            if pygame.mouse.get_focused() and not pygame.event.get_grab():
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)
        # ----------------------

        if self.state in [STATE_STATS_VIEW, STATE_EDIT, STATE_MODAL, STATE_SETTINGS]:
            return

        # ... (rest of logic remains exactly the same) ...
        self.engine.smoothing_window = self.sl_smooth.val
        dx, dy = pygame.mouse.get_rel()
        start_v, end_v, duration = self.sl_start.val, self.sl_end.val, self.sl_dur.val
        target = start_v 
        
        if self.state == STATE_CHALLENGE_RUN:
            self.timer += dt
            target = self.engine.get_target_for_time(self.timer, duration, start_v, end_v)
            if self.timer >= duration:
                self.finish_challenge()
                return

        tol = self.sl_tol.val
        dirs = [t.active for t in self.toggles]
        speed, status, diff = self.engine.process_frame(dx, dy, dt, target, tol, dirs)
        
        if self.state == STATE_WARMUP: self.audio.update(dt, status)
        elif self.state == STATE_CHALLENGE_RUN:
            if self.timer < 0: self.audio.stop_all()
            else: self.audio.update(dt, status)
        else: self.audio.stop_all()

        color = COLOR_ZONE_LINE
        is_perfect = (status == "PERFECT")
        if status == "LOW": color = COLOR_SLOW
        elif status == "HIGH": color = COLOR_FAST
        elif status == "PERFECT": color = COLOR_PERFECT

        if self.state == STATE_WARMUP:
            if is_perfect:
                self.warmup_streak += dt; self.warmup_total += dt
                if self.warmup_streak > self.warmup_best: self.warmup_best = self.warmup_streak
            else: self.warmup_streak = 0
        
        if self.state == STATE_CHALLENGE_RUN:
            if self.timer >= 0 and is_perfect: self.time_in_zone += dt

        self.engine.record_graph_point(speed, color, target)

    def finish_challenge(self):
        self.state = STATE_CHALLENGE_END
        self.audio.stop_all()
        self.timer = self.sl_dur.val
        if self.sl_dur.val > 0:
            self.score = (self.time_in_zone / self.sl_dur.val) * 100
        
        # --- PB LOGIC ---
        curr_dict = self.get_current_config_dict()
        curr_hash = generate_hash(curr_dict)
        previous_best = self.storage.get_high_score(curr_hash)
        
        if self.score > previous_best and self.score > 0:
            self.is_pb = True
            self.cached_pb = self.score # New Record is the current score
        else:
            self.is_pb = False
            self.cached_pb = previous_best # Keep the old record
            
        # Get Name & Save
        name = self.storage.get_display_name(curr_dict)
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "config": name,
            "target": f"{self.sl_start.val}->{self.sl_end.val}",
            "score": round(self.score, 2),
            "hash": curr_hash 
        }
        self.storage.save_run(entry)

    def draw(self):
        self.screen.fill(BG_COLOR)
        if self.state == STATE_STATS_VIEW: self.draw_stats_view()
        elif self.state == STATE_SETTINGS: self.draw_settings_ui()
        elif self.state == STATE_EDIT: self.draw_edit_ui()
        elif self.state == STATE_MODAL: 
            self.draw_edit_ui()
            if self.modal: self.modal.draw(self.screen, self.font)
        else: self.draw_graph_view()
        pygame.display.flip()
    
    # ... (draw_graph_view, draw_hud, draw_settings_ui, draw_stats_view same as before) ...
    # BUT draw_edit_ui needs update for new buttons

    def draw_edit_ui(self):
        # Draw Taller Panel (240px)
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, SCREEN_HEIGHT - 240, SCREEN_WIDTH, 240))
        
        for s in self.sliders: s.draw(self.screen, self.font)
        for t in self.toggles: t.draw(self.screen, self.font)
        
        self.browser.draw(self.screen, self.font)
        
        self.btn_copy.draw(self.screen, self.font)
        self.btn_paste.draw(self.screen, self.font)
        self.btn_star.draw(self.screen, self.font)
        
        # Display Current Config Name
        curr = self.get_current_config_dict()
        name = self.storage.get_display_name(curr)
        # Position centered between actions and play buttons
        # Browser ~320 bottom, Panel ~660 top. Midpoint ~490
        self.draw_text_centered(name, 420, UI_COLOR, self.font_big)
        
        self.btn_warmup.draw(self.screen, self.font)
        self.btn_challenge.draw(self.screen, self.font)
        
        self.btn_stats.draw(self.screen, self.font)
        self.btn_settings.draw(self.screen, self.font)

    def draw_text_centered(self, text, y, color=UI_COLOR, font=None):
        if font is None: font = self.font
        text_str = str(text)
        
        surf = font.render(text_str, True, color)
        
        # --- FIX: Dynamic Scaling ---
        max_w = SCREEN_WIDTH - 40 # Leave some padding
        if surf.get_width() > max_w:
            # Calculate scale factor
            ratio = max_w / surf.get_width()
            new_w = int(surf.get_width() * ratio)
            new_h = int(surf.get_height() * ratio)
            # Resize
            surf = pygame.transform.smoothscale(surf, (new_w, new_h))
            
        cx = SCREEN_WIDTH // 2
        self.screen.blit(surf, (cx - surf.get_width()//2, y))

    def draw_graph_view(self):
        rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT - 100)
        scale = self.sl_zoom.val * 0.2
        tol = self.sl_tol.val
        cx = SCREEN_WIDTH // 2 
        
        points = self.engine.graph_points
        if len(points) > 1:
            upper_past = []
            lower_past = []
            line_pts = []
            start_index = max(0, len(points) - cx)
            visible_points = list(points)[start_index:]
            offset = len(visible_points) - 1
            for i, (spd, col, tgt) in enumerate(visible_points):
                x = cx - (offset - i)
                yu = rect.bottom - ((tgt + tol) * scale)
                yl = rect.bottom - ((tgt - tol) * scale)
                ys = rect.bottom - (spd * scale)
                upper_past.append((x, max(0, yu)))
                lower_past.append((x, max(0, yl)))
                line_pts.append((x, max(0, ys), col))
            if len(upper_past) > 1:
                poly = upper_past + lower_past[::-1]
                surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(surf, (255, 255, 255, 30), poly)
                self.screen.blit(surf, (0,0))
                pygame.draw.lines(self.screen, COLOR_ZONE_LINE, False, upper_past, 1)
                pygame.draw.lines(self.screen, COLOR_ZONE_LINE, False, lower_past, 1)
            if len(line_pts) > 1:
                for i in range(len(line_pts)-1):
                    p1 = line_pts[i]
                    p2 = line_pts[i+1]
                    pygame.draw.line(self.screen, p2[2], (p1[0], p1[1]), (p2[0], p2[1]), 2)

        start_v, end_v, duration = self.sl_start.val, self.sl_end.val, self.sl_dur.val
        future_pixels = SCREEN_WIDTH - cx
        upper_fut, lower_fut = [], []
        dt_per_px = 1.0 / TARGET_FPS 
        for i in range(future_pixels):
            x = cx + i
            if self.state == STATE_CHALLENGE_RUN:
                tgt = self.engine.get_target_for_time(self.timer + (i * dt_per_px), duration, start_v, end_v)
            else: tgt = start_v
            yu = rect.bottom - ((tgt + tol) * scale)
            yl = rect.bottom - ((tgt - tol) * scale)
            upper_fut.append((x, max(0, yu)))
            lower_fut.append((x, max(0, yl)))
        if len(upper_fut) > 1:
            poly = upper_fut + lower_fut[::-1]
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(surf, (255, 255, 255, 30), poly)
            self.screen.blit(surf, (0,0))
            pygame.draw.lines(self.screen, (60, 60, 60), False, upper_fut, 1)
            pygame.draw.lines(self.screen, (60, 60, 60), False, lower_fut, 1)

        pygame.draw.line(self.screen, (100, 100, 100), (cx, 0), (cx, rect.bottom), 1)
        self.draw_hud()

    def draw_hud(self):
        # Shared: Get current config name for display
        curr_dict = self.get_current_config_dict()
        conf_name = self.storage.get_display_name(curr_dict)
        cx = SCREEN_WIDTH // 2

        if self.state == STATE_WARMUP:
            self.draw_text_centered("WARMUP MODE", 20, UI_COLOR)
            self.draw_text_centered(f"{self.warmup_streak:.2f}s", 60, COLOR_PERFECT, self.font_big)
            self.draw_text_centered(f"BEST: {self.warmup_best:.2f}  TOTAL: {self.warmup_total:.2f}", 120, TEXT_GRAY)
            self.draw_text_centered("[ESC] Edit", SCREEN_HEIGHT - 100, ACCENT_COLOR)
        
        elif self.state == STATE_CHALLENGE_IDLE:
            self.draw_text_centered("READY?", 300, UI_COLOR)
            self.draw_text_centered("PRESS [Z]", 360, COLOR_PERFECT, self.font_big)
            self.draw_text_centered(f"Config: {conf_name}", 420, TEXT_GRAY)
        
        elif self.state == STATE_CHALLENGE_RUN:
            # 1. Display Config Name at top
            self.draw_text_centered(conf_name, 30, TEXT_GRAY)

            # 2. Timer (Moved down slightly to Y=70)
            if self.timer < 0:
                self.draw_text_centered("STARTS IN", 300, UI_COLOR)
                self.draw_text_centered(f"{abs(self.timer):.1f}", 360, COLOR_REC, self.font_big)
                self.draw_text_centered("MATCH SPEED NOW", 430, TEXT_GRAY)
            else:
                rem = max(0, self.sl_dur.val - self.timer)
                self.draw_text_centered(f"{rem:.1f}", 70, UI_COLOR, self.font_big)
                
                # Rec Dot (Moved down to Y=120)
                if int(self.timer * 4) % 2 == 0: 
                    pygame.draw.circle(self.screen, COLOR_REC, (cx - 100, 100), 10)
        
        elif self.state == STATE_CHALLENGE_END:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); s.set_alpha(200); s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            
            # 1. Config Name
            self.draw_text_centered(conf_name, 50, UI_COLOR)

            # 2. Main Status (New Record OR Just PB display)
            if self.is_pb:
                # Flashing "NEW RECORD"
                alpha = abs(math.sin(pygame.time.get_ticks() / 800)) * 255
                pb_surf = self.font_big.render("NEW PERSONAL RECORD!", True, (255, 215, 0))
                pb_surf.set_alpha(int(alpha))
                self.screen.blit(pb_surf, (cx - pb_surf.get_width()//2, SCREEN_HEIGHT//2 - 150))
            else:
                # Show existing PB quietly
                # Only show if there IS a previous PB (greater than 0)
                if self.cached_pb > 0:
                    self.draw_text_centered(f"PB: {self.cached_pb:.2f}%", SCREEN_HEIGHT//2 - 120, TEXT_GRAY)
            
            # 3. Current Score (Big)
            self.draw_text_centered(f"{self.score:.2f}%", SCREEN_HEIGHT//2 - 40, COLOR_PERFECT, self.font_big)
            
            # 4. Footer
            self.draw_text_centered("RUN SAVED", SCREEN_HEIGHT//2 + 60, UI_COLOR)
            self.draw_text_centered("[Z] Retry   [ESC] Edit", SCREEN_HEIGHT//2 + 110, ACCENT_COLOR)


    def draw_settings_ui(self):
        # ... (Same as before) ...
        self.screen.fill(BG_COLOR)
        self.btn_back.draw(self.screen, self.font)
        self.draw_text_centered("GLOBAL AUDIO SETTINGS", 40, UI_COLOR, self.font_big)
        t_hit = self.font_big.render("HIT", True, COLOR_PERFECT)
        self.screen.blit(t_hit, (300 + 125 - t_hit.get_width()//2, 140))
        self.tog_hit.draw(self.screen, self.font)
        self.sl_hit_vol.draw(self.screen, self.font)
        self.sl_hit_freq.draw(self.screen, self.font)
        t_miss = self.font_big.render("MISS", True, COLOR_FAST)
        self.screen.blit(t_miss, (600 + 125 - t_miss.get_width()//2, 140))
        self.tog_miss.draw(self.screen, self.font)
        self.sl_miss_vol.draw(self.screen, self.font)
        self.sl_miss_freq.draw(self.screen, self.font)
        self.sl_tick_rate.draw(self.screen, self.font)
        rate_val = self.sl_tick_rate.val
        msg = "Continuous Drone" if rate_val == 0 else f"{rate_val} Shots / Sec"
        self.draw_text_centered(msg, 415, TEXT_GRAY)

    def draw_stats_view(self):
        self.screen.fill(STATS_BG_COLOR)
        self.btn_back.draw(self.screen, self.font)
        
        h = self.storage.load_stats()
        y = 100
        self.draw_text_centered("HISTORY", 40, UI_COLOR, self.font_big)
        
        # Draw Header Line
        pygame.draw.line(self.screen, ACCENT_COLOR, (100, 90), (SCREEN_WIDTH-100, 90))
        
        for i, row in enumerate(h):
            if y > SCREEN_HEIGHT - 50: break
            c = UI_COLOR
            
            # Get Data Safely
            score = row.get('score', 0)
            if score >= 90: c = COLOR_PERFECT
            
            date_str = row.get('date', '')
            conf = row.get('config', 'Legacy')
            tgt = str(row.get('target', '???'))
            
            # Truncate long names for the table
            if len(conf) > 15: conf = conf[:12] + "..."
            
            txt = f"{date_str} | {conf:<15} | TGT: {tgt:<10} | {score}%"
            self.draw_text_centered(txt, y, c)
            y += 30