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
        SAFE_DIST = 15.0      # Path verification range
        DANGER_ZONE = 12.0    # Dodge trigger
        MIN_GAP_WIDTH = 3     # 30-degree minimum width
        
        all_rays = lidar_data
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= 20] + [15.0])

        # 1. STATE MANAGEMENT: Enter/Exit Dodging
        if self.state == "DODGE":
            if front_dist > 14.5: # Clear enough to resume forward
                self.state = "FORWARD"
                self.locked_side = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                # Initial commitment: Pick the side with more overall space
                left_space = sum(r['distance'] for r in all_rays if r['angle'] < 0 and r['angle'] >= -90)
                right_space = sum(r['distance'] for r in all_rays if r['angle'] > 0 and r['angle'] <= 90)
                self.locked_side = 1 if right_space > left_space else -1

        # 2. PATHFINDING BASED ON STATE
        best_angle = 0
        if self.state == "DODGE":
            # Find the best gap specifically on our LOCKED SIDE to prevent oscillation
            side_rays = [r for r in all_rays if (r['angle'] * self.locked_side) > 0]
            
            # Find wide clusters on this side
            gaps = []
            curr_gap = []
            for r in sorted(side_rays, key=lambda x: x['angle']):
                if r['distance'] >= SAFE_DIST:
                    curr_gap.append(r)
                else:
                    if len(curr_gap) >= MIN_GAP_WIDTH: gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= MIN_GAP_WIDTH: gaps.append(curr_gap)
            
            if gaps:
                # Target the center of the best gap on our preferred side
                best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g)/len(g)))
                best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
            else:
                # No wide gap? Just steer hard to the locked side
                best_angle = 90 * self.locked_side
        else:
            # Forward cruising: Search for tiny adjustments to stay center-path
            best_angle = 0 # Default straight
            
        # 3. STEERING CALCULATION (Filtered)
        target_steering = best_angle / 90.0
        target_steering = max(-1.0, min(1.0, target_steering))
        
        # Immediate reaction: 90% target, 10% history
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        # 4. THROTTLE
        throttle = 1.0
        if self.state == "DODGE":
            throttle = 0.6 # Maintain speed for maneuverability
        elif abs(steering) > 0.3:
            throttle = 0.8

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
