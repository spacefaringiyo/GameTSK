import pygame
from src.states.base import BaseState
import src.core.config as cfg
from src.core.config import *
from src.ui.elements import Button, LinkButton

class CreditsState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 25)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 50)
        self.font_small = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        
        self.btn_back = Button(20, 20, 100, 30, "< BACK", "BACK")
        
        # --- LINKS ---
        self.link_iyo = LinkButton(0, 0, "iyo", "https://x.com/spacefaringiyo", font_size=25)
        self.link_gemini = LinkButton(0, 0, "Gemini", "https://aistudio.google.com", font_size=25)
        
        self.links = [self.link_iyo, self.link_gemini]
        
        # --- DYNAMIC TESTERS ---
        self.testers = ["Loading..."] 
        self.fetch_testers()

    def handle_event(self, event):
        if self.btn_back.handle_event(event) == "BACK":
            self.next_state = "EDITOR"; self.done = True
        
        for link in self.links:
            link.handle_event(event)

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.btn_back.draw(screen, self.font)
        
        cx = cfg.SCREEN_WIDTH // 2
        y_cursor = 100 
        
        # --- HEADER ---
        t = self.font_big.render("DEVELOPMENT TEAM", True, UI_COLOR)
        screen.blit(t, (cx - t.get_width()//2, y_cursor))
        y_cursor += 150 
        
        # --- SECTION: CORE TEAM ---
        self.draw_role_pair(screen, "Design Lead", self.link_iyo, y_cursor)
        y_cursor += 50
        self.draw_role_pair(screen, "Technical Lead & Design", self.link_gemini, y_cursor)
        y_cursor += 100 

        # --- SECTION: SPECIAL THANKS ---
        self.draw_section_header(screen, "EARLY BUILD TESTERS", y_cursor)
        y_cursor += 50
        # Use the dynamic list now
        self.draw_simple_list(screen, self.testers, y_cursor)
        
        # --- FOOTER ---
        msg = self.font.render("Thank you for playing TSK AimTrainer", True, (100, 100, 100))
        screen.blit(msg, (cx - msg.get_width()//2, cfg.SCREEN_HEIGHT - 80))

    # --- HELPER METHODS FOR CLEANER CODE ---

    def draw_role_pair(self, screen, role, link_obj, y):
        """Draws 'Role - Name' centered"""
        role_txt = f"{role} - "
        role_surf = self.font.render(role_txt, True, TEXT_GRAY)
        
        total_w = role_surf.get_width() + link_obj.surf.get_width()
        start_x = (cfg.SCREEN_WIDTH // 2) - (total_w // 2)
        
        screen.blit(role_surf, (start_x, y))
        
        # Update link position dynamically
        link_obj.rect.x = start_x + role_surf.get_width()
        link_obj.rect.y = y
        link_obj.draw(screen)

    def draw_section_header(self, screen, text, y):
        """Draws a centered section title"""
        surf = self.font.render(text, True, UI_COLOR)
        screen.blit(surf, (cfg.SCREEN_WIDTH // 2 - surf.get_width() // 2, y))

    def draw_simple_list(self, screen, names, start_y):
        """Draws a list of names vertically"""
        y = start_y
        for name in names:
            surf = self.font_small.render(name, True, TEXT_GRAY)
            screen.blit(surf, (cfg.SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 30

    def fetch_testers(self):
        import urllib.request
        import json
        import threading
        
        def _run():
            try:
                with urllib.request.urlopen(cfg.CREDITS_URL, timeout=3) as url:
                    raw_data = url.read().decode()
                    
                    # 1. Try JSON format ["A", "B"]
                    try:
                        data = json.loads(raw_data)
                    except json.JSONDecodeError:
                        # 2. Fallback to Text format "A, B, C"
                        data = [name.strip() for name in raw_data.split(',') if name.strip()]
                        
                    if isinstance(data, list) and data:
                        self.testers = data
            except Exception as e:
                print(f"Credits Error: {e}")
                self.testers = ["(Fetch Failed)"]

        t = threading.Thread(target=_run)
        t.daemon = True
        t.start()