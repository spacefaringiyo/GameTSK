import pygame
import math
import array

class AudioEngine:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(44100, -16, 1, 512)
        
        self.sample_rate = 44100
        
        # State
        self.hit_enabled = True
        self.miss_enabled = False
        self.hit_vol = 0.5
        self.miss_vol = 0.5
        self.hit_freq = 150 
        self.miss_freq = 100
        
        # NEW: Tick Rate (0 = Continuous, >0 = Hz)
        self.tick_rate = 20
        self.tick_timer = 0.0
        
        # Sound Objects
        self.snd_hit_drone = None
        self.snd_miss_drone = None
        self.snd_hit_pulse = None
        self.snd_miss_pulse = None
        
        # Channels (for continuous drones)
        self.chn_hit = None
        self.chn_miss = None
        
        self.generate_sounds()

    def generate_sounds(self):
        # 1. Generate Continuous Drones (1 second loopable)
        self.snd_hit_drone = self._make_sine(self.hit_freq, self.hit_vol)
        self.snd_miss_drone = self._make_sine(self.miss_freq, self.miss_vol)
        
        # 2. Generate Discrete Pulses (0.1 second fade out)
        self.snd_hit_pulse = self._make_pulse(self.hit_freq, self.hit_vol)
        self.snd_miss_pulse = self._make_pulse(self.miss_freq, self.miss_vol)

    def _make_sine(self, freq, volume):
        """Continuous wave"""
        n_samples = self.sample_rate
        buf = array.array('h', [0] * n_samples)
        amplitude = 32767 * volume
        for i in range(n_samples):
            val = math.sin(2 * math.pi * freq * (i / self.sample_rate))
            buf[i] = int(val * amplitude)
        return pygame.mixer.Sound(buffer=buf)

    def _make_pulse(self, freq, volume):
        """Short percussive sound (100ms)"""
        duration = 0.1 
        n_samples = int(self.sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        amplitude = 32767 * volume
        
        for i in range(n_samples):
            # Envelope: Linear decay from 1.0 to 0.0
            env = 1.0 - (i / n_samples)
            val = math.sin(2 * math.pi * freq * (i / self.sample_rate))
            buf[i] = int(val * amplitude * env)
            
        return pygame.mixer.Sound(buffer=buf)

    def update_settings(self, hit_en, miss_en, hit_v, miss_v, hit_f, miss_f, tick_r):
        regen = False
        # If acoustic properties change, regenerate buffers
        if (abs(self.hit_freq - hit_f) > 1 or abs(self.hit_vol - hit_v) > 0.01 or 
            abs(self.miss_freq - miss_f) > 1 or abs(self.miss_vol - miss_v) > 0.01):
            regen = True
            
        self.hit_enabled = hit_en
        self.miss_enabled = miss_en
        self.hit_vol = hit_v
        self.miss_vol = miss_v
        self.hit_freq = hit_f
        self.miss_freq = miss_f
        self.tick_rate = tick_r
        
        if regen:
            self.stop_all()
            self.generate_sounds()

    def update(self, dt, status):
        """
        dt: delta time in seconds
        status: "PERFECT", "LOW", "HIGH"
        """
        # MODE A: CONTINUOUS DRONE (Tick Rate 0)
        if self.tick_rate == 0:
            # Hit Logic
            if status == "PERFECT" and self.hit_enabled:
                if self.chn_hit is None or not self.chn_hit.get_busy():
                    self.chn_hit = self.snd_hit_drone.play(loops=-1, fade_ms=10)
            else:
                if self.chn_hit: self.chn_hit.stop(); self.chn_hit = None

            # Miss Logic
            is_miss = (status == "LOW" or status == "HIGH")
            if is_miss and self.miss_enabled:
                if self.chn_miss is None or not self.chn_miss.get_busy():
                    self.chn_miss = self.snd_miss_drone.play(loops=-1, fade_ms=10)
            else:
                if self.chn_miss: self.chn_miss.stop(); self.chn_miss = None

        # MODE B: DISCRETE PULSES (Tick Rate > 0)
        else:
            # Stop any lingering drones
            if self.chn_hit: self.chn_hit.stop(); self.chn_hit = None
            if self.chn_miss: self.chn_miss.stop(); self.chn_miss = None
            
            self.tick_timer += dt
            interval = 1.0 / self.tick_rate
            
            if self.tick_timer >= interval:
                self.tick_timer -= interval # Keep accumulated time for precision
                
                # Play Shot
                if status == "PERFECT" and self.hit_enabled:
                    self.snd_hit_pulse.play()
                elif (status == "LOW" or status == "HIGH") and self.miss_enabled:
                    self.snd_miss_pulse.play()

    def stop_all(self):
        if self.chn_hit: self.chn_hit.stop()
        if self.chn_miss: self.chn_miss.stop()