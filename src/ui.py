import pygame
from .config import *

# --- 1. Basic Widgets ---

class Toggle:
    def __init__(self, x, y, w, h, text, state=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = state
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        
        # FIX: Check collision directly on click, don't rely on cached hover state
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                return True 
        return False

    def draw(self, screen, font):
        color = (0, 200, 100) if self.active else (60, 60, 60)
        pygame.draw.rect(screen, color, self.rect)
        border_c = (255, 255, 255) if self.hover else (20, 20, 20)
        pygame.draw.rect(screen, border_c, self.rect, 2)
        txt = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

class Button:
    def __init__(self, x, y, w, h, text, action, color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action
        self.base_color = color if color else (50, 50, 60)
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover:
                return self.action
        return None

    def draw(self, screen, font):
        c = (min(255, self.base_color[0]+30), min(255, self.base_color[1]+30), min(255, self.base_color[2]+30)) if self.hover else self.base_color
        pygame.draw.rect(screen, c, self.rect)
        pygame.draw.rect(screen, UI_COLOR, self.rect, 1)
        txt = font.render(self.text, True, UI_COLOR)
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

class TextInput:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = False
        self.color_inactive = (100, 100, 100)
        self.color_active = ACCENT_COLOR

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "SUBMIT"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Limit length
                if len(self.text) < 20 and event.unicode.isprintable():
                    self.text += event.unicode
        return None

    def draw(self, screen, font):
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, (10, 10, 10), self.rect)
        pygame.draw.rect(screen, color, self.rect, 2)
        surf = font.render(self.text, True, UI_COLOR)
        
        # Clip text if too long
        if surf.get_width() > self.rect.width - 5:
            # Simple crude clipping
            self.text = self.text[:-1]
            surf = font.render(self.text, True, UI_COLOR)
            
        screen.blit(surf, (self.rect.x + 5, self.rect.y + 5))

# --- 2. Advanced Widgets ---

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label):
        # We split the requested Width (w)
        # 70% Track, 30% Box (fixed width approx 60px)
        box_w = 60
        track_w = w - box_w - 10
        
        self.rect = pygame.Rect(x, y, track_w, h) # Track Rect
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.dragging = False
        self.handle_w = 12
        
        # Internal Value Box
        # Positioned to the right of the track
        self.val_box = TextInput(x + track_w + 10, y - 10, box_w, 30, str(start_val))

    def handle_event(self, event):
        changed = False
        
        # 1. Handle Text Box Input
        res = self.val_box.handle_event(event)
        if self.val_box.active:
            # Attempt to parse int
            try:
                # Allow empty while typing
                if self.val_box.text == "": 
                    pass 
                else:
                    new_val = int(self.val_box.text)
                    # Clamp
                    new_val = max(self.min_val, min(self.max_val, new_val))
                    if new_val != self.val:
                        self.val = new_val
                        changed = True
            except ValueError:
                pass # Ignore non-digits
        
        # 2. Handle Slider Drag
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.inflate(10, 10).collidepoint(event.pos):
                self.dragging = True
                self.update_from_mouse(event.pos[0])
                self.val_box.active = False # Unfocus box if dragging
                changed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            # Sync text box on release (cleanup)
            self.val_box.text = str(self.val)
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_from_mouse(event.pos[0])
                changed = True
                return True
        
        return changed

    def update_from_mouse(self, mx):
        x = max(self.rect.x, min(mx, self.rect.x + self.rect.width))
        ratio = (x - self.rect.x) / self.rect.width
        self.val = int(self.min_val + (ratio * (self.max_val - self.min_val)))
        # Sync Text Box
        self.val_box.text = str(self.val)

    def draw(self, screen, font):
        # Label
        label_surf = font.render(f"{self.label}", True, UI_COLOR)
        screen.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        # Track
        pygame.draw.rect(screen, (60, 60, 60), self.rect)
        
        # Handle
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        hx = self.rect.x + (ratio * (self.rect.width - self.handle_w))
        handle_rect = pygame.Rect(hx, self.rect.y - 5, self.handle_w, self.rect.height + 10)
        pygame.draw.rect(screen, ACCENT_COLOR, handle_rect)
        
        # Draw Box
        self.val_box.draw(screen, font)

    def set_val(self, v):
        self.val = max(self.min_val, min(self.max_val, int(v)))
        self.val_box.text = str(self.val)

class ConfigBrowser:
    def __init__(self, x, y, w, h, storage):
        self.rect = pygame.Rect(x, y, w, h)
        self.storage = storage
        self.configs = []
        self.selected_index = -1
        self.refresh()

    def refresh(self):
        self.configs = self.storage.list_configs()
        if self.configs and self.selected_index == -1:
            self.selected_index = 0

    def get_selected(self):
        if 0 <= self.selected_index < len(self.configs):
            return self.configs[self.selected_index]
        return None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                ly = event.pos[1] - self.rect.y - 30 
                idx = ly // 25
                if 0 <= idx < len(self.configs):
                    self.selected_index = idx
                    return "SELECTED"
        return None

    def draw(self, screen, font):
        pygame.draw.rect(screen, (25, 25, 30), self.rect)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 2)
        head = font.render("AVAILABLE CONFIGS", True, ACCENT_COLOR)
        screen.blit(head, (self.rect.x + 10, self.rect.y + 5))
        pygame.draw.line(screen, (50,50,50), (self.rect.x, self.rect.y+30), (self.rect.right, self.rect.y+30))
        y = self.rect.y + 35
        for i, name in enumerate(self.configs):
            color = UI_COLOR
            if i == self.selected_index:
                color = ACCENT_COLOR
                pygame.draw.rect(screen, (40, 40, 50), (self.rect.x+2, y, self.rect.width-4, 24))
            txt = font.render(name, True, color)
            # Clip name
            if txt.get_width() > self.rect.width - 20:
                txt = font.render(name[:15]+"...", True, color)
            screen.blit(txt, (self.rect.x + 10, y))
            y += 25

class SaveAsModal:
    def __init__(self, screen_w, screen_h, default_text, font):
        self.w = 400
        self.h = 200
        self.x = (screen_w - self.w) // 2
        self.y = (screen_h - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.title = "Create Copy?"
        self.txt_input = TextInput(self.x + 50, self.y + 70, 300, 30, default_text)
        self.txt_input.active = True 
        self.btn_yes = Button(self.x + 50, self.y + 130, 100, 40, "YES", "YES", color=(40, 80, 40))
        self.btn_no = Button(self.x + 250, self.y + 130, 100, 40, "NO", "NO", color=(80, 40, 40))

    def handle_event(self, event):
        res = self.txt_input.handle_event(event)
        if res == "SUBMIT": return "YES" 
        if self.btn_yes.handle_event(event) == "YES": return "YES"
        if self.btn_no.handle_event(event) == "NO": return "NO"
        return None

    def get_text(self):
        return self.txt_input.text

    def draw(self, screen, font):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        pygame.draw.rect(screen, (40, 40, 45), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        title_surf = font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surf, (self.rect.centerx - title_surf.get_width()//2, self.y + 20))
        self.txt_input.draw(screen, font)
        self.btn_yes.draw(screen, font)
        self.btn_no.draw(screen, font)

class ConfirmationModal:
    def __init__(self, screen_w, screen_h, title, message, font):
        self.w = 400
        self.h = 200
        self.x = (screen_w - self.w) // 2
        self.y = (screen_h - self.h) // 2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        
        self.title = title
        self.message = message
        
        # Buttons
        self.btn_yes = Button(self.x + 50, self.y + 130, 100, 40, "YES", "YES", color=(80, 40, 40)) # Reddish for danger
        self.btn_no = Button(self.x + 250, self.y + 130, 100, 40, "NO", "NO", color=(40, 80, 40))

    def handle_event(self, event):
        if self.btn_yes.handle_event(event) == "YES": return "YES"
        if self.btn_no.handle_event(event) == "NO": return "NO"
        return None

    def draw(self, screen, font):
        # Dim background
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        
        # Draw Box
        pygame.draw.rect(screen, (40, 30, 30), self.rect) # Slightly red bg
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        
        # Title
        t_surf = font.render(self.title, True, (255, 50, 50))
        screen.blit(t_surf, (self.rect.centerx - t_surf.get_width()//2, self.y + 20))
        
        # Message
        m_surf = font.render(self.message, True, (200, 200, 200))
        screen.blit(m_surf, (self.rect.centerx - m_surf.get_width()//2, self.y + 70))
        
        self.btn_yes.draw(screen, font)
        self.btn_no.draw(screen, font)
