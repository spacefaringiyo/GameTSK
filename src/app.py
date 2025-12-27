import pygame
import sys
from datetime import datetime
from .config import *
from .engine import Engine
from .storage import Storage
from .ui import Slider, Button, ConfigBrowser, TextInput, SaveAsModal, ConfirmationModal, Toggle
from .audio import AudioEngine

class TosokuApp:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        
        # CHANGED: Added pygame.SCALED vsync=1 for smooth resizing
        # The window will technically be 1200x900 but scaled up/down
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags, vsync=1)

        
        pygame.display.set_caption("Project GameTSK Alpha v0.1 - Fullscreen is broken btw")
        self.clock = pygame.time.Clock()
        
        pygame.key.set_repeat(400, 30)
        
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_big = pygame.font.SysFont("consolas", 60)
        
        self.engine = Engine()
        self.storage = Storage()
        self.audio = AudioEngine()
        
        self.apply_global_settings()
        
        self.state = STATE_EDIT
        self.modal = None
        self.modal_type = "" 
        
        self.init_ui()
        
        # Game Vars
        self.timer = 0.0
        self.time_in_zone = 0.0
        self.score = 0.0
        self.warmup_streak = 0.0
        self.warmup_best = 0.0
        self.warmup_total = 0.0

        self.load_config_by_name("Default")

    def apply_global_settings(self):
        s = self.storage.load_global_settings()
        self.audio.update_settings(
            s.get("hit_enabled", True),
            s.get("miss_enabled", False),
            s.get("hit_vol", 0.3),
            s.get("miss_vol", 0.3),
            s.get("hit_freq", 800),
            s.get("miss_freq", 200),
            s.get("tick_rate", 0)
        )

    def init_ui(self):
        # Sliders
        self.sl_smooth = Slider(50, SCREEN_HEIGHT - 130, 200, 10, 1, 100, 15, "Smoothing")
        self.sl_zoom = Slider(50, SCREEN_HEIGHT - 70, 200, 10, 1, 20, 3, "Zoom")
        self.sl_start = Slider(300, SCREEN_HEIGHT - 130, 250, 10, 0, 2000, 500, "Start Speed")
        self.sl_end = Slider(300, SCREEN_HEIGHT - 70, 250, 10, 0, 2000, 500, "End Speed")
        self.sl_tol = Slider(600, SCREEN_HEIGHT - 130, 200, 10, 10, 500, 50, "Tolerance")
        self.sl_dur = Slider(600, SCREEN_HEIGHT - 70, 200, 10, 5, 60, 15, "Duration")
        self.sl_warmup_time = Slider(600, SCREEN_HEIGHT - 20, 200, 10, 0, 5, 0, "Start Buffer (s)")

        # Toggles
        tx, ty = 130, SCREEN_HEIGHT - 200 
        self.tog_up = Toggle(tx, ty - 30, 40, 25, "UP")
        self.tog_down = Toggle(tx, ty, 40, 25, "DN")
        self.tog_left = Toggle(tx - 45, ty, 40, 25, "L")
        self.tog_right = Toggle(tx + 45, ty, 40, 25, "R")
        self.toggles = [self.tog_up, self.tog_down, self.tog_left, self.tog_right]

        # Browser
        self.browser = ConfigBrowser(SCREEN_WIDTH - 250, 60, 220, 300, self.storage)
        self.txt_name = TextInput(SCREEN_WIDTH - 250, 370, 220, 30, "MyConfig")
        
        # File Buttons
        self.btn_new = Button(SCREEN_WIDTH - 250, 410, 50, 30, "NEW", "NEW", color=(80, 40, 40))
        self.btn_save = Button(SCREEN_WIDTH - 195, 410, 50, 30, "SAVE", "SAVE")
        self.btn_save_as = Button(SCREEN_WIDTH - 140, 410, 70, 30, "SAVE AS", "SAVE_AS")
        self.btn_delete = Button(SCREEN_WIDTH - 65, 410, 50, 30, "DEL", "DELETE", color=(100, 20, 20))

        # Game Mode
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.btn_warmup = Button(cx - 150, cy, 140, 50, "WARMUP", "WARMUP", color=(50, 80, 50))
        self.btn_challenge = Button(cx + 10, cy, 140, 50, "CHALLENGE", "CHALLENGE", color=(80, 60, 20))

        self.btn_stats = Button(20, 20, 100, 30, "STATS", "STATS")
        self.btn_back = Button(20, 20, 100, 30, "< BACK", "BACK")
        self.btn_settings = Button(20, 60, 100, 30, "AUDIO", "SETTINGS", color=(80, 80, 100))

        self.sliders = [self.sl_smooth, self.sl_zoom, self.sl_start, self.sl_end, self.sl_tol, self.sl_dur, self.sl_warmup_time]

        # Settings Widgets
        self.tog_hit = Toggle(400, 200, 60, 30, "ON", self.audio.hit_enabled)
        self.tog_miss = Toggle(700, 200, 60, 30, "ON", self.audio.miss_enabled)
        self.sl_hit_vol = Slider(300, 250, 250, 10, 0, 100, int(self.audio.hit_vol*100), "Volume")
        self.sl_miss_vol = Slider(600, 250, 250, 10, 0, 100, int(self.audio.miss_vol*100), "Volume")
        self.sl_hit_freq = Slider(300, 310, 250, 10, 100, 2000, self.audio.hit_freq, "Freq (Hz)")
        self.sl_miss_freq = Slider(600, 310, 250, 10, 100, 2000, self.audio.miss_freq, "Freq (Hz)")
        self.sl_tick_rate = Slider(450, 380, 300, 10, 0, 30, self.audio.tick_rate, "Tick Rate (Hz)")
        self.settings_widgets = [self.sl_hit_vol, self.sl_miss_vol, self.sl_hit_freq, self.sl_miss_freq, self.sl_tick_rate]

    def generate_unique_name(self, base_name):
        existing = self.storage.list_configs()
        candidate = f"{base_name} copy"
        if candidate not in existing: return candidate
        i = 1
        while True:
            candidate = f"{base_name} copy{i}"
            if candidate not in existing: return candidate
            i += 1

    def open_save_as_modal(self):
        current_name = self.txt_name.text
        new_name = self.generate_unique_name(current_name)
        self.modal = SaveAsModal(SCREEN_WIDTH, SCREEN_HEIGHT, new_name, self.font)
        self.modal_type = "SAVE_AS"
        self.state = STATE_MODAL

    def open_delete_modal(self):
        target = self.txt_name.text
        self.modal = ConfirmationModal(SCREEN_WIDTH, SCREEN_HEIGHT, "DELETE CONFIG?", f"Permanently delete '{target}'?", self.font)
        self.modal_type = "DELETE"
        self.state = STATE_MODAL

    def load_config_by_name(self, name):
        data = self.storage.load_config(name)
        if data:
            self.sl_smooth.set_val(data.get('smoothing', 15))
            self.sl_zoom.set_val(data.get('zoom_scale', 3))
            self.sl_start.set_val(data.get('start_speed', 500))
            self.sl_end.set_val(data.get('end_speed', 500))
            self.sl_tol.set_val(data.get('tolerance', 50))
            self.sl_dur.set_val(data.get('duration', 15))
            self.sl_warmup_time.set_val(data.get('warmup_time', 0))
            self.txt_name.text = name
            dirs = data.get('directions', [True, True, True, True])
            self.tog_up.active = dirs[0]
            self.tog_down.active = dirs[1]
            self.tog_left.active = dirs[2]
            self.tog_right.active = dirs[3]

    def reset_to_default(self):
        self.txt_name.text = "NewConfig"
        self.sl_start.set_val(500)
        self.sl_end.set_val(500)
        self.sl_dur.set_val(15)
        self.sl_tol.set_val(50)
        self.sl_warmup_time.set_val(0)
        for t in self.toggles: t.active = True

    def save_current_config(self, force_name=None):
        name = force_name if force_name else self.txt_name.text.strip()
        if not name: return
        data = {
            "smoothing": self.sl_smooth.val,
            "zoom_scale": self.sl_zoom.val,
            "start_speed": self.sl_start.val,
            "end_speed": self.sl_end.val,
            "tolerance": self.sl_tol.val,
            "duration": self.sl_dur.val,
            "warmup_time": self.sl_warmup_time.val,
            "directions": [self.tog_up.active, self.tog_down.active, self.tog_left.active, self.tog_right.active]
        }
        self.storage.save_config(name, data)
        self.browser.refresh()
        self.txt_name.text = name

    def save_global_audio(self):
        data = {
            "hit_enabled": self.tog_hit.active,
            "miss_enabled": self.tog_miss.active,
            "hit_vol": self.sl_hit_vol.val / 100.0,
            "miss_vol": self.sl_miss_vol.val / 100.0,
            "hit_freq": self.sl_hit_freq.val,
            "miss_freq": self.sl_miss_freq.val,
            "tick_rate": self.sl_tick_rate.val
        }
        self.storage.save_global_settings(data)
        self.audio.update_settings(
            data["hit_enabled"], data["miss_enabled"],
            data["hit_vol"], data["miss_vol"],
            data["hit_freq"], data["miss_freq"],
            data["tick_rate"]
        )

    def run(self):
        while True:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # Fixes mouse loss on Resize/Maximize/F11
            if event.type == pygame.VIDEORESIZE or event.type == pygame.WINDOWFOCUSGAINED:
                if self.state in [STATE_WARMUP, STATE_CHALLENGE_IDLE, STATE_CHALLENGE_RUN]:
                    # We are playing, but window changed. Force the grab back.
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                    pygame.mouse.get_rel() # Flush the massive jump caused by the resize
            # ------------------------------

            # --- MODAL HANDLING ---
            if self.state == STATE_MODAL:
                if self.modal:
                    res = self.modal.handle_event(event)
                    if res == "YES":
                        if self.modal_type == "SAVE_AS":
                            new_name = self.modal.get_text()
                            self.save_current_config(force_name=new_name)
                        elif self.modal_type == "DELETE":
                            target = self.txt_name.text
                            self.storage.delete_config(target)
                            self.browser.refresh()
                            self.reset_to_default()
                        self.state = STATE_EDIT
                        self.modal = None
                        self.modal_type = ""
                    elif res == "NO":
                        self.state = STATE_EDIT
                        self.modal = None
                        self.modal_type = ""
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = STATE_EDIT
                        self.modal = None
                        self.modal_type = ""
                return

            # --- SETTINGS MODE ---
            if self.state == STATE_SETTINGS:
                if self.btn_back.handle_event(event) == "BACK":
                    self.save_global_audio() 
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
                        pygame.quit(); sys.exit()
                    else:
                        self.set_state(STATE_EDIT)
                        self.audio.stop_all()
                
                # 2. F11 Fullscreen Logic (The fix from before)
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    # FORCE mouse state sync
                    if self.state in [STATE_EDIT, STATE_SETTINGS, STATE_STATS_VIEW, STATE_MODAL]:
                        pygame.event.set_grab(False)
                        pygame.mouse.set_visible(True)
                    else:
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)

                # 3. Hotkeys (Blocked if typing name)
                if not is_typing:
                    # [Z] RESTART / START
                    if event.key == pygame.K_z:
                        # Challenge Modes: Restart/Start Run
                        if self.state in [STATE_CHALLENGE_IDLE, STATE_CHALLENGE_RUN, STATE_CHALLENGE_END]:
                            self.start_challenge()
                        
                        # Warmup Mode: Reset Stats (New Feature)
                        elif self.state == STATE_WARMUP:
                            self.warmup_streak = 0
                            self.warmup_total = 0
                            self.warmup_best = 0
                            self.engine.reset_graph()

                    # [S] STATS (Only in Edit)
                    elif event.key == pygame.K_s and self.state == STATE_EDIT:
                        self.state = STATE_STATS_VIEW

            # --- EDIT MODE CLICKS ---
            if self.state == STATE_EDIT:
                if self.btn_warmup.handle_event(event) == "WARMUP": self.set_state(STATE_WARMUP)
                if self.btn_challenge.handle_event(event) == "CHALLENGE": self.set_state(STATE_CHALLENGE_IDLE)
                if self.btn_stats.handle_event(event) == "STATS": self.state = STATE_STATS_VIEW
                if self.btn_settings.handle_event(event) == "SETTINGS": self.state = STATE_SETTINGS

                if self.browser.handle_event(event) == "SELECTED":
                    sel = self.browser.get_selected()
                    if sel: 
                        self.load_config_by_name(sel)
                        self.txt_name.text = sel

                if self.btn_new.handle_event(event) == "NEW": self.reset_to_default()
                if self.btn_save.handle_event(event) == "SAVE": self.save_current_config()
                if self.btn_save_as.handle_event(event) == "SAVE_AS": self.open_save_as_modal()
                if self.btn_delete.handle_event(event) == "DELETE": self.open_delete_modal()

                for s in self.sliders: s.handle_event(event)
                for t in self.toggles: t.handle_event(event)

            elif self.state == STATE_STATS_VIEW:
                if self.btn_back.handle_event(event) == "BACK": self.state = STATE_EDIT

    def set_state(self, new_state):
        self.state = new_state
        if new_state == STATE_EDIT:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
        elif new_state in [STATE_WARMUP, STATE_CHALLENGE_IDLE]:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)
            pygame.mouse.get_rel() 
            self.engine.reset_graph()
            self.engine.reset_history()
            
            if new_state == STATE_WARMUP:
                self.warmup_streak = 0
                self.warmup_best = 0
                self.warmup_total = 0

    def start_challenge(self):
        self.state = STATE_CHALLENGE_RUN
        self.timer = -float(self.sl_warmup_time.val)
        self.time_in_zone = 0.0
        self.score = 0.0
        self.engine.reset_graph()
        pygame.mouse.get_rel()

    def update(self, dt):
        if self.state in [STATE_STATS_VIEW, STATE_EDIT, STATE_MODAL, STATE_SETTINGS]:
            return

        self.engine.smoothing_window = self.sl_smooth.val
        dx, dy = pygame.mouse.get_rel()
        
        start_v = self.sl_start.val
        end_v = self.sl_end.val
        duration = self.sl_dur.val
        target = start_v 
        
        if self.state == STATE_CHALLENGE_RUN:
            self.timer += dt
            target = self.engine.get_target_for_time(self.timer, duration, start_v, end_v)
            if self.timer >= duration:
                self.finish_challenge()
                return

        tol = self.sl_tol.val
        dirs = (self.tog_up.active, self.tog_down.active, self.tog_left.active, self.tog_right.active)
        speed, status, diff = self.engine.process_frame(dx, dy, dt, target, tol, dirs)
        
        if self.state == STATE_WARMUP:
            self.audio.update(dt, status)
        elif self.state == STATE_CHALLENGE_RUN:
            if self.timer < 0:
                self.audio.stop_all()
            else:
                self.audio.update(dt, status)
        else:
            self.audio.stop_all()

        color = COLOR_ZONE_LINE
        is_perfect = (status == "PERFECT")
        if status == "LOW": color = COLOR_SLOW
        elif status == "HIGH": color = COLOR_FAST
        elif status == "PERFECT": color = COLOR_PERFECT

        if self.state == STATE_WARMUP:
            if is_perfect:
                self.warmup_streak += dt
                self.warmup_total += dt
                if self.warmup_streak > self.warmup_best: self.warmup_best = self.warmup_streak
            else:
                self.warmup_streak = 0
        
        if self.state == STATE_CHALLENGE_RUN:
            if self.timer >= 0 and is_perfect:
                self.time_in_zone += dt

        self.engine.record_graph_point(speed, color, target)

    def finish_challenge(self):
        self.state = STATE_CHALLENGE_END
        self.audio.stop_all()
        self.timer = self.sl_dur.val
        if self.sl_dur.val > 0:
            self.score = (self.time_in_zone / self.sl_dur.val) * 100
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "config": self.txt_name.text,
            "target": f"{self.sl_start.val}->{self.sl_end.val}",
            "score": round(self.score, 2)
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

    def draw_graph_view(self):
        rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT - 100)
        scale = self.sl_zoom.val * 0.2
        tol = self.sl_tol.val
        cx = SCREEN_WIDTH // 2 
        
        # DRAW PAST
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

        # DRAW FUTURE
        start_v = self.sl_start.val
        end_v = self.sl_end.val
        duration = self.sl_dur.val
        
        future_pixels = SCREEN_WIDTH - cx
        upper_fut = []
        lower_fut = []
        dt_per_px = 1.0 / TARGET_FPS 
        
        for i in range(future_pixels):
            x = cx + i
            if self.state == STATE_CHALLENGE_RUN:
                # Add dt * i to current timer
                # If timer is negative (countdown), this visualizes the moment speed starts
                sim_time = self.timer + (i * dt_per_px)
                tgt = self.engine.get_target_for_time(sim_time, duration, start_v, end_v)
            else:
                tgt = start_v

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

        # CENTER MARKER
        pygame.draw.line(self.screen, (100, 100, 100), (cx, 0), (cx, rect.bottom), 1)

        self.draw_hud()

    def draw_hud(self):
        if self.state == STATE_WARMUP:
            self.draw_text_centered("WARMUP MODE", 20, UI_COLOR)
            self.draw_text_centered(f"{self.warmup_streak:.2f}s", 60, COLOR_PERFECT, self.font_big)
            self.draw_text_centered(f"BEST: {self.warmup_best:.2f}  TOTAL: {self.warmup_total:.2f}", 120, TEXT_GRAY)
            self.draw_text_centered("[ESC] Edit", SCREEN_HEIGHT - 100, ACCENT_COLOR)
        
        elif self.state == STATE_CHALLENGE_IDLE:
            self.draw_text_centered("READY?", 300, UI_COLOR)
            self.draw_text_centered("PRESS [Z]", 360, COLOR_PERFECT, self.font_big)
            self.draw_text_centered(f"Config: {self.txt_name.text}", 420, TEXT_GRAY)
        
        elif self.state == STATE_CHALLENGE_RUN:
            if self.timer < 0:
                countdown_sec = abs(self.timer)
                self.draw_text_centered("STARTS IN", 300, UI_COLOR)
                self.draw_text_centered(f"{countdown_sec:.1f}", 360, COLOR_REC, self.font_big)
                self.draw_text_centered("MATCH SPEED NOW", 430, TEXT_GRAY)
            else:
                rem = max(0, self.sl_dur.val - self.timer)
                self.draw_text_centered(f"{rem:.1f}", 20, UI_COLOR, self.font_big)
                cx = SCREEN_WIDTH // 2
                if int(self.timer * 4) % 2 == 0:
                    pygame.draw.circle(self.screen, COLOR_REC, (cx - 100, 50), 10)
        
        elif self.state == STATE_CHALLENGE_END:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); s.set_alpha(150); s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            self.draw_text_centered(f"{self.score:.2f}%", SCREEN_HEIGHT//2 - 40, COLOR_PERFECT, self.font_big)
            self.draw_text_centered("RUN SAVED", SCREEN_HEIGHT//2 + 20, UI_COLOR)
            self.draw_text_centered("[Z] Retry   [ESC] Edit", SCREEN_HEIGHT//2 + 60, ACCENT_COLOR)

    def draw_settings_ui(self):
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

    def draw_edit_ui(self):
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, SCREEN_HEIGHT - 160, SCREEN_WIDTH, 160))
        for s in self.sliders: s.draw(self.screen, self.font)
        for t in self.toggles: t.draw(self.screen, self.font)
        
        self.browser.draw(self.screen, self.font)
        self.txt_name.draw(self.screen, self.font)
        
        self.btn_new.draw(self.screen, self.font)
        self.btn_save.draw(self.screen, self.font)
        self.btn_save_as.draw(self.screen, self.font)
        self.btn_delete.draw(self.screen, self.font)
        
        self.draw_text_centered(self.txt_name.text, SCREEN_HEIGHT // 2 - 60, UI_COLOR, self.font_big)
        
        self.btn_warmup.draw(self.screen, self.font)
        self.btn_challenge.draw(self.screen, self.font)
        self.btn_stats.draw(self.screen, self.font)
        self.btn_settings.draw(self.screen, self.font)

    def draw_stats_view(self):
        self.screen.fill(STATS_BG_COLOR)
        self.btn_back.draw(self.screen, self.font)
        h = self.storage.load_stats()
        y = 100
        self.draw_text_centered("HISTORY", 40, UI_COLOR, self.font_big)
        pygame.draw.line(self.screen, ACCENT_COLOR, (100, 90), (SCREEN_WIDTH-100, 90))
        for i, row in enumerate(h):
            if y > SCREEN_HEIGHT - 50: break
            c = UI_COLOR
            score = row.get('score', 0)
            if score >= 90: c = COLOR_PERFECT
            date_str = row.get('date', '')
            conf = row.get('config', 'Legacy')
            tgt = str(row.get('target', '???'))
            if len(conf) > 15: conf = conf[:12] + "..."
            txt = f"{date_str} | {conf:<15} | TGT: {tgt:<10} | {score}%"
            self.draw_text_centered(txt, y, c)
            y += 30

    def draw_text_centered(self, text, y, color=UI_COLOR, font=None):
        if font is None: font = self.font
        text_str = str(text)
        surf = font.render(text_str, True, color)
        cx = SCREEN_WIDTH // 2
        self.screen.blit(surf, (cx - surf.get_width()//2, y))