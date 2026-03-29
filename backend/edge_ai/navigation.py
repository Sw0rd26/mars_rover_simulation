import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_side = 0 # 0: None, 1: Right, -1: Left
        self.last_steering = 0.0
        self.commit_timer = 0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constants for robust navigation
        SAFE_DIST = 14.0      
        DANGER_ZONE = 11.0    
        MIN_GAP_WIDTH = 3     
        
        all_rays = lidar_data
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])

        # 1. STATE MANAGEMENT: Irreversible Commitment
        if self.state == "DODGE":
            self.commit_timer += 1
            # Only exit if front is clear AND we have spent at least 15 frames dodging
            if front_dist > 13.5 and self.commit_timer > 15: 
                self.state = "FORWARD"
                self.locked_side = 0
                self.commit_timer = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                self.commit_timer = 0
                # Choose the path of absolute least resistance on the front 180 sweep
                left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
                self.locked_side = 1 if right_space > left_space else -1

        # 2. PATHFINDING: The "One-Way" Filter
        best_angle = 0
        if self.state == "DODGE":
            # REJECT any path on the 'wrong' side. This stops the "focusing" vibration.
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
                # Aim for the center of the best gap on our chosen side
                best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g)/len(g)))
                best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
            else:
                # If no wide gaps, perform a hard evasive maneuver to the safe side
                best_angle = 120 * self.locked_side
        else:
            best_angle = 0 # Forward cruise
            
        # 3. STEERING 
        target_steering = best_angle / 90.0
        target_steering = max(-1.1, min(1.1, target_steering))
        
        # Immediate snap but with jitter correction
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        # 4. THROTTLE
        throttle = 1.0
        if self.state == "DODGE":
            # Keep moving! Stopping is what gets it stuck. 
            throttle = 0.5 
        elif abs(steering) > 0.4:
            throttle = 0.8

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
