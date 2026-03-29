import random

class EdgeAIAgent:
    def __init__(self):
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constants for 'Path-Width' logic
        SAFE_DIST = 12.0      # Requirement: Path must be clear for 12m
        MIN_GAP_WIDTH = 3     # Number of consecutive rays (3 rays = 30 degrees width)
        
        # 1. IDENTIFY ALL SAFE RAYS (>= 12m)
        all_rays = lidar_data
        
        # 2. FIND WIDE GAP CLUSTERS
        # A wide gap is a sequence of rays where EVERY ray is safe.
        gaps = []
        current_gap = []
        
        # Sort rays by angle to find consecutive clusters
        sorted_lidar = sorted(all_rays, key=lambda x: x['angle'])
        
        for r in sorted_lidar:
            if r['distance'] >= SAFE_DIST:
                current_gap.append(r)
            else:
                if len(current_gap) >= MIN_GAP_WIDTH:
                    gaps.append(current_gap)
                current_gap = []
        if len(current_gap) >= MIN_GAP_WIDTH:
            gaps.append(current_gap)

        # 3. PICK THE BEST GAP
        best_angle = 0
        is_safe_path_found = False
        
        if gaps:
            # Of all wide gaps, pick the one closest to our current forward heading (0°)
            best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g) / len(g)))
            # Target the center of the gap
            best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
            is_safe_path_found = True
        else:
            # If NO wide gap >= 12m exists, find the single clearest direction
            # but bias it towards the front 180 degrees.
            max_val = 0
            for r in all_rays:
                bias = 1.0 - (abs(r['angle']) / 360.0) 
                score = r['distance'] * bias
                if score > max_val:
                    max_val = score
                    best_angle = r['angle']

        # 4. CALCULATE STEERING
        target_steering = best_angle / 90.0
        target_steering = max(-1.0, min(1.0, target_steering))
        
        # Apply smoothing
        steering = (self.last_steering * 0.3) + (target_steering * 0.7)
        self.last_steering = steering

        # 5. THROTTLE LOGIC
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])
        
        if not is_safe_path_found or front_dist < 8.0:
            # Hard Dodge mode: Use 40% speed for precision turning
            throttle = 0.4
        elif abs(steering) > 0.4:
            # Curve smoothing
            throttle = 0.7
        else:
            # Clear path
            throttle = 1.0

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
