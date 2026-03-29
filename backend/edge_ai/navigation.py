import random

class EdgeAIAgent:
    def __init__(self):
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constants for 'Snap-to-Safe-Path' logic
        SAFE_THRESHOLD = 12.0 # Requirement: Ensure path is safe for at least 12m
        DANGER_ZONE = 10.0    # Requirement: Dodge when objects get in this range
        
        # 1. EVALUATE ALL PATHS (360 Degrees)
        all_rays = lidar_data
        safe_rays = [r for r in all_rays if r['distance'] >= SAFE_THRESHOLD]
        
        # 2. DECIDE BEST VECTOR
        best_angle = 0
        if safe_rays:
            # Pick the safe sector that is CLOSEST to our current forward heading (0°)
            # This ensures we don't do violent U-turns if a forward path is available.
            best_r = min(safe_rays, key=lambda x: abs(x['angle']))
            best_angle = best_r['angle']
        else:
            # If no path is >= 12m, pick the absolute clearest direction available
            # but bias it heavily toward the front 180 degrees.
            max_dist = 0
            for r in all_rays:
                # Add a 'Frontal Bias' – we prefer going forward over backward
                bias = 1.0 - (abs(r['angle']) / 360.0) 
                score = r['distance'] * bias
                if score > max_dist:
                    max_dist = score
                    best_angle = r['angle']

        # 3. CALCULATE STEERING
        # We need an 'Immediate' turn but without the feedback-loop spin.
        # Steering is relative to the current front. 
        target_steering = best_angle / 90.0
        target_steering = max(-1.0, min(1.0, target_steering))
        
        # Apply Hysteresis: 40% influence from last frame to smooth out 'violent' jitter
        steering = (self.last_steering * 0.4) + (target_steering * 0.6)
        self.last_steering = steering

        # 4. THROTTLE LOGIC
        # Check if we are in the 'Danger Zone' (Frontal obstacle < 10m)
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= 15] + [15.0])
        
        throttle = 1.0
        if front_dist < DANGER_ZONE:
            # We are dodging. Use 50% speed to ensure the turn is tight and controlled.
            throttle = 0.5
        elif abs(steering) > 0.5:
            # High-angle turn: Slow down slightly to maintain traction
            throttle = 0.7

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
