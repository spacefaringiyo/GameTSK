import pygame
import src.core.config as cfg
from src.core.config import * 
import webbrowser
import math
from src.core.utils import generate_hash

# --- 1. Basic Widgets ---

class Toggle:
    def __init__(self, x, y, w, h, text, state=True):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.active = state # This is True/False for the setting
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                return True 
        return False

    def draw(self, screen, font):
        # Toggles use simple Green/Gray colors
        color = (0, 200, 100) if self.active else (60, 60, 60)
        pygame.draw.rect(screen, color, self.rect)
        
        # Draw border
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
        # FIX: Check for Button 1
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
        self.active = False   # This is True/False for keyboard focus
        self.selected = False # This is True/False for blue highlight
        self.color_inactive = (100, 100, 100)
        self.color_active = (0, 200, 255) # ACCENT_COLOR
        self.last_click_time = 0 
        self.max_chars = 50

    def handle_event(self, event):
        # 1. Mouse Logic
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
                now = pygame.time.get_ticks()
                # Double click check
                if now - self.last_click_time < 500: self.selected = True
                else: self.selected = False
                self.last_click_time = now
            else:
                self.active = False
                self.selected = False
        
        # 2. Keyboard Logic
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN: return "SUBMIT"
            
            # Select All
            if event.key == pygame.K_a and (event.mod & pygame.KMOD_CTRL):
                self.selected = True
                return None
            
            # Typing Logic
            if self.selected:
                if event.key in [pygame.K_BACKSPACE, pygame.K_DELETE]: self.text = ""
                elif event.unicode.isprintable(): self.text = event.unicode
                self.selected = False
                return None

            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                forbidden = '<>:"/\\|?*'
                if len(self.text) < self.max_chars and event.unicode.isprintable() and event.unicode not in forbidden:
                    self.text += event.unicode
        return None

    def draw(self, screen, font):
        # Determine border color based on focus
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(screen, (10, 10, 10), self.rect)
        pygame.draw.rect(screen, color, self.rect, 2)
        
        # Text rendering with Clipping window
        txt_surf = font.render(self.text, True, (255, 255, 255))
        
        if self.selected and self.text:
            # Highlight logic
            sel_w = min(txt_surf.get_width(), self.rect.width - 10)
            pygame.draw.rect(screen, (0, 100, 200), (self.rect.x + 5, self.rect.y + 5, sel_w, 20))

        if txt_surf.get_width() > self.rect.width - 10:
            width_to_show = self.rect.width - 10
            visible_area = pygame.Rect(txt_surf.get_width() - width_to_show, 0, width_to_show, txt_surf.get_height())
            txt_surf = txt_surf.subsurface(visible_area)

        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + 5))

# --- 2. Advanced Widgets ---

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label):
        box_w = 60
        track_w = w - box_w - 10
        self.rect = pygame.Rect(x, y, track_w, h) 
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.dragging = False
        self.handle_w = 12
        self.val_box = TextInput(x + track_w + 10, y - 10, box_w, 30, str(start_val))

    def handle_event(self, event):
        changed = False
        res = self.val_box.handle_event(event)
        if self.val_box.active:
            try:
                if self.val_box.text != "":
                    new_val = int(self.val_box.text)
                    new_val = max(self.min_val, min(self.max_val, new_val))
                    if new_val != self.val:
                        self.val = new_val
                        changed = True
            except ValueError: pass
        
        # FIX: Check for Button 1 for Drag
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.inflate(10, 10).collidepoint(event.pos):
                self.dragging = True
                self.update_from_mouse(event.pos[0])
                self.val_box.active = False 
                changed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Only release on left up
                self.dragging = False
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
        self.val_box.text = str(self.val)

    def draw(self, screen, font):
        label_surf = font.render(f"{self.label}", True, UI_COLOR)
        screen.blit(label_surf, (self.rect.x, self.rect.y - 35))
        pygame.draw.rect(screen, (60, 60, 60), self.rect)
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val) if self.max_val > self.min_val else 0
        hx = self.rect.x + (ratio * (self.rect.width - self.handle_w))
        handle_rect = pygame.Rect(hx, self.rect.y - 5, self.handle_w, self.rect.height + 10)
        pygame.draw.rect(screen, ACCENT_COLOR, handle_rect)
        self.val_box.draw(screen, font)

    def set_val(self, v):
        self.val = max(self.min_val, min(self.max_val, int(v)))
        self.val_box.text = str(self.val)

class TabbedBrowser:
    def __init__(self, x, y, w, h, storage, start_tab=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.storage = storage
        self.tabs = ["OFFICIAL", "COMMUNITY", "LOCAL", "RECENT", "IMPORT"]

        self.active_tab = max(0, min(3, start_tab))
        self.scroll_y = 0
        self.items = []
        self.selected_hash = None
        self.refresh()
    
    def set_selection(self, config_data):
        """External method to force highlight (e.g. on startup or paste)"""
        if config_data:
            self.selected_hash = generate_hash(config_data)

    def refresh(self):
        tab_key = self.tabs[self.active_tab]
        raw_list = []
        
        if tab_key == "RECENT":
            raw_list = self.storage.data['recents']
        elif tab_key == "IMPORT":
            raw_list = self.storage.data['imported']
        elif tab_key == "LOCAL": # Was FAV
            for v in self.storage.data['local_scenarios'].values():
                if isinstance(v, dict) and 'data' in v:
                    raw_list.append(v['data'])
            raw_list.reverse() # Show newest local first
        elif tab_key == "OFFICIAL":
            raw_list = self.storage.get_online_scenarios(cfg.SCENARIOS_OFFICIAL_URL)
        elif tab_key == "COMMUNITY":
            raw_list = self.storage.get_online_scenarios(cfg.SCENARIOS_COMMUNITY_URL)

        
        # --- NEW: PINNING SORT LOGIC ---
        # 1. Separate into Pinned and Unpinned
        pinned = []
        unpinned = []
        
        for item in raw_list:
            # Note: We need to handle the 'Online' wrapper correctly
            data_to_check = item["data"] if "data" in item else item
            
            if self.storage.is_starred(tab_key, data_to_check):
                pinned.append(item)
            else:
                unpinned.append(item)
        
        # 2. Combine them (Pinned always on top)
        self.items = pinned + unpinned
        # -------------------------------
        
        self.scroll_y = min(self.scroll_y, max(0, len(self.items)*25 - (self.rect.height - 40)))

    def handle_event(self, event):
        # 1. SCROLLING (Mouse Wheel)
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_y -= event.y * 20 # Speed
                
                # Clamp Scroll
                max_scroll = max(0, len(self.items) * 25 - (self.rect.height - 40))
                self.scroll_y = max(0, min(self.scroll_y, max_scroll))
                return None

        # 2. CLICKS (Left Click Only)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Tab Header
            if self.rect.x <= event.pos[0] <= self.rect.right and self.rect.y <= event.pos[1] <= self.rect.y + 30:
                tab_w = self.rect.width // len(self.tabs)
                clicked_idx = (event.pos[0] - self.rect.x) // tab_w
                if 0 <= clicked_idx < len(self.tabs):
                    self.active_tab = clicked_idx
                    self.scroll_y = 0 # Reset scroll on tab change
                    self.refresh()
                    return None
            
            # Check for List clicking
            list_rect = pygame.Rect(self.rect.x, self.rect.y + 40, self.rect.width, self.rect.height - 40)
            if list_rect.collidepoint(event.pos):
                ly = event.pos[1] - (self.rect.y + 40) + self.scroll_y
                if ly >= 0:
                    idx = int(ly // 25)
                    if 0 <= idx < len(self.items):
                        # --- NEW: Check if we clicked the STAR (left side) ---
                        # We define the star hitbox as the first 30 pixels of the row
                        if event.pos[0] < self.rect.x + 40:
                            data = self.items[idx]
                            # Unwrap online data if needed
                            data_to_star = data["data"] if "data" in data else data
                            
                            tab_key = self.tabs[self.active_tab]
                            self.storage.toggle_star(tab_key, data_to_star)
                            self.refresh()
                            return None # Stop here, don't "Select" the item
                        
                        # Selection Logic
                        item = self.items[idx]
                        data_to_hash = item["data"] if "data" in item else item
                        self.selected_hash = generate_hash(data_to_hash) # <--- Update highlight
                        return item
        return None

    def draw(self, screen, font):
        pygame.draw.rect(screen, (25, 25, 30), self.rect)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 2)
        
        # Draw Tabs
        tab_w = self.rect.width // len(self.tabs) 
        for i, t in enumerate(self.tabs):
            tx = self.rect.x + (i * tab_w)
            color = ACCENT_COLOR if i == self.active_tab else (60, 60, 60)
            pygame.draw.rect(screen, color, (tx, self.rect.y, tab_w, 30))
            pygame.draw.rect(screen, (20, 20, 20), (tx, self.rect.y, tab_w, 30), 1)
            lbl = font.render(t, True, UI_COLOR if i == self.active_tab else (150, 150, 150))
            screen.blit(lbl, (tx + tab_w//2 - lbl.get_width()//2, self.rect.y + 5))
            
        # Draw List with Clipping
        # Define the viewable area for the list
        view_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 35, self.rect.width - 4, self.rect.height - 37)
        screen.set_clip(view_rect)
        start_y = self.rect.y + 40 - self.scroll_y
        tab_key = self.tabs[self.active_tab]
        
        for i, cfg_item in enumerate(self.items):
            y = start_y + (i * 25)
            if y + 25 < view_rect.top or y > view_rect.bottom: continue
            
            # --- NEW: DRAW STAR ---
            data_to_check = cfg_item["data"] if "data" in cfg_item else cfg_item

            # --- HIGHLIGHT SELECTED ---
            if generate_hash(data_to_check) == self.selected_hash:
                # Draw a subtle blue-grey bar behind the text
                highlight_rect = pygame.Rect(self.rect.x + 2, y, self.rect.width - 4, 25)
                pygame.draw.rect(screen, (45, 55, 65), highlight_rect)
            # --------------------------

            is_pinned = self.storage.is_starred(tab_key, data_to_check)
            
            star_color = COLOR_PERFECT if is_pinned else (100, 100, 100)
            star_glyph = "★" if is_pinned else "☆"
            
            star_surf = font.render(star_glyph, True, star_color)
            screen.blit(star_surf, (self.rect.x + 10, y))
            # ----------------------

            # Draw Name (Offset to the right of the star)
            name = self.storage.get_display_name(cfg_item)
            name_surf = font.render(name, True, UI_COLOR)
            screen.blit(name_surf, (self.rect.x + 40, y))
            
        screen.set_clip(None)

class EditFavModal:
    def __init__(self, screen_w, screen_h, current_name, font):
        self.w, self.h = 400, 220
        self.x, self.y = (screen_w - self.w)//2, (screen_h - self.h)//2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.title = "Edit Favorite"
        self.txt_input = TextInput(self.x + 50, self.y + 60, 300, 30, current_name)
        self.txt_input.active = True
        self.btn_update = Button(self.x + 50, self.y + 120, 140, 40, "UPDATE NAME", "UPDATE", color=(40, 80, 40))
        self.btn_unstar = Button(self.x + 210, self.y + 120, 140, 40, "UNSTAR", "UNSTAR", color=(80, 40, 40))
        self.btn_cancel = Button(self.x + 50, self.y + 170, 300, 30, "CANCEL", "CANCEL", color=(60, 60, 60))

    def handle_event(self, event):
        self.txt_input.handle_event(event)
        if self.btn_update.handle_event(event) == "UPDATE": return "UPDATE"
        if self.btn_unstar.handle_event(event) == "UNSTAR": return "UNSTAR"
        if self.btn_cancel.handle_event(event) == "CANCEL": return "CANCEL"
        return None

    def get_text(self): return self.txt_input.text

    def draw(self, screen, font):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        pygame.draw.rect(screen, (40, 40, 45), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        t = font.render(self.title, True, (255, 255, 255))
        screen.blit(t, (self.rect.centerx - t.get_width()//2, self.y + 20))
        self.txt_input.draw(screen, font)
        self.btn_update.draw(screen, font)
        self.btn_unstar.draw(screen, font)
        self.btn_cancel.draw(screen, font)

class NameModal:
    def __init__(self, screen_w, screen_h, default_text, font):
        self.w, self.h = 400, 200
        self.x, self.y = (screen_w - self.w)//2, (screen_h - self.h)//2
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.txt_input = TextInput(self.x + 50, self.y + 70, 300, 30, default_text)
        self.txt_input.active = True 
        self.btn_ok = Button(self.x + 150, self.y + 130, 100, 40, "OK", "OK", color=(40, 80, 40))

    def handle_event(self, event):
        res = self.txt_input.handle_event(event)
        if res == "SUBMIT": return "OK"
        if self.btn_ok.handle_event(event) == "OK": return "OK"
        return None

    def get_text(self): return self.txt_input.text

    def draw(self, screen, font):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        pygame.draw.rect(screen, (40, 40, 45), self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        t = font.render("Name this Favorite:", True, UI_COLOR)
        screen.blit(t, (self.rect.centerx - t.get_width()//2, self.y + 20))
        self.txt_input.draw(screen, font)
        self.btn_ok.draw(screen, font)

# Clean up older classes we don't need or alias them if you want 
# (e.g. SaveAsModal, ConfirmationModal are technically dead now, but kept for safety)
class SaveAsModal: # Keeping dummy to prevent import errors in app.py if not updated fully
    def __init__(self, *args): pass
    def handle_event(self, e): return None
    def draw(self, s, f): pass
class ConfirmationModal:
    def __init__(self, *args): pass
    def handle_event(self, e): return None
    def draw(self, s, f): pass

class IconButton:
    def __init__(self, x, y, w, h, text, color=(80, 40, 40)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, screen, font):
        c = (min(255, self.color[0]+30), min(255, self.color[1]+30), min(255, self.color[2]+30)) if self.hover else self.color
        pygame.draw.rect(screen, c, self.rect)
        txt = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

class LinkButton:
        def __init__(self, x, y, text, url, font_size=20, color=(0, 200, 255)):
            self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], font_size)
            self.text = text
            self.url = url
            self.color = color
            self.surf = self.font.render(self.text, True, self.color)
            self.rect = pygame.Rect(x, y, self.surf.get_width(), self.surf.get_height())
            self.hover = False

        def handle_event(self, event):
            if event.type == pygame.MOUSEMOTION:
                self.hover = self.rect.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hover:
                    webbrowser.open(self.url)

        def draw(self, screen):
            # Draw underline if hovering
            screen.blit(self.surf, self.rect)
            if self.hover:
                pygame.draw.line(screen, self.color, (self.rect.left, self.rect.bottom), (self.rect.right, self.rect.bottom), 2)

class PulseButton(Button):
    def __init__(self, x, y, w, h, text, action):
        super().__init__(x, y, w, h, text, action)
        # Cute Pink Theme
        self.base_color = (255, 105, 180) # Hot Pink
        self.hover_color = (255, 150, 200) # Pastel Pink
        
    def draw(self, screen, font):
        # 1. Calculate Pulse (Heartbeat effect)
        # Slower speed (divide by 300), bouncing between 0 and 1
        t = pygame.time.get_ticks() / 300.0
        scale = (math.sin(t) + 1) / 2 # 0.0 to 1.0
        
        # 2. Draw Background
        c = self.hover_color if self.hover else self.base_color
        # border_radius=10 makes it round and soft!
        pygame.draw.rect(screen, c, self.rect, border_radius=10)
        
        # 3. Draw Pulsing Border
        # The alpha/color shifts slightly with the pulse
        border_c = (255, 200 + int(55*scale), 220)
        pygame.draw.rect(screen, border_c, self.rect, 3, border_radius=10)
        
        # 4. Text
        txt = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))