import random

class EdgeAIAgent:
    def __init__(self):
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constants for 'High-Range' proactive logic
        SAFE_DIST = 15.0      # Increased requirement: Search for 15m clear paths
        MIN_GAP_WIDTH = 3     # Consecutive rays (30 degrees)
        DANGER_ZONE = 12.0    # Dodge earlier (12m instead of 10m)
        
        # 1. EVALUATE ALL PATHS
        all_rays = lidar_data
        gaps = []
        current_gap = []
        
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

        # 2. PICK THE BEST GAP
        best_angle = 0
        is_safe_path_found = False
        
        if gaps:
            best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g) / len(g)))
            best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
            is_safe_path_found = True
        else:
            max_val = 0
            for r in all_rays:
                bias = 1.0 - (abs(r['angle']) / 360.0) 
                score = r['distance'] * bias
                if score > max_val:
                    max_val = score
                    best_angle = r['angle']

        # 3. CALCULATE STEERING
        target_steering = best_angle / 90.0
        target_steering = max(-1.0, min(1.0, target_steering))
        
        # Overclocked smoothing: 90% instant reaction for 'Immediate' turn feel
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        # 4. THROTTLE LOGIC
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])
        
        if not is_safe_path_found or front_dist < DANGER_ZONE:
            # High-performance Dodge: Maintain 60% speed for carrying momentum through turns
            throttle = 0.6
        elif abs(steering) > 0.4:
            throttle = 0.8
        else:
            throttle = 1.0

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
