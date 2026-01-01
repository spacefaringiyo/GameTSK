import pygame
import math
from datetime import datetime
from src.states.base import BaseState
import src.core.config as cfg
from src.core.config import *
from src.engine.physics import Engine
from src.engine.scenario import Scenario
from src.vfx.particles import ParticleSystem # <--- Import

class GameState(BaseState):
    def __init__(self, app):
        super().__init__(app)
        self.font = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 20)
        self.font_big = pygame.font.SysFont(["segoe ui symbol", "arial", "sans-serif"], 60)
        self.engine = Engine()
        
        # --- PARTICLE SYSTEM SETUP ---
        # OPTIONS: "POPPER", "STARS", "FOUNTAIN"
        self.vfx_mode = "STARS" 
        self.particles = ParticleSystem(self.vfx_mode)
        # ----------------------------------
        
        self.graph_surf = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.reset_state_vars()

    def reset_state_vars(self):
        self.timer = 0.0
        self.score = 0.0
        self.time_in_zone = 0.0
        self.run_finished = False
        self.is_pb = False
        self.cached_pb = 0.0
        # Clear particles when restarting run
        self.particles.particles = []

    def startup(self, persistent):
        self.reset_state_vars()
        self.mode = persistent.get("mode", "WARMUP")
        self.config = persistent.get("config", {}).copy()
        
        self.display_name = persistent.get("name", "Unknown")
        self.origin = persistent.get("origin", "IMPORT")
        
        self.title_color = UI_COLOR
        if self.origin == "OFFICIAL": self.icon = "🌐"
        elif self.origin == "COMMUNITY": self.icon = "👥"
        elif self.origin == "LOCAL": self.icon = "🛠️"
        else: self.icon = "📄"


        self.scenario = Scenario.from_config(self.config)
        self.duration = self.scenario.duration
        self.engine.smoothing_window = self.config.get("smoothing", 75)
        
        self.engine.reset_graph()
        self.engine.reset_history()
        
        if self.mode == "CHALLENGE":
            self.timer = -float(self.config.get("warmup_time", 0))
        
        pygame.event.set_grab(True); pygame.mouse.set_visible(False); pygame.mouse.get_rel()
        
        if self.graph_surf.get_size() != (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT):
            self.graph_surf = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), pygame.SRCALPHA)

    def cleanup(self):
        pygame.event.set_grab(False)
        pygame.mouse.set_visible(True)
        self.app.audio.stop_all()
        return {}

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.next_state = "EDITOR"
                self.done = True
            
            if event.key == pygame.K_z:
                self.startup({
                    "mode": self.mode, 
                    "config": self.config,
                    "name": self.display_name,
                    "origin": self.origin
                })

        if pygame.mouse.get_focused():
            if not pygame.event.get_grab():
                pygame.event.set_grab(True)
                pygame.mouse.set_visible(False)

    def update(self, dt):
        if dt > 0.1: dt = 0.1
        if dt < 0.001: dt = 0.001

        dx, dy = pygame.mouse.get_rel()
        multiplier = self.app.global_settings.get("sensitivity", 100) / 100.0
        dx *= multiplier
        dy *= multiplier

        # --- UPDATE PARTICLES ---
        # Update them every frame, regardless of game state
        self.particles.update(dt, cfg.SCREEN_HEIGHT)
        
        # If it's the FOUNTAIN style, we keep emitting while on the result screen!
        if self.run_finished and self.is_pb and self.vfx_mode == "FOUNTAIN":
            self.particles.emit(cfg.SCREEN_WIDTH//2, cfg.SCREEN_HEIGHT + 10, count=5)
        # ------------------------

        if self.mode == "CHALLENGE" and not self.run_finished:
            self.timer += dt
            if self.timer >= self.duration:
                self.finish_challenge()
                return

        sim_time = max(0.0, self.timer)
        target_speed, target_tol, target_dirs = self.scenario.get_state_at(sim_time)
        speed, status, diff = self.engine.process_frame(dx, dy, dt, target_speed, target_tol, target_dirs)
        
        if self.mode == "WARMUP" or (self.mode == "CHALLENGE" and self.timer >= 0 and not self.run_finished):
             self.app.audio.update(dt, status)
             if status == "PERFECT":
                 if self.mode == "WARMUP": self.time_in_zone += dt
                 else: self.time_in_zone += dt
        else:
             self.app.audio.stop_all()

        color = COLOR_ZONE_LINE
        if status == "LOW": color = COLOR_SLOW
        elif status == "HIGH": color = COLOR_FAST
        elif status == "PERFECT": color = COLOR_PERFECT
        
        self.engine.record_graph_point(dt, speed, color, target_speed, target_tol)

    def finish_challenge(self):
        self.run_finished = True
        self.app.audio.stop_all()
        self.timer = self.duration
        if self.duration > 0:
            self.score = (self.time_in_zone / self.duration) * 100
            if self.score > 100.0: self.score = 100.0
                
        from src.core.utils import generate_hash
        curr_hash = generate_hash(self.config)
        previous_best = self.app.storage.get_high_score(curr_hash)
        
        if self.score > previous_best and self.score > 0:
            self.is_pb = True; self.cached_pb = self.score
            
            # --- TRIGGER PARTICLES (ONE SHOT) ---
            if self.vfx_mode == "POPPER":
                self.particles.emit(cfg.SCREEN_WIDTH//2, cfg.SCREEN_HEIGHT//2, count=100)
            elif self.vfx_mode == "STARS":
                self.particles.emit(cfg.SCREEN_WIDTH//2, cfg.SCREEN_HEIGHT//2 + 100, count=100)
            # Fountain is handled in update() because it's continuous
            # ------------------------------------
            
        else:
            self.is_pb = False; self.cached_pb = previous_best
            
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "config": f"{self.icon} {self.display_name}",
            "target": f"{int(self.scenario.keyframes[0].speed)}->{int(self.scenario.keyframes[-1].speed)}",
            "score": round(self.score, 2),
            "hash": curr_hash
        }
        self.app.storage.save_run(entry)

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.draw_graph_view(screen)
        self.draw_hud(screen)
        
        # --- DRAW PARTICLES ON TOP ---
        self.particles.draw(screen)

    def draw_graph_view(self, screen):
        # ... (This method stays exactly as optimized before, no changes needed) ...
        rect = pygame.Rect(0, 0, cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT - 100)
        scale = self.config.get("zoom_scale", 3) * 0.2
        cx = cfg.SCREEN_WIDTH // 2 
        self.graph_surf.fill((0, 0, 0, 0))
        
        points = self.engine.graph_points
        if len(points) > 1:
            upper_past, lower_past, line_pts = [], [], []
            start_index = max(0, len(points) - cx)
            visible_points = list(points)[start_index:]
            offset = len(visible_points) - 1
            for i, (spd, col, tgt, h_tol) in enumerate(visible_points):
                x = cx - (offset - i)
                yu = rect.bottom - ((tgt + h_tol) * scale)
                yl = rect.bottom - ((tgt - h_tol) * scale)
                ys = rect.bottom - (spd * scale)
                upper_past.append((x, max(0, yu))); lower_past.append((x, max(0, yl)))
                line_pts.append((x, max(0, ys), col))
            if len(upper_past) > 1:
                poly = upper_past + lower_past[::-1]
                pygame.draw.polygon(self.graph_surf, (255, 255, 255, 30), poly)
                pygame.draw.lines(screen, COLOR_ZONE_LINE, False, upper_past, 1)
                pygame.draw.lines(screen, COLOR_ZONE_LINE, False, lower_past, 1)
            for i in range(len(line_pts)-1):
                p1, p2 = line_pts[i], line_pts[i+1]
                pygame.draw.line(screen, p2[2], (p1[0], p1[1]), (p2[0], p2[1]), 2)

        future_pixels = cfg.SCREEN_WIDTH - cx
        upper_fut, lower_fut = [], []
        dt_per_px = 1.0 / self.engine.REFERENCE_FPS 
        for i in range(future_pixels):
            x, pixel_time = cx + i, self.timer + (i * dt_per_px)
            tgt, f_tol, _ = self.scenario.get_state_at(pixel_time)
            yu = rect.bottom - ((tgt + f_tol) * scale); yl = rect.bottom - ((tgt - f_tol) * scale)
            upper_fut.append((x, max(0, yu))); lower_fut.append((x, max(0, yl)))
        if len(upper_fut) > 1:
            poly = upper_fut + lower_fut[::-1]
            pygame.draw.polygon(self.graph_surf, (255, 255, 255, 30), poly)
            pygame.draw.lines(screen, (60, 60, 60), False, upper_fut, 1)
            pygame.draw.lines(screen, (60, 60, 60), False, lower_fut, 1)
        
        screen.blit(self.graph_surf, (0,0))
        pygame.draw.line(screen, (100, 100, 100), (cx, 0), (cx, rect.bottom), 1)

    def draw_hud(self, screen):
        cx = cfg.SCREEN_WIDTH // 2
        
        def draw_txt(txt, y, col=UI_COLOR, font=self.font):
            s = font.render(str(txt), True, col)
            screen.blit(s, (cx - s.get_width()//2, y))

        if self.mode == "WARMUP":
            draw_txt(f"{self.icon} {self.display_name}", 20, self.title_color)
            draw_txt("[ESC] Hub", cfg.SCREEN_HEIGHT - 100, ACCENT_COLOR)
        
        elif self.mode == "CHALLENGE":
            if self.run_finished:
                overlay = pygame.Surface((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)); overlay.set_alpha(200); overlay.fill((0,0,0))
                screen.blit(overlay, (0,0))
                
                draw_txt(f"{self.icon} {self.display_name}", 50, self.title_color)
                if self.is_pb:
                    alpha = abs(math.sin(pygame.time.get_ticks() / 300)) * 255
                    pb_surf = self.font_big.render("NEW PERSONAL BEST!", True, (255, 215, 0))
                    pb_surf.set_alpha(int(alpha))
                    screen.blit(pb_surf, (cx - pb_surf.get_width()//2, cfg.SCREEN_HEIGHT//2 - 150))
                elif self.cached_pb > 0:
                    draw_txt(f"PB: {self.cached_pb:.2f}%", cfg.SCREEN_HEIGHT//2 - 120, TEXT_GRAY)
                
                draw_txt(f"{self.score:.2f}%", cfg.SCREEN_HEIGHT//2 - 40, COLOR_PERFECT, self.font_big)
                draw_txt("[Z] Retry   [ESC] Hub", cfg.SCREEN_HEIGHT//2 + 110, ACCENT_COLOR)
            else:
                draw_txt(f"{self.icon} {self.display_name}", 30, self.title_color)
                if self.timer < 0:
                    draw_txt(f"{abs(self.timer):.1f}", 360, COLOR_REC, self.font_big)
                else:
                    rem = max(0, self.duration - self.timer)
                    draw_txt(f"{rem:.1f}", 70, UI_COLOR, self.font_big)