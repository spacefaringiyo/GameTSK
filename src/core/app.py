import pygame
import sys
import src.core.config as cfg # We import the module object so we can write to it
from .config import TARGET_FPS # Constants like this are fine
from src.engine.audio import AudioEngine
from src.engine.storage import Storage

class TosokuApp:
    def __init__(self, state_dict, start_state):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass # Not on Windows or older version, ignore
        pygame.init()
        pygame.mixer.pre_init(44100, -16, 1, 512)

        pygame.key.set_repeat(400, 30) 
        
        self.clock = pygame.time.Clock()
        self.storage = Storage()
        self.audio = AudioEngine()
        self.debug_font = pygame.font.SysFont("arial", 16)
        pygame.display.set_caption("TSK AimTrainer (TAT) Alpha v0.3")
        
        # --- NEW: LOAD SAVED RESOLUTION ---
        self.global_settings = self.storage.load_global_settings()
        
        # Ensure Sensitivity exists (Default 100%)
        if "sensitivity" not in self.global_settings:
            self.global_settings["sensitivity"] = 100 
        
        # Default to 1200x900 if not saved
        w = self.global_settings.get("res_w", 1600)
        h = self.global_settings.get("res_h", 900)
        
        # 1. Update the Config Module globally
        cfg.SCREEN_WIDTH = w
        cfg.SCREEN_HEIGHT = h
        
        # 2. Create Screen
        # Remove 'vsync=1' if you want to avoid the "red line" lag bug potential
        self.screen = pygame.display.set_mode((w, h), pygame.SCALED, vsync=0) 
        # ----------------------------------

        # Audio Init...
        self.audio.update_settings(
             # ... (keep existing audio params) ...
             self.global_settings.get("hit_enabled", True),
             self.global_settings.get("miss_enabled", False),
             self.global_settings.get("hit_vol", 0.3),
             self.global_settings.get("miss_vol", 0.3),
             self.global_settings.get("hit_freq", 150),
             self.global_settings.get("miss_freq", 100),
             self.global_settings.get("tick_rate", 20)
        )
        
        self.state_dict = state_dict
        self.state_name = start_state

    def set_resolution(self, w, h):
        cfg.SCREEN_WIDTH = w
        cfg.SCREEN_HEIGHT = h
        self.screen = pygame.display.set_mode((w, h), pygame.SCALED, vsync=0)
        self.global_settings["res_w"] = w
        self.global_settings["res_h"] = h
        self.storage.save_global_settings(self.global_settings)
        
        from src.states.editor import EditorState
        from src.states.game import GameState
        from src.states.settings import SettingsState
        from src.states.stats import StatsState
        from src.states.workshop import WorkshopState
        from src.states.credits import CreditsState
        from src.states.links import LinksState
        
        self.state_dict = {
            'EDITOR': EditorState(self),
            'GAME': GameState(self),
            'SETTINGS': SettingsState(self),
            'STATS': StatsState(self),
            'WORKSHOP': WorkshopState(self),
            'CREDITS': CreditsState(self),
            'LINKS': LinksState(self)
        }
        
        self.state = self.state_dict['SETTINGS']
        self.state.startup({})


    def run(self):
        if not hasattr(self, 'state'):
            self.state = self.state_dict[self.state_name]
            
        self.state.startup({}) 
        while True:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
    
            self.state.handle_event(event)

    def update(self, dt):
        if self.state.quit: self.quit()
        if self.state.done: self.flip_state()
        self.state.update(dt)

    def draw(self):
        self.state.draw(self.screen)
        # --- FPS COUNTER ---
        if self.global_settings.get("show_fps", False):
            fps = int(self.clock.get_fps())
            fps_col = (0, 255, 0) if fps > 140 else (255, 255, 0)
            fps_surf = self.debug_font.render(f"FPS: {fps}", True, fps_col)
            # Draw with a small black background for visibility
            bg_rect = fps_surf.get_rect(topleft=(5, 5))
            pygame.draw.rect(self.screen, (0,0,0), bg_rect.inflate(4, 4))
            self.screen.blit(fps_surf, (5, 5))
        # -------------------
        pygame.display.flip()

    def flip_state(self):
        previous, next_state_name = self.state_name, self.state.next_state
        data = self.state.cleanup()
        self.state.done = False
        self.state_name = next_state_name
        self.state = self.state_dict[self.state_name]
        self.state.startup(data)

    def quit(self):
        if self.state_name == "EDITOR" and hasattr(self.state, "browser"):
            self.global_settings["last_active_tab"] = self.state.browser.active_tab
            
        # 2. Save to disk
        self.storage.save_global_settings(self.global_settings)
        pygame.quit(); sys.exit()