import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_side = 0 # 0: None, 1: Right, -1: Left
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constants for robust navigation
        SAFE_DIST = 13.0      # Path verification range
        DANGER_ZONE = 10.0    # Dodge trigger
        MIN_GAP_WIDTH = 3     # 30-degree minimum width
        
        all_rays = lidar_data
        # Look specifically at the focal front cone (30 degrees)
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= 15] + [15.0])

        # 1. STATE MANAGEMENT: Mandatory Commitment
        if self.state == "DODGE":
            # Exit only when the path dead-ahead is truly clear
            if front_dist > 12.5: 
                self.state = "FORWARD"
                self.locked_side = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                # Evaluate overall sector space (-80 to +80)
                left_space = sum(r['distance'] for r in all_rays if -80 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 80)
                self.locked_side = 1 if right_space > left_space else -1

        # 2. PATHFINDING: One-Way Search
        best_angle = 0
        if self.state == "DODGE":
            # ONLY look for paths on the locked side. This PREVENTS oscillation.
            side_rays = [r for r in all_rays if (r['angle'] * self.locked_side) > 0]
            
            gaps = []
            curr_gap = []
            for r in sorted(side_rays, key=lambda x: x['angle']):
                if r['distance'] >= SAFE_DIST: curr_gap.append(r)
                else:
                    if len(curr_gap) >= MIN_GAP_WIDTH: gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= MIN_GAP_WIDTH: gaps.append(curr_gap)
            
            if gaps:
                # Target the safest wide cluster on this side
                best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g)/len(g)))
                best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
            else:
                # No wide gap discovered yet? Use a hard vector on the safe side
                best_angle = 110 * self.locked_side
        else:
            best_angle = 0 # Forward cruise
            
        # 3. STEERING 
        target_steering = best_angle / 90.0
        target_steering = max(-1.1, min(1.1, target_steering))
        
        # Smooth snapping
        steering = (self.last_steering * 0.15) + (target_steering * 0.85)
        self.last_steering = steering

        # 4. THROTTLE
        throttle = 1.0
        if self.state == "DODGE":
            throttle = 0.5 # Maintain speed to ensure we actually turn
        elif abs(steering) > 0.4:
            throttle = 0.7

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
