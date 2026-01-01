import pygame
import threading
import urllib.request
import json
import src.core.config as cfg
from src.core.config import *
from src.states.base import BaseState
from src.ui.elements import Button, LinkButton

class LinksState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 50)
        
        self.btn_back = Button(20, 20, 100, 30, "< BACK", "BACK")
        
        # Default Fallback (Hardcoded in case internet fails)
        self.links_data = [
            {"text": "TSK Discord Server", "url": "https://discord.gg/CeyHwgnSH7"}
        ]
        
        self.link_buttons = []
        self.rebuild_buttons()
        
        # Start fetching immediately
        self.fetch_links()

    def fetch_links(self):
        def _run():
            try:
                with urllib.request.urlopen(cfg.LINKS_URL, timeout=3) as url:
                    # Expecting JSON: [{"text": "Title", "url": "http..."}, ...]
                    data = json.loads(url.read().decode())
                    if isinstance(data, list) and len(data) > 0:
                        self.links_data = data
                        self.rebuild_buttons()
            except Exception as e:
                print(f"Links Fetch Error: {e}")

        t = threading.Thread(target=_run)
        t.daemon = True
        t.start()

    def rebuild_buttons(self):
        """Creates LinkButton objects based on current data"""
        self.link_buttons = []
        cx = cfg.SCREEN_WIDTH // 2
        start_y = 150
        gap = 60
        
        for i, item in enumerate(self.links_data):
            txt = item.get("text", "Link")
            url = item.get("url", "")
            
            # Create button (X is 0 for now, we center it below)
            # Using a larger font (30) for importance
            btn = LinkButton(0, start_y + (i * gap), txt, url, font_size=30, color=ACCENT_COLOR)
            
            # Center it
            btn.rect.x = cx - btn.surf.get_width() // 2
            
            self.link_buttons.append(btn)

    def handle_event(self, event):
        if self.btn_back.handle_event(event) == "BACK":
            self.next_state = "EDITOR"
            self.done = True
        
        for btn in self.link_buttons:
            btn.handle_event(event)

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.btn_back.draw(screen, self.font)
        
        # Title
        t = self.font_big.render("COMMUNITY & LINKS", True, UI_COLOR)
        screen.blit(t, (cfg.SCREEN_WIDTH//2 - t.get_width()//2, 50))
        
        # Divider
        pygame.draw.line(screen, (50, 50, 50), (100, 110), (cfg.SCREEN_WIDTH-100, 110))
        
        # Buttons
        for btn in self.link_buttons:
            btn.draw(screen)