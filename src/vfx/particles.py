import pygame
import random
import math

# --- COLOR PALETTES ---
PALETTE_PASTEL = [
    (255, 105, 180), (255, 182, 193), (135, 206, 250), 
    (255, 255, 224), (255, 255, 255), (221, 160, 221)
]

PALETTE_GOLD = [
    (255, 215, 0), (255, 250, 205), (176, 224, 230), (255, 255, 255)
]

PALETTE_RAINBOW = [
    (255, 0, 0), (255, 165, 0), (255, 255, 0),
    (0, 128, 0), (0, 0, 255), (75, 0, 130), (238, 130, 238)
]

class Particle:
    def __init__(self, x, y, mode, overrides=None):
        self.x = x
        self.y = y
        self.mode = mode
        self.life = 1.0 
        
        # --- 1. DEFAULT SETTINGS ---
        # (These are overwritten immediately below)
        self.vx = 0
        self.vy = 0
        self.gravity = 0
        self.drag = 0.95
        self.size = 5
        self.color = (255, 255, 255)
        self.decay = 1.0
        self.rotation = 0
        self.spin_speed = 0
        self.bounce = False

        # --- 2. MODE DEFAULTS ---
        if mode == "POPPER":
            self.vx = random.uniform(-400, 400)
            self.vy = random.uniform(-400, 400)
            self.gravity = 800
            self.drag = 0.92
            self.color = random.choice(PALETTE_PASTEL)
            self.size = random.randint(6, 10)
            self.decay = random.uniform(0.3, 0.8)
            self.spin_speed = random.uniform(5, 15)

        elif mode == "STARS":
            self.gravity = -40            
            self.drag = 0.98              
            
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(10, 150)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed

            self.color = random.choice(PALETTE_GOLD)
            self.size = random.randint(4, 9)       
            self.decay = random.uniform(0.2, 0.6)  
            # ----------------------------
            
            self.spin_speed = 0

        elif mode == "FOUNTAIN":
            angle = random.uniform(math.radians(250), math.radians(290))
            speed = random.uniform(500, 900)
            self.vx = math.cos(angle) * speed
            self.vy = math.sin(angle) * speed
            self.gravity = 1200
            self.color = random.choice(PALETTE_RAINBOW)
            self.size = random.randint(3, 8)
            self.decay = random.uniform(0.4, 0.7)
            self.bounce = True

        # --- 3. APPLY OVERRIDES (FROM LAB) ---
        if overrides:
            # Physics
            if 'gravity' in overrides: self.gravity = overrides['gravity']
            if 'drag' in overrides: self.drag = overrides['drag']
            
            # Ranges (Randomness)
            if 'size_min' in overrides and 'size_max' in overrides:
                self.size = random.randint(overrides['size_min'], overrides['size_max'])
            
            if 'decay_min' in overrides and 'decay_max' in overrides:
                self.decay = random.uniform(overrides['decay_min'], overrides['decay_max'])
                
            if 'speed_min' in overrides and 'speed_max' in overrides:
                # Rescale velocity vector to new speed
                current_speed = math.sqrt(self.vx**2 + self.vy**2)
                if current_speed > 0:
                    new_speed = random.uniform(overrides['speed_min'], overrides['speed_max'])
                    ratio = new_speed / current_speed
                    self.vx *= ratio
                    self.vy *= ratio


    def update(self, dt, screen_h):
        self.life -= self.decay * dt
        
        self.vx *= self.drag
        self.vy *= self.drag
        self.vy += self.gravity * dt
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.spin_speed * dt * 10

        if self.bounce:
            if self.y > screen_h:
                self.y = screen_h
                self.vy *= -0.6
                self.vx *= 0.8

    def draw(self, surface):
        if self.life <= 0: return
        alpha = int(max(0, self.life) * 255)
        
        if self.mode == "POPPER":
            current_w = max(1, int(self.size * abs(math.sin(self.rotation))))
            s = pygame.Surface((current_w, self.size), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            surface.blit(s, (int(self.x - current_w/2), int(self.y - self.size/2)))
            
        elif self.mode == "STARS":
            twinkle = self.size + math.sin(pygame.time.get_ticks() * 0.01) * 2
            r = max(1, int(twinkle))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r, r), r//2)
            if alpha > 100:
                pygame.draw.line(s, (*self.color, alpha//2), (r, 0), (r, r*2), 2)
                pygame.draw.line(s, (*self.color, alpha//2), (0, r), (r*2, r), 2)
            surface.blit(s, (int(self.x - r), int(self.y - r)))

        else:
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            s.fill((*self.color, alpha))
            surface.blit(s, (int(self.x), int(self.y)))

class ParticleSystem:
    def __init__(self, mode="POPPER"):
        self.particles = []
        self.mode = mode
        self.overrides = {} # New: Stores active lab settings

    def set_mode(self, mode):
        if self.mode != mode:
            self.mode = mode
            self.particles = []
            
    def set_overrides(self, data):
        self.overrides = data

    def emit(self, x, y, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, self.mode, self.overrides))

    def update(self, dt, screen_h):
        for p in self.particles:
            p.update(dt, screen_h)
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)