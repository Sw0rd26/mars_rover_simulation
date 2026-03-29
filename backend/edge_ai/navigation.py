import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_side = 0 # 1: Right, -1: Left
        self.commit_timer = 0
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # --- TUNED HEDGEHOG-CLASS DECISIVE NAVIGATION ---
        # Increased sensitivity to ensure the AI reacts BEFORE the frontend ADAS slows it down.
        SAFE_CORRIDOR = 15.0      # Clear path depth
        DANGER_ZONE = 12.5        # Proactive trigger (up from 11.0)
        FRONT_SWEEP = 45          # Wide focal cone (Total 90 degrees)
        MIN_GAP_WIDTH = 3         # Sector width requirement
        
        all_rays = lidar_data
        # Broad focal cone to prevent "missing" side-rocks
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= FRONT_SWEEP] + [15.0])

        # 1. STATE MACHINE: Irreversible Commitment
        if self.state == "DODGE":
            self.commit_timer += 1
            # Maintain commitment until the path is COMPLETELY clear
            if front_dist > 14.5 and self.commit_timer > 20: 
                self.state = "FORWARD"
                self.locked_side = 0
                self.commit_timer = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                self.commit_timer = 0
                # Choose side based on total peripheral space (-90 to +90)
                left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
                self.locked_side = 1 if right_space > left_space else -1

        # 2. PATHFINDING: The Decisive Escape
        best_angle = 0
        if self.state == "DODGE":
            # ONLY search for gaps on the locked side
            side_rays = [r for r in all_rays if (r['angle'] * self.locked_side) > 0]
            
            gaps = []
            curr_gap = []
            for r in sorted(side_rays, key=lambda x: x['angle']):
                if r['distance'] >= SAFE_CORRIDOR: curr_gap.append(r)
                else:
                    if len(curr_gap) >= MIN_GAP_WIDTH: gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= MIN_GAP_WIDTH: gaps.append(curr_gap)
            
            if gaps:
                # Target the safest gap on the chosen side
                best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g)/len(g)))
                raw_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
                
                # STEERING AMPLIFICATION:
                # If the AI says turn 15 degrees, we turn 60 to be DECISIVE.
                best_angle = raw_angle
                if abs(best_angle) < 60:
                    best_angle = 60 * self.locked_side
            else:
                # No clear safe path? Maximum defensive pivot
                best_angle = 130 * self.locked_side
            
            # Momentum: 50% Speed
            throttle = 0.5 
        else:
            best_angle = 0
            # Adaptive speed control: slow slightly if even a little turned
            throttle = 1.0 if abs(self.last_steering) < 0.2 else 0.8
            
        # 3. STEERING 
        target_steering = best_angle / 90.0
        target_steering = max(-1.4, min(1.4, target_steering))
        
        # Fast Snapping: 90% immediate response
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)

