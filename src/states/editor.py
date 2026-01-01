import pygame
import src.core.config as cfg
from src.core.config import *
from src.states.base import BaseState
from src.ui.elements import Button, TabbedBrowser, Slider, NameModal, EditFavModal, PulseButton
from src.core.utils import encode_config, decode_config

class EditorState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 60)
        
        self.update_available = False
        self.update_url = ""

        # 1. State Data
        self.current_config = {}
        self.current_name = "Default"   # Track Name
        self.current_origin = "IMPORT"  # Track Origin (ONLINE, LOCAL, IMPORT)
        
        self.modal = None
        
        self.check_for_updates()
        # 2. Build UI
        self.init_ui()
        
        # 3. Load Initial Data
        if self.app.storage.data['recents']:
            # Load the most recent item
            first_recent = self.app.storage.data['recents'][0]

            saved_origin = first_recent.get("origin_tag")
            if not saved_origin:
                # Fallback for old legacy files
                saved_origin = "LOCAL" if self.app.storage.is_local(first_recent) else "IMPORT"


            self.load_config(first_recent, 
                             name=self.app.storage.get_display_name(first_recent),
                             origin=saved_origin) 
        else:
            self.reset_to_default()

    def init_ui(self):
        # --- BROWSER (Top Center) ---
        bx, by = (cfg.SCREEN_WIDTH - 800) // 2, 20
        start_tab = self.app.global_settings.get("last_active_tab", 0)
        self.browser = TabbedBrowser(bx, by, 800, 300, self.app.storage, start_tab=start_tab)
        
        # --- ACTION BUTTONS (Below Browser) ---
        btn_y = by + 310
        start_x = (cfg.SCREEN_WIDTH - 210) // 2
        self.btn_copy = Button(start_x, btn_y, 100, 30, "EXPORT", "COPY")
        self.btn_paste = Button(start_x + 110, btn_y, 100, 30, "IMPORT", "PASTE")

        # --- PLAY & EDIT BUTTONS (Lower Center) ---
        cx = cfg.SCREEN_WIDTH // 2
        # Move down to clear description text
        base_y = cfg.SCREEN_HEIGHT // 2 + 160 

        # 1. Play Buttons (Centered Block)
        # Total width 290px (140 + 140 + 10 gap)
        self.btn_warmup = Button(cx - 145, base_y, 140, 50, "WARMUP", "WARMUP", color=(50, 80, 50))
        self.btn_challenge = Button(cx + 5, base_y, 140, 50, "CHALLENGE", "CHALLENGE", color=(80, 60, 20))

        # 2. Edit Button (Offset to the Right)
        # Challenge ends at (cx + 145). We start Edit at (cx + 215).
        # That is a 70px safety gap.
        # Making it slightly narrower (100px) to differentiate it from Play buttons.
        self.btn_edit = Button(cx + 285, base_y, 100, 50, "EDIT", "EDIT", color=(60, 60, 80))

        # --- SENSITIVITY (Below Play Buttons) ---
        sens_y = base_y + 80
        curr_sens = self.app.global_settings.get("sensitivity", 100)
        self.sl_sens = Slider(cx - 150, sens_y, 300, 10, 10, 500, curr_sens, "Sensitivity (%)")

        # --- CORNER BUTTONS ---
        self.btn_stats = Button(20, 20, 100, 30, "STATS", "STATS")
        self.btn_settings = Button(20, 60, 100, 30, "SETTINGS", "SETTINGS", color=(80, 80, 100))
        
        self.btn_links = Button(20, cfg.SCREEN_HEIGHT - 90, 100, 30, "LINKS", "LINKS", color=(40, 80, 80))
        self.btn_credits = Button(20, cfg.SCREEN_HEIGHT - 50, 100, 30, "CREDITS", "CREDITS", color=(60, 60, 60))

        # UPDATE BUTTON
        self.btn_update = PulseButton(cfg.SCREEN_WIDTH - 300, 20, 280, 35, "UPDATE AVAILABLE! (b °▽°)b", "OPEN_UPDATE")

    def load_config(self, data, name=None, origin="IMPORT"):
        """
        Loads config and updates context (Name/Origin).
        If name is None, it attempts to find it in the data or generate it.
        """
        self.current_config = data.copy()
        self.current_origin = origin
        
        # Clean up name (remove old prefixes if they exist in the string)
        if name:
            clean = name.replace("★ ", "").replace("🌐 ", "").replace("🛠️ ", "").replace(" [MOD]", "")
            self.current_name = clean
        else:
            raw = self.app.storage.get_display_name(data)
            self.current_name = raw.replace("★ ", "").replace("🌐 ", "").replace("🛠️ ", "").replace(" [MOD]", "")

        self.browser.set_selection(self.current_config)


    def get_config(self):
        return self.current_config

    def reset_to_default(self):
        self.current_config = {
            "smoothing": 75, "zoom_scale": 2,
            "start_speed": 500, "end_speed": 500,
            "tolerance": 75, "duration": 10, "warmup_time": 0,
            "directions": [True, True, True, True]
        }
        self.current_name = "Default"
        self.current_origin = "IMPORT"

    def handle_event(self, event):
        # 1. MODAL HANDLING
        if self.modal:
            res = self.modal.handle_event(event)
            
        if self.update_available:
            if self.btn_update.handle_event(event) == "OPEN_UPDATE":
                import webbrowser
                webbrowser.open(self.update_url)

        if isinstance(self.modal, NameModal):
            if res == "OK":
                # Save to Local
                final_name = self.modal.get_text()
                # Inject name into data so it's self-contained
                data_to_save = self.get_config().copy()
                data_to_save["name"] = final_name
                
                self.app.storage.save_to_local(data_to_save, final_name)
                self.browser.refresh(); self.modal = None
                
                # Update current context to match the save
                self.load_config(data_to_save, name=final_name, origin="LOCAL")
                
            elif res == "CANCEL" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.modal = None
        elif isinstance(self.modal, EditFavModal):
            if res == "UPDATE":
                # Update Name in DB
                new_name = self.modal.get_text()
                data_to_save = self.get_config().copy()
                data_to_save["name"] = new_name
                
                self.app.storage.update_favorite_name(data_to_save, new_name)
                self.browser.refresh(); self.modal = None
                self.load_config(data_to_save, name=new_name, origin="LOCAL")
                
            elif res == "UNSTAR":
                self.app.storage.delete_local(self.get_config())
                self.browser.refresh(); self.modal = None
                # Revert to import/generic status
                self.current_origin = "IMPORT"
                
            elif res == "CANCEL" or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.modal = None

            return

        # 2. SENSITIVITY
        if self.sl_sens.handle_event(event):
            self.app.global_settings["sensitivity"] = self.sl_sens.val

        # 3. BROWSER INTERACTION
        res = self.browser.handle_event(event)
        if isinstance(res, dict):
            # Determine Origin based on Active Tab
            tab_name = self.browser.tabs[self.browser.active_tab]
            new_origin = "IMPORT" # Default
            if tab_name == "OFFICIAL": new_origin = "OFFICIAL"
            elif tab_name == "COMMUNITY": new_origin = "COMMUNITY"
            elif tab_name == "LOCAL": new_origin = "LOCAL"
            # RECENT keeps default IMPORT/Generic status unless we check DB, but IMPORT is safer

            # Unwrap Online/Custom items
            if "data" in res:
                payload = res["data"].copy()
                name_str = res.get("name", "Unknown")
                if "author" in res:
                    payload["author"] = res["author"]
                if "description" in res:
                    payload["description"] = res["description"]

                if tab_name == "RECENT" and "origin_tag" in payload:
                    new_origin = payload["origin_tag"]

                self.load_config(payload, name=name_str, origin=new_origin)
            else:
                self.load_config(res, origin=new_origin)

        # 4. ACTION BUTTONS
        if self.btn_copy.handle_event(event):
            # When exporting, we encode the current name too!
            export_data = self.get_config().copy()
            export_data["name"] = self.current_name
            code = encode_config(export_data)
            if code:
                pygame.scrap.init()
                pygame.scrap.put(pygame.SCRAP_TEXT, code.encode('utf-8'))
        
        if self.btn_paste.handle_event(event):
            pygame.scrap.init()
            content = pygame.scrap.get(pygame.SCRAP_TEXT)
            if content:
                data = decode_config(content.decode('utf-8').strip().strip('\x00'))
                if data: 
                    # Imported items are definitely IMPORT origin
                    # We check if the pasted data has a "name" field
                    loaded_name = data.get("name", None)
                    self.load_config(data, name=loaded_name, origin="IMPORT")
                    self.app.storage.add_imported(data)
                    self.browser.refresh()

        # 5. NAVIGATION / PLAY
        if self.btn_warmup.handle_event(event) == "WARMUP":
            self.start_run("WARMUP")

        if self.btn_challenge.handle_event(event) == "CHALLENGE":
            self.start_run("CHALLENGE")

        if self.btn_edit.handle_event(event) == "EDIT":
            self.next_state = "WORKSHOP"
            # PASS CONTEXT TO WORKSHOP
            self.persistent_data = {
                "config": self.get_config(),
                "name": self.current_name,
                "origin": self.current_origin
            }
            self.done = True

        if self.btn_stats.handle_event(event) == "STATS":
            self.next_state = "STATS"; self.done = True

        if self.btn_settings.handle_event(event) == "SETTINGS":
            self.next_state = "SETTINGS"; self.done = True

        if self.btn_links.handle_event(event) == "LINKS":
            self.next_state = "LINKS"; self.done = True

        if self.btn_credits.handle_event(event) == "CREDITS":
            self.next_state = "CREDITS"; self.done = True

    def start_run(self, mode):
        # Save Sens
        self.app.storage.save_global_settings(self.app.global_settings)
        
        # --- FIX: Inject Name into Config for Recents ---
        recents_data = self.get_config().copy()
        recents_data["name"] = self.current_name
        recents_data["origin_tag"] = self.current_origin
        self.app.storage.add_recent(recents_data)
        self.browser.refresh()
        
        # Switch State
        self.next_state = "GAME"
        # PASS CONTEXT TO GAME
        self.persistent_data = {
            "mode": mode, 
            "config": self.get_config(),
            "name": self.current_name,
            "origin": self.current_origin
        }
        self.done = True

    def draw(self, screen):
        screen.fill(BG_COLOR)
        
        # 1. UI Components
        self.browser.draw(screen, self.font)
        self.btn_copy.draw(screen, self.font)
        self.btn_paste.draw(screen, self.font)
        self.btn_warmup.draw(screen, self.font)
        self.btn_challenge.draw(screen, self.font)
        self.btn_edit.draw(screen, self.font)
        self.btn_stats.draw(screen, self.font)
        self.btn_settings.draw(screen, self.font)
        self.sl_sens.draw(screen, self.font)
        self.btn_credits.draw(screen, self.font)
        self.btn_links.draw(screen, self.font)
        
        # 2. Draw Title Info (Using Explicit Context)
        curr = self.get_config()
        author = curr.get("author", "")
        desc = curr.get("description", "")
        
        # Determine Icon based on Explicit Origin
        icon = "📄" 
        if self.current_origin == "OFFICIAL": icon = "🌐"
        elif self.current_origin == "COMMUNITY": icon = "👥" # People Icon
        elif self.current_origin == "LOCAL": icon = "🛠️"

        # 3. Draw Title (Y=400)
        display_str = f"{icon} {self.current_name}"
        txt = self.font_big.render(display_str, True, UI_COLOR)
        
        # Scale if too wide
        max_w = cfg.SCREEN_WIDTH - 40
        if txt.get_width() > max_w:
            ratio = max_w / txt.get_width()
            txt = pygame.transform.smoothscale(txt, (int(txt.get_width()*ratio), int(txt.get_height()*ratio)))
        screen.blit(txt, (cfg.SCREEN_WIDTH//2 - txt.get_width()//2, 400))

        # 4. Draw Author (Y=465)
        if author:
            auth_surf = self.font.render(f"by {author}", True, ACCENT_COLOR)
            screen.blit(auth_surf, (cfg.SCREEN_WIDTH//2 - auth_surf.get_width()//2, 465))

        # 5. Draw Description (Y=500)
        if desc:
            desc_surf = self.font.render(desc, True, TEXT_GRAY)
            screen.blit(desc_surf, (cfg.SCREEN_WIDTH//2 - desc_surf.get_width()//2, 500))
        
        # 6. Draw Modal Overlay
        if self.modal:
            self.modal.draw(screen, self.font)

        # 7. Update Check
        if self.update_available:
            self.btn_update.draw(screen, self.font)

    def check_for_updates(self):
        import urllib.request
        import threading
        
        def _fetch():
            try:
                with urllib.request.urlopen(cfg.VERSION_URL, timeout=3) as url:
                    content = url.read().decode().strip()
                    if content > cfg.GAME_VERSION:
                        self.update_available = True
                        self.update_url = "https://github.com/spacefaringiyo/GameTSK/releases"
            except Exception: pass

        t = threading.Thread(target=_fetch)
        t.daemon = True
        t.start()

    def startup(self, persistent):
        # 1. Check if Workshop sent us a new selection/save
        incoming_data = persistent.get("new_selection")
        if incoming_data:
            incoming_name = persistent.get("new_name")
            # If coming from Workshop save, it is now LOCAL
            self.load_config(incoming_data, name=incoming_name, origin="LOCAL")
            
            self.browser.refresh()
            try:
                # Switch to LOCAL tab to show the new save
                local_idx = self.browser.tabs.index("LOCAL")
                self.browser.active_tab = local_idx
                self.browser.refresh()
            except: pass