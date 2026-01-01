import pygame
from src.states.base import BaseState
import src.core.config as cfg
from src.core.config import *
from src.ui.elements import Button

class StatsState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 40)
        self.btn_back = Button(20, 20, 100, 30, "< BACK", "BACK")

    def handle_event(self, event):
        if self.btn_back.handle_event(event) == "BACK":
            self.next_state = "EDITOR"
            self.done = True

    def draw(self, screen):
        screen.fill(STATS_BG_COLOR)
        self.btn_back.draw(screen, self.font)
        
        # Title
        t = self.font_big.render("HISTORY", True, UI_COLOR)
        screen.blit(t, (cfg.SCREEN_WIDTH//2 - t.get_width()//2, 40))
        
        # Header Line
        pygame.draw.line(screen, ACCENT_COLOR, (100, 90), (cfg.SCREEN_WIDTH-100, 90))
        
        # Load Stats
        history = self.app.storage.load_stats()
        y = 120
        
        if not history:
            msg = self.font.render("No runs recorded yet.", True, TEXT_GRAY)
            screen.blit(msg, (cfg.SCREEN_WIDTH//2 - msg.get_width()//2, 150))
            return

        # Draw Table
        # We limit to 20 entries for now to avoid scrolling complexity
        for i, row in enumerate(history[:20]):
            c = UI_COLOR
            
            score = row.get('score', 0)
            if score >= 90: c = COLOR_PERFECT
            
            date_str = row.get('date', '')
            # Strip seconds/year if too long
            date_str = date_str[5:] # Remove YYYY-
            
            conf = row.get('config', 'Legacy')
            tgt = str(row.get('target', '???'))
            
            # Formatting
            txt_str = f"{date_str:<12} | {conf:<20} | {tgt:<12} | {score:.2f}%"
            
            surf = self.font.render(txt_str, True, c)
            # Center it
            screen.blit(surf, (cfg.SCREEN_WIDTH//2 - surf.get_width()//2, y))
            y += 30