import pygame
from src.states.base import BaseState
import src.core.config as cfg
from src.core.config import *
from src.ui.elements import Button, Slider, Toggle

class SettingsState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 40)
        
        self.init_ui()

    def init_ui(self):
        self.btn_back = Button(20, 20, 100, 30, "< BACK", "BACK")
        
        cx = cfg.SCREEN_WIDTH // 2
        
        # --- VIDEO ---
        res_text = f"{cfg.SCREEN_WIDTH}x{cfg.SCREEN_HEIGHT}"
        # Center the Resolution button (140px wide -> offset 70)
        self.btn_res = Button(cx - 70, 140, 140, 30, res_text, "CYCLE_RES", color=(60, 60, 80))
        
        # FPS Toggle: Place it at y=190, slightly to the right of center
        show_fps = self.app.global_settings.get("show_fps", False)
        self.tog_fps = Toggle(cx + 20, 190, 60, 30, "ON", show_fps)

        # --- AUDIO ---
        s = self.app.global_settings
        base_y = 300
        
        self.tog_hit = Toggle(400, base_y, 60, 30, "ON", s.get("hit_enabled", True))
        self.sl_hit_vol = Slider(300, base_y + 50, 250, 10, 0, 100, int(s.get("hit_vol", 0.3)*100), "Hit Vol")
        self.sl_hit_freq = Slider(300, base_y + 110, 250, 10, 100, 2000, s.get("hit_freq", 150), "Hit Freq")

        self.tog_miss = Toggle(700, base_y, 60, 30, "ON", s.get("miss_enabled", False))
        self.sl_miss_vol = Slider(600, base_y + 50, 250, 10, 0, 100, int(s.get("miss_vol", 0.3)*100), "Miss Vol")
        self.sl_miss_freq = Slider(600, base_y + 110, 250, 10, 100, 2000, s.get("miss_freq", 100), "Miss Freq")
        
        self.sl_tick = Slider(450, base_y + 200, 300, 10, 0, 30, s.get("tick_rate", 20), "Tick Rate")
        
        self.widgets = [
            self.btn_res,
            self.tog_fps,
            self.tog_hit, self.tog_miss,
            self.sl_hit_vol, self.sl_hit_freq,
            self.sl_miss_vol, self.sl_miss_freq,
            self.sl_tick
        ]

    def handle_event(self, event):
        if self.btn_back.handle_event(event) == "BACK":
            self.save_and_exit()
            return

        changed = False
        for w in self.widgets:
            action = w.handle_event(event)
            if action:
                changed = True
                
                # --- NEW LOGIC HERE ---
                if action == "CYCLE_RES":
                    self.cycle_resolution()
                    return 
                # ----------------------
        
        # Fullscreen Check - comment out until fullscreen is solved
        # current_fs = (self.app.screen.get_flags() & pygame.FULLSCREEN) != 0
        # if self.tog_fullscreen.active != current_fs:
        #     pygame.display.toggle_fullscreen()
        #     if not pygame.mouse.get_visible():
        #          pygame.event.set_grab(True)
        
        if changed:
            self.update_live_audio()

    def update_live_audio(self):
        # Send new values to the Audio Engine immediately
        self.app.audio.update_settings(
            self.tog_hit.active, self.tog_miss.active,
            self.sl_hit_vol.val/100.0, self.sl_miss_vol.val/100.0,
            self.sl_hit_freq.val, self.sl_miss_freq.val,
            self.sl_tick.val
        )

    def save_and_exit(self):
        data = {
            "hit_enabled": self.tog_hit.active,
            "miss_enabled": self.tog_miss.active,
            "hit_vol": self.sl_hit_vol.val / 100.0,
            "miss_vol": self.sl_miss_vol.val / 100.0,
            "hit_freq": self.sl_hit_freq.val,
            "miss_freq": self.sl_miss_freq.val,
            "tick_rate": self.sl_tick.val,
            
            "res_w": cfg.SCREEN_WIDTH,
            "res_h": cfg.SCREEN_HEIGHT,
            # NEW: Save FPS Setting
            "show_fps": self.tog_fps.active,
            
            # Preserve Globals
            "sensitivity": self.app.global_settings.get("sensitivity", 100), 
            "last_active_tab": self.app.global_settings.get("last_active_tab", 1)
        }
        self.app.storage.save_global_settings(data)
        self.app.global_settings = data
        
        self.next_state = "EDITOR"
        self.done = True

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.btn_back.draw(screen, self.font)
        
        cx = cfg.SCREEN_WIDTH // 2
        
        t = self.font_big.render("SETTINGS", True, UI_COLOR)
        screen.blit(t, (cx - t.get_width()//2, 40))
        
        # --- VIDEO ---
        pygame.draw.line(screen, (50, 50, 50), (100, 100), (cfg.SCREEN_WIDTH-100, 100))
        
        # Resolution Label (Above button)
        self.draw_text_centered(screen, "DISPLAY RESOLUTION", 110, UI_COLOR)
        
        # FPS Label (To the left of the toggle)
        # Toggle is at (cx + 20, 190). Text should be at (cx - 20 - text_width, 195)
        fps_txt = self.font.render("Show FPS Counter", True, TEXT_GRAY)
        screen.blit(fps_txt, (cx - 20 - fps_txt.get_width(), 195))

        # --- AUDIO ---
        pygame.draw.line(screen, (50, 50, 50), (100, 250), (cfg.SCREEN_WIDTH-100, 250))
        self.draw_text_centered(screen, "AUDIO", 260, UI_COLOR)
        
        t_hit = self.font_big.render("HIT", True, COLOR_PERFECT)
        screen.blit(t_hit, (300 + 125 - t_hit.get_width()//2, 350)) 
        
        t_miss = self.font_big.render("MISS", True, COLOR_FAST)
        screen.blit(t_miss, (600 + 125 - t_miss.get_width()//2, 350))

        for w in self.widgets: w.draw(screen, self.font)

        rate_val = self.sl_tick.val
        msg = "Continuous Drone" if rate_val == 0 else f"{rate_val} Shots / Sec"
        self.draw_text_centered(screen, msg, 535, TEXT_GRAY)

    def draw_text_centered(self, screen, text, y, color):
        s = self.font.render(text, True, color)
        # Use cfg.SCREEN_WIDTH for centering
        screen.blit(s, (cfg.SCREEN_WIDTH//2 - s.get_width()//2, y))

    def cycle_resolution(self):
        modes = [(1600, 900), (1920, 1080), (2560, 1440)]
        current = (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        
        idx = 0
        if current in modes:
            idx = modes.index(current)
            
        idx = (idx + 1) % len(modes)
        new_w, new_h = modes[idx]
        
        self.app.set_resolution(new_w, new_h)
