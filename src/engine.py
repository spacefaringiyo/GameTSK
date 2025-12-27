import math
import collections

class Engine:
    def __init__(self, max_history=300):
        self.raw_history = collections.deque(maxlen=max_history)
        self.graph_points = collections.deque(maxlen=1200) 
        self.smoothing_window = 10
    
    def reset_graph(self):
        self.graph_points.clear()

    def reset_history(self):
        self.raw_history.clear()

    def process_frame(self, dx, dy, dt, target_speed, tolerance, directions):
        """
        directions: tuple (up, down, left, right) booleans
        """
        # 1. Filter Direction
        allow_up, allow_down, allow_left, allow_right = directions
        
        valid_dx = 0
        valid_dy = 0
        
        # X Axis Logic
        if dx < 0 and allow_left: valid_dx = dx
        elif dx > 0 and allow_right: valid_dx = dx
        
        # Y Axis Logic
        if dy < 0 and allow_up: valid_dy = dy
        elif dy > 0 and allow_down: valid_dy = dy

        # 2. Calculate Speed using ONLY valid components
        raw_dist = math.sqrt(valid_dx**2 + valid_dy**2)
        current_pps = 0
        if dt > 0:
            current_pps = raw_dist / dt
        
        self.raw_history.append(current_pps)

        # 3. Smooth
        current_window = list(self.raw_history)[-int(self.smoothing_window):]
        if current_window:
            smoothed_speed = sum(current_window) / len(current_window)
        else:
            smoothed_speed = 0

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

    def record_graph_point(self, speed, color, target):
        self.graph_points.append((speed, color, target))