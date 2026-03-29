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

        # --- HEDGEHOG V4: WIDE-SECTOR GAP VECTORING ---
        SAFE_CORRIDOR = 14.5      # Distance to define a "Green" path
        DANGER_ZONE = 12.0        # Trigger to start dodging
        FRONT_SWEEP = 50          # 100-degree focal cone for hazard detection
        
        all_rays = lidar_data
        # Broad focal cone (90 degrees total) to catch side-objects
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= FRONT_SWEEP] + [15.0])

        # 1. STATE DETERMINATION
        if self.state == "DODGE":
            self.commit_timer += 1
            # Maintain dodge until the front is ENTIRELY clear and we've committed
            if front_dist > 14.0 and self.commit_timer > 30: 
                self.state = "FORWARD"
                self.locked_side = 0
                self.commit_timer = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                self.commit_timer = 0
                # Initial choice based on total space
                left_space = sum(r['distance'] for r in all_rays if -70 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 70)
                self.locked_side = 1 if right_space > left_space else -1

        # 2. SECTOR ANALYSIS: The "Turn to Green" Logic
        best_angle = 0
        if self.state == "DODGE":
            # Identify all Safe Gaps in the environment
            gaps = []
            curr_gap = []
            # Scan all rays to find "Green Roads"
            for r in sorted(all_rays, key=lambda x: x['angle']):
                if r['distance'] >= SAFE_CORRIDOR:
                    curr_gap.append(r)
                else:
                    if len(curr_gap) >= 4: # Min 40-degree width for safety
                        gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= 4: gaps.append(curr_gap)
            
            # Find the best gap on our locked side
            side_gaps = [g for g in gaps if (sum(r['angle'] for r in g)/len(g)) * self.locked_side > 0]
            
            if side_gaps:
                # Target the largest gap on the correct side
                best_gap = max(side_gaps, key=lambda g: len(g))
                best_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
                # AMPLIFY: Ensure we dodge wide enough to clear the rock
                if abs(best_angle) < 65:
                    best_angle = 65 * self.locked_side
            else:
                # No gaps found on that side? Hard pivot
                best_angle = 135 * self.locked_side
            
            throttle = 0.5 # Gliding momentum
        else:
            # FORWARD: Smooth cruise
            best_angle = 0
            throttle = 1.0

        # 3. STEERING RESOLUTION
        target_steering = best_angle / 90.0
        # Aggressive steering override during dodge
        if self.state == "DODGE":
            target_steering *= 1.4 
            
        target_steering = max(-1.4, min(1.4, target_steering))
        
        # High-response steering (90% immediate)
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
