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

        # --- HEDGEHOG V5: HARD HYSTERESIS & IRREVERSIBLE DECISION ---
        SAFE_CORRIDOR = 14.5      # Distance to define a "Green" road
        DANGER_ZONE = 12.0        # Proactive trigger
        FRONT_SWEEP = 50          # 100-degree total focal cone
        
        all_rays = lidar_data
        # Focal front cone to catch side-objects early
        front_dist = min([r['distance'] for r in all_rays if abs(r['angle']) <= FRONT_SWEEP] + [15.0])

        # 1. STATE MACHINE: Hard Hysteresis
        if self.state == "DODGE":
            self.commit_timer += 1
            # CRITICAL: Do NOT exit dodge until the path is PERFECTLY clear (15.0m)
            # This prevents flickering between Dodge/Forward/Reverse logic.
            if front_dist >= 14.9 and self.commit_timer > 40: 
                self.state = "FORWARD"
                self.locked_side = 0
                self.commit_timer = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                self.commit_timer = 0
                # Choose the side with the most total safe volume
                left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
                # IRREVERSIBLE: This choice is locked until the path is 15m clear.
                self.locked_side = 1 if right_space > left_space else -1

        # 2. SECTOR ANALYSIS: The "One Side" Only Search
        best_angle = 0
        if self.state == "DODGE":
            # Identify "Green Roads" (Gaps)
            gaps = []
            curr_gap = []
            for r in sorted(all_rays, key=lambda x: x['angle']):
                if r['distance'] >= SAFE_CORRIDOR:
                    curr_gap.append(r)
                else:
                    if len(curr_gap) >= 3: gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= 3: gaps.append(curr_gap)
            
            # FOCUS ONLY ON THE CHOSEN SIDE (Locked Side)
            # This prevents "searching" for a better road on the other side mid-turn.
            side_gaps = [g for g in gaps if (sum(r['angle'] for r in g)/len(g)) * self.locked_side > 0]
            
            if side_gaps:
                # Target the largest gap on our locked side
                best_gap = max(side_gaps, key=lambda g: len(g))
                target_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
                # DECISIVE: Ensure the turn is aggressive enough (Min 70 degrees)
                best_angle = target_angle
                if abs(best_angle) < 70:
                    best_angle = 70 * self.locked_side
            else:
                # No green path on the locked side? Force a wide evasive pivot
                best_angle = 140 * self.locked_side
            
            throttle = 0.5 # Maintain gliding momentum
        else:
            # FORWARD: Normal cruise
            best_angle = 0
            # Slow down slightly if carrying residual steering
            throttle = 1.0 if abs(self.last_steering) < 0.2 else 0.8

        # 3. STEERING RESOLUTION
        target_steering = best_angle / 90.0
        # Aggressive steering during dodge state to clear the "red signals"
        if self.state == "DODGE":
            target_steering *= 1.6 # Massive turn response
            
        target_steering = max(-1.6, min(1.6, target_steering))
        
        # High-response snapping
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
