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

        # --- HEDGEHOG CLASS NAVIGATION CONSTANTS ---
        SAFE_DIST = 14.0      # Path verification depth
        DANGER_ZONE = 10.5    # Dodge trigger distance
        MIN_GAP_WIDTH = 3     # 30-degree minimum width for a safe sector
        
        all_rays = lidar_data
        # Focal front cone (30 degrees)
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= 15] + [15.0])

        # 1. STATE MACHINE: Irreversible Side Commitment
        if self.state == "DODGE":
            self.commit_timer += 1
            # Only exit if the way ahead is TRULY clear and we have committed for a min time
            if front_dist > 13.5 and self.commit_timer > 20: 
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

        # 2. PATHFINDING: The Hedgehog Evasion
        best_angle = 0
        if self.state == "DODGE":
            # ONLY search for gaps on the locked side (prevents oscillation)
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
                # Find the gap that requires the least sharp turn
                best_gap = min(gaps, key=lambda g: abs(sum(r['angle'] for r in g)/len(g)))
                best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
            else:
                # No clear gap? Emergency pivot toward the safe side
                best_angle = 120 * self.locked_side
        else:
            best_angle = 0 # Cruise forward
            
        # 3. STEERING 
        target_steering = best_angle / 90.0
        target_steering = max(-1.1, min(1.1, target_steering))
        
        # Smooth snapping (80% immediate, 20% inertia)
        steering = (self.last_steering * 0.2) + (target_steering * 0.8)
        self.last_steering = steering

        # 4. THROTTLE: Smooth-Glide Momentum
        throttle = 1.0
        if self.state == "DODGE":
            # RECOGNIZED HEDGEHOG BEHAVIOR: 50% speed during maneuvers. NEVER STOP.
            throttle = 0.5 
        elif abs(steering) > 0.4:
            throttle = 0.8

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
