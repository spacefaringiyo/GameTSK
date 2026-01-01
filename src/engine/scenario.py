import math

class Keyframe:
    def __init__(self, time, speed, tolerance, directions):
        self.time = time
        self.speed = speed
        self.tolerance = tolerance
        self.directions = directions # [Up, Down, Left, Right]

class Scenario:
    def __init__(self, duration):
        self.duration = duration
        self.keyframes = []
    
    def add_keyframe(self, time, speed, tolerance, directions):
        kf = Keyframe(time, speed, tolerance, directions)
        self.keyframes.append(kf)
        # Ensure they are always sorted by time
        self.keyframes.sort(key=lambda k: k.time)

    def get_state_at(self, t):
        """
        Returns (speed, tolerance, directions) for a specific time 't'.
        Interpolates speed between keyframes.
        """
        # Clamp time
        t = max(0, min(t, self.duration))
        
        # 1. Find the two keyframes surrounding time 't'
        # Since lists are small (usually < 50 items), a linear search is fast enough.
        # We look for the first keyframe that is AFTER our current time.
        
        prev_kf = self.keyframes[0]
        next_kf = self.keyframes[-1]
        
        for kf in self.keyframes:
            if kf.time > t:
                next_kf = kf
                break
            prev_kf = kf
            
        # 2. Interpolate
        if prev_kf == next_kf:
            return prev_kf.speed, prev_kf.tolerance, prev_kf.directions
        
        # Calculate progress between prev and next (0.0 to 1.0)
        segment_duration = next_kf.time - prev_kf.time
        if segment_duration <= 0:
            return prev_kf.speed, prev_kf.tolerance, prev_kf.directions
            
        progress = (t - prev_kf.time) / segment_duration
        
        # Lerp Speed
        current_speed = prev_kf.speed + (next_kf.speed - prev_kf.speed) * progress
        
        # Lerp Tolerance (Optional, but looks nice)
        current_tol = prev_kf.tolerance + (next_kf.tolerance - prev_kf.tolerance) * progress
        
        # Directions: Use the previous keyframe's setting until we hit the next one
        # (Discrete change, no interpolation for booleans)
        current_dirs = prev_kf.directions
        
        return current_speed, current_tol, current_dirs

    @staticmethod
    def from_config(data):
        # Update Default Duration (10)
        dur = float(data.get("duration", 10))
        scen = Scenario(dur)
        
        if "timeline" in data:
            for kf in data["timeline"]:
                t = kf.get("time", 0)
                s = kf.get("speed", 500)
                # Update Default Tolerance (75)
                tol = kf.get("tolerance", 75)
                d = kf.get("directions", [True, True, True, True])
                scen.add_keyframe(t, s, tol, d)
        else:
            start_v = float(data.get("start_speed", 500))
            end_v = float(data.get("end_speed", 500))
            # Update Default Tolerance (75)
            tol = float(data.get("tolerance", 75))
            dirs = data.get("directions", [True, True, True, True])
            
            scen.add_keyframe(0.0, start_v, tol, dirs)
            scen.add_keyframe(dur, end_v, tol, dirs)
            
        return scen

    @staticmethod
    def create_remix_example():
        """
        A hardcoded example of what this engine can actually do.
        """
        scen = Scenario(20) # 20 seconds
        
        # 0s: Slow Start
        scen.add_keyframe(0.0, 300, 50, [True, True, True, True])
        
        # 5s: Speed Up
        scen.add_keyframe(5.0, 800, 50, [True, True, True, True])
        
        # 10s: Sudden Stop & Horizontal Only
        scen.add_keyframe(10.0, 200, 30, [False, False, True, True])
        
        # 15s: Vertical Only & Fast
        scen.add_keyframe(15.0, 1000, 100, [True, True, False, False])
        
        # 20s: End
        scen.add_keyframe(20.0, 1000, 100, [True, True, False, False])
        
        return scen