import math
import collections
# Removed: from src.core.config import TARGET_FPS 

class Engine:
    def __init__(self, max_history=1200):
        # Increased buffer to handle high-fps inputs safely
        self.raw_history = collections.deque(maxlen=max_history)
        self.graph_points = collections.deque(maxlen=1200) 
        
        self.smoothing_window = 75
        
        # --- THE GOLDEN STANDARD ---
        # We treat 144Hz as the reference reality for all physics/graphing.
        # This prevents FPS manipulation from changing gameplay difficulty.
        self.REFERENCE_FPS = 144.0 
        
        self.graph_accumulator = 0.0
        self.graph_step = 1.0 / self.REFERENCE_FPS 
    
    def reset_graph(self):
        self.graph_points.clear()
        self.graph_accumulator = 0.0

    def reset_history(self):
        self.raw_history.clear()

    def process_frame(self, dx, dy, dt, target_speed, tolerance, directions):
        # 1. Filter Direction
        allow_up, allow_down, allow_left, allow_right = directions
        valid_dx = 0; valid_dy = 0
        if dx < 0 and allow_left: valid_dx = dx
        elif dx > 0 and allow_right: valid_dx = dx
        if dy < 0 and allow_up: valid_dy = dy
        elif dy > 0 and allow_down: valid_dy = dy

        # 2. Store Data (Time, Distance)
        raw_dist = math.sqrt(valid_dx**2 + valid_dy**2)
        self.raw_history.append((dt, raw_dist))

        # 3. Time-Based Smoothing (Standardized)
        # We calculate duration using REFERENCE_FPS, not local TARGET_FPS.
        # Slider 15 always means ~0.1 seconds, regardless of computer speed.
        target_duration = self.smoothing_window / self.REFERENCE_FPS
        
        total_time = 0.0
        total_dist = 0.0
        
        for h_dt, h_dist in reversed(self.raw_history):
            total_time += h_dt
            total_dist += h_dist
            if total_time >= target_duration:
                break
        
        if total_time > 0.0001:
            smoothed_speed = total_dist / total_time
        else:
            smoothed_speed = 0.0

        # 4. Determine Status
        min_zone = target_speed - tolerance
        max_zone = target_speed + tolerance
        
        status = "PERFECT"
        diff = 0
        
        if smoothed_speed < min_zone:
            status = "LOW"
            diff = smoothed_speed - min_zone
        elif smoothed_speed > max_zone:
            status = "HIGH"
            diff = smoothed_speed - max_zone
            
        return smoothed_speed, status, diff

    def get_target_for_time(self, elapsed, duration, start_val, end_val):
        if duration <= 0: return start_val
        progress = min(1.0, max(0.0, elapsed / duration))
        return start_val + (end_val - start_val) * progress

    def record_graph_point(self, dt, speed, color, target, tolerance): 
        self.graph_accumulator += dt
        
        loop_guard = 0
        MAX_LOOPS = 20 
        
        # Accumulate points based on the REFERENCE step (1/144), not frame rate
        while self.graph_accumulator >= self.graph_step and loop_guard < MAX_LOOPS:
            self.graph_accumulator -= self.graph_step
            self.graph_points.append((speed, color, target, tolerance))
            loop_guard += 1
            
        if loop_guard >= MAX_LOOPS:
            self.graph_accumulator = 0.0