import pygame
import src.core.config as cfg
from src.core.config import *
from src.states.base import BaseState
from src.ui.elements import Slider, Button, Toggle, NameModal, TextInput, IconButton
from src.core.utils import generate_hash
import uuid # For Save As salt

class WorkshopState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 35)
        self.font_vbig = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 60)
        
        self.db_source_config = {}
        self.original_name = "Default"
        self.original_origin = "IMPORT"
        
        self.edit_mode = "SIMPLE" 
        self.timeline_rows = []
        
        # --- SCROLLING SETUP ---
        self.timeline_scroll_y = 0
        # Define the window: Left=40, Top=290, Width=300, Height=450 (fits on 900h screen)
        self.timeline_view_rect = pygame.Rect(40, 290, 300, 450)
        # -----------------------

        self.modal = None
        self.init_ui()

    def init_ui(self):
        # 1. Top Buttons
        self.btn_back = Button(20, 20, 120, 40, "< HUB", "BACK", color=(80, 40, 40))
        self.btn_save = Button(cfg.SCREEN_WIDTH - 260, 20, 100, 40, "SAVE", "SAVE", color=(40, 80, 40))
        self.btn_save_as = Button(cfg.SCREEN_WIDTH - 140, 20, 120, 40, "SAVE AS", "SAVE_AS", color=(40, 60, 80))

        # 2. Mode Toggle (Center Top)
        self.btn_mode = Button(cfg.SCREEN_WIDTH//2 - 100, 130, 200, 35, "GO ADVANCED", "TOGGLE_MODE", color=(60, 60, 60))

        # 3. Physics Sliders (Left Column)
        x_left, base_y, gap = 50, 290, 70
        self.sl_start = Slider(x_left, base_y, 230, 10, 0, 2000, 500, "Start Speed")
        self.sl_end = Slider(x_left, base_y + gap, 230, 10, 0, 2000, 500, "End Speed")
        self.sl_tol = Slider(x_left, base_y + gap*2, 230, 10, 10, 500, 50, "Tolerance")
        
        # 4. Advanced: Add Row Button
        self.btn_add_row = Button(x_left, 190, 120, 30, "+ ADD ROW", "ADD_ROW", color=(40, 80, 40))

        # 5. Global Sliders (Right Column 1)
        x_right_a = 880
        self.sl_smooth = Slider(x_right_a, 290, 230, 10, 1, 100, 15, "Smoothing")
        self.sl_zoom = Slider(x_right_a, 290 + gap, 230, 10, 1, 20, 3, "Zoom Scale")
        self.sl_warmup_time = Slider(x_right_a, 290 + gap*3, 230, 10, 0, 5, 0, "Warmup Buffer (s)")
        self.sl_dur = Slider(x_right_a, 290 + gap*4, 230, 10, 1, 60, 15, "Total Duration")

        # 6. Directions (Right Column 2)
        dx, dy = 1350, 290
        self.tog_up = Toggle(dx, dy, 50, 35, "UP")
        self.tog_down = Toggle(dx, dy + 80, 50, 35, "DN")
        self.tog_left = Toggle(dx - 55, dy + 40, 50, 35, "L")
        self.tog_right = Toggle(dx + 55, dy + 40, 50, 35, "R")
        
        self.sliders = [self.sl_start, self.sl_end, self.sl_tol, self.sl_smooth, self.sl_zoom, self.sl_warmup_time, self.sl_dur]
        self.toggles = [self.tog_up, self.tog_down, self.tog_left, self.tog_right]

        # 7. Metadata Inputs
        my = dy + 180 
        self.txt_author = TextInput(dx - 55, my, 160, 30, "")
        self.txt_desc = TextInput(dx - 55, my + 50, 300, 30, "")
        
        self.meta_labels = [
            {"txt": "Author Name", "x": dx + 25, "y": my - 25},
            {"txt": "Scenario Description", "x": dx + 95, "y": my + 25}
        ]

    def startup(self, persistent):
        self.db_source_config = persistent.get("config", {}).copy()
        self.original_name = persistent.get("name", "Unknown")
        self.original_origin = persistent.get("origin", "IMPORT")
        
        self.apply_data_to_sliders(self.db_source_config)
        self.baseline_config = self.get_current_data()
        
        self.txt_author.text = self.db_source_config.get("author", "")
        self.txt_desc.text = self.db_source_config.get("description", "")
        
        if "timeline" in self.db_source_config:
            self.edit_mode = "ADVANCED"; self.btn_mode.text = "GO SIMPLE"
            self.sync_timeline_to_ui(self.db_source_config["timeline"])
        else:
            self.edit_mode = "SIMPLE"; self.btn_mode.text = "GO ADVANCED"
            self.timeline_rows = []

        self.modal = None
        self.timeline_scroll_y = 0 # Reset scroll on entry

    def apply_data_to_sliders(self, data):
        self.sl_start.set_val(data.get('start_speed', 500))
        self.sl_end.set_val(data.get('end_speed', 500))
        self.sl_tol.set_val(data.get('tolerance', 75))
        self.sl_smooth.set_val(data.get('smoothing', 75))
        self.sl_zoom.set_val(data.get('zoom_scale', 2))
        self.sl_dur.set_val(data.get('duration', 10))
        self.sl_warmup_time.set_val(data.get('warmup_time', 0))
        dirs = data.get('directions', [True, True, True, True])
        for i, t in enumerate(self.toggles): t.active = dirs[i]

    def sync_timeline_to_ui(self, timeline):
        self.timeline_rows = []
        for entry in timeline:
            self.add_row_to_ui(entry.get("time", 0), entry.get("speed", 500), entry.get("tolerance", 50))

    def add_row_to_ui(self, t, s, tol):
        # We don't calculate Y here anymore, we do it dynamically in draw/handle_event
        row_idx = len(self.timeline_rows)
        sx = 50 
        # Create widgets with dummy Y (0), we will update it every frame
        self.timeline_rows.append({
            "time": TextInput(sx, 0, 60, 30, str(t)),
            "speed": TextInput(sx + 70, 0, 90, 30, str(s)),
            "tol": TextInput(sx + 170, 0, 60, 30, str(tol)),
            "del": IconButton(sx + 240, 0, 30, 30, "X")
        })

    def update_row_positions(self):
        """Crucial: Move widgets to their visual position based on scroll"""
        base_y = self.timeline_view_rect.y
        for i, row in enumerate(self.timeline_rows):
            y = base_y + (i * 35) - self.timeline_scroll_y
            row["time"].rect.y = y
            row["speed"].rect.y = y
            row["tol"].rect.y = y
            row["del"].rect.y = y

    def get_current_data(self):
        data = self.db_source_config.copy()
        data.update({
            "smoothing": self.sl_smooth.val, "zoom_scale": self.sl_zoom.val,
            "warmup_time": self.sl_warmup_time.val, "duration": self.sl_dur.val,
            "directions": [t.active for t in self.toggles],
            "author": self.txt_author.text,
            "description": self.txt_desc.text,
            "name": self.original_name
        })
        
        if self.edit_mode == "SIMPLE":
            if "timeline" in data: del data["timeline"]
            data.update({"start_speed": self.sl_start.val, "end_speed": self.sl_end.val, "tolerance": self.sl_tol.val})
        else:
            new_tl = []
            for row in self.timeline_rows:
                try: new_tl.append({"time": float(row["time"].text), "speed": int(row["speed"].text), "tolerance": int(row["tol"].text)})
                except: continue
            new_tl.sort(key=lambda x: x["time"])
            data["timeline"] = new_tl
            if new_tl:
                data["start_speed"], data["end_speed"], data["tolerance"] = new_tl[0]["speed"], new_tl[-1]["speed"], new_tl[0]["tolerance"]
        
        return data

    def handle_event(self, event):
        if self.modal:
            res = self.modal.handle_event(event)
            if res == "OK":
                final_name = self.modal.get_text()
                new_data = self.get_current_data()
                new_data["name"] = final_name 
                new_data["variant_id"] = str(uuid.uuid4())[:8] # Salt
                self.app.storage.save_to_local(new_data, final_name)
                self.next_state = "EDITOR"
                self.persistent_data = {"new_selection": new_data, "new_name": final_name}
                self.done = True
            elif res == "CANCEL" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.modal = None
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = "EDITOR"; self.done = True; return

        if self.btn_mode.handle_event(event):
            if self.edit_mode == "SIMPLE":
                self.edit_mode = "ADVANCED"; self.btn_mode.text = "GO SIMPLE"
                self.sync_timeline_to_ui([{"time": 0.0, "speed": self.sl_start.val, "tolerance": self.sl_tol.val}, {"time": self.sl_dur.val, "speed": self.sl_end.val, "tolerance": self.sl_tol.val}])
            else:
                self.edit_mode = "SIMPLE"; self.btn_mode.text = "GO ADVANCED"

        for s in [self.sl_smooth, self.sl_zoom, self.sl_warmup_time, self.sl_dur]: s.handle_event(event)
        for t in self.toggles: t.handle_event(event)

        if self.edit_mode == "SIMPLE":
            for s in [self.sl_start, self.sl_end, self.sl_tol]: s.handle_event(event)
        else:
            if self.btn_add_row.handle_event(event):
                last_t = float(self.timeline_rows[-1]["time"].text) if self.timeline_rows else 0
                self.add_row_to_ui(last_t + 1, 500, 50)
            
            # --- SCROLLING LOGIC ---
            # Mouse Wheel inside Viewport
            if event.type == pygame.MOUSEWHEEL and self.timeline_view_rect.collidepoint(pygame.mouse.get_pos()):
                self.timeline_scroll_y -= event.y * 35 # Scroll 1 row per tick
                max_scroll = max(0, (len(self.timeline_rows) * 35) - self.timeline_view_rect.height)
                self.timeline_scroll_y = max(0, min(self.timeline_scroll_y, max_scroll))
            
            # Sync Rects BEFORE checking events
            self.update_row_positions()
            
            # Handle Row Events only if potentially visible
            # (We could optimize this but a simple loop is fine for <100 rows)
            for i, row in enumerate(self.timeline_rows):
                # Optimization: Check if roughly in view
                if self.timeline_view_rect.colliderect(row["time"].rect):
                    row["time"].handle_event(event); row["speed"].handle_event(event); row["tol"].handle_event(event)
                    if row["del"].handle_event(event):
                        self.timeline_rows.pop(i); break
        
        self.txt_author.handle_event(event)
        self.txt_desc.handle_event(event)

        if self.btn_back.handle_event(event): self.next_state = "EDITOR"; self.done = True
        if self.btn_save_as.handle_event(event): self.open_save_as()
        
        if self.btn_save.handle_event(event):
            if self.original_origin == "LOCAL":
                new_data = self.get_current_data()
                new_data["name"] = self.original_name
                self.app.storage.delete_local(self.db_source_config)
                self.app.storage.save_to_local(new_data, self.original_name)
                self.next_state = "EDITOR"
                self.persistent_data = {"new_selection": new_data, "new_name": self.original_name}
                self.done = True
            else:
                self.open_save_as()

    def is_dirty(self):
        return generate_hash(self.get_current_data()) != generate_hash(self.baseline_config)

    def open_save_as(self):
        default_name = f"{self.original_name} [MOD]"
        self.modal = NameModal(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT, default_name, self.font)

    def draw(self, screen):
        screen.fill(BG_COLOR)
        dirty = self.is_dirty()
        
        icon = "📄"
        if self.original_origin == "OFFICIAL": icon = "🌐" # Fixed check logic
        elif self.original_origin == "COMMUNITY": icon = "👥"
        elif self.original_origin == "LOCAL": icon = "🛠️"
        
        display_name = self.original_name + (" *" if dirty else "")
        title_color = (255, 140, 0) if dirty else UI_COLOR
        
        txt = self.font_vbig.render(f"{icon} {display_name}", True, title_color)
        max_w = cfg.SCREEN_WIDTH - 320
        if txt.get_width() > max_w:
            ratio = max_w / txt.get_width()
            txt = pygame.transform.smoothscale(txt, (int(txt.get_width()*ratio), int(txt.get_height()*ratio)))
        screen.blit(txt, (cfg.SCREEN_WIDTH//2 - txt.get_width()//2, 60))

        self.btn_back.draw(screen, self.font)
        self.btn_save.draw(screen, self.font)
        self.btn_save_as.draw(screen, self.font)
        self.btn_mode.draw(screen, self.font)

        hy = 220
        self.draw_txt(screen, "FEEL", hy, UI_COLOR, x=880+115, font=self.font_big)
        self.draw_txt(screen, "TIME", hy + 190, UI_COLOR, x=880+115, font=self.font_big)
        self.draw_txt(screen, "DIRECTIONS", hy, UI_COLOR, x=1350, font=self.font_big)
        
        for s in [self.sl_smooth, self.sl_zoom, self.sl_warmup_time, self.sl_dur]: s.draw(screen, self.font)
        for t in self.toggles: t.draw(screen, self.font)

        if self.edit_mode == "SIMPLE":
            self.draw_txt(screen, "PHYSICS (SIMPLE)", hy, UI_COLOR, x=175, font=self.font_big)
            for s in [self.sl_start, self.sl_end, self.sl_tol]: s.draw(screen, self.font)
        else:
            self.draw_txt(screen, "TIMELINE (ADVANCED)", hy, UI_COLOR, x=175, font=self.font_big)
            self.btn_add_row.draw(screen, self.font)
            screen.blit(self.font.render("TIME", True, TEXT_GRAY), (50, 265))
            screen.blit(self.font.render("SPEED", True, TEXT_GRAY), (120, 265))
            screen.blit(self.font.render("TOL", True, TEXT_GRAY), (220, 265))
            
            # --- SCROLLABLE TIMELINE RENDER ---
            # 1. Update positions
            self.update_row_positions()
            
            # 2. Set Clipping Rectangle (The "Window")
            screen.set_clip(self.timeline_view_rect)
            
            # 3. Draw Rows
            for row in self.timeline_rows:
                # Optimization: Only draw if inside view + margin
                if row["time"].rect.bottom > self.timeline_view_rect.top and row["time"].rect.top < self.timeline_view_rect.bottom:
                    row["time"].draw(screen, self.font)
                    row["speed"].draw(screen, self.font)
                    row["tol"].draw(screen, self.font)
                    row["del"].draw(screen, self.font)
            
            # 4. Unclip
            screen.set_clip(None)

            # --- NEW: VISUAL SCROLLBAR ---
            total_h = len(self.timeline_rows) * 35
            view_h = self.timeline_view_rect.height
            
            # Only draw if content overflows
            if total_h > view_h:
                bar_w = 6
                # Place it 5px to the right of the input fields
                bar_x = self.timeline_view_rect.right + 5
                bar_y = self.timeline_view_rect.y
                
                # 1. Draw Track (Background)
                pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, view_h), border_radius=3)
                
                # 2. Calculate Thumb Size (Proportional)
                # Minimum size of 30px so it doesn't vanish
                thumb_h = max(30, int(view_h * (view_h / total_h)))
                
                # 3. Calculate Thumb Position
                max_scroll = total_h - view_h
                max_thumb_travel = view_h - thumb_h
                
                if max_scroll > 0:
                    scroll_ratio = self.timeline_scroll_y / max_scroll
                    thumb_offset = int(scroll_ratio * max_thumb_travel)
                else:
                    thumb_offset = 0
                
                # 4. Draw Thumb (Foreground)
                pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y + thumb_offset, bar_w, thumb_h), border_radius=3)
            # -----------------------------
            
            # Optional: Draw border around the view rect to show limits
            # pygame.draw.rect(screen, (50, 50, 50), self.timeline_view_rect, 1)
            # ----------------------------------

        self.txt_author.draw(screen, self.font)
        self.txt_desc.draw(screen, self.font)
        for lbl in self.meta_labels:
            self.draw_txt(screen, lbl["txt"], lbl["y"], TEXT_GRAY, x=lbl["x"])

        if self.modal: self.modal.draw(screen, self.font)

    def draw_txt(self, screen, text, y, color, x=None, font=None):
        f = font if font else self.font
        surf = f.render(text, True, color)
        pos_x = x if x else cfg.SCREEN_WIDTH // 2
        screen.blit(surf, (pos_x - surf.get_width()//2, y))