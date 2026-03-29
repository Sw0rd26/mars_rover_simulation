import math

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_side = 0 # 1: Right, -1: Left
        self.commit_timer = 0
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # --- HEDGEHOG V6: SURGICAL CORRIDOR EVASION ---
        # Only focus on rocks that are PHYSICALLY in our path (Width-based Corridor)
        ROVER_WIDTH_SAFETY = 2.8   # 2.8m corridor (Rover is 1.8m)
        DANGER_ZONE = 12.0         # Proactive trigger distance
        SAFE_CORRIDOR_DIST = 14.5  # Distance to define a "Green" road
        
        all_rays = lidar_data
        
        # 1. HAZARD DETECTION: "Only what blocks me"
        # Find rocks that are both CLOSER than DANGER_ZONE and inside the ROVER'S WIDTH corridor.
        hazards = []
        for r in all_rays:
            ang_rad = math.radians(r['angle'])
            # Lateral distance from the center-line: d * sin(angle)
            lateral_offset = abs(r['distance'] * math.sin(ang_rad))
            if r['distance'] < DANGER_ZONE and lateral_offset < (ROVER_WIDTH_SAFETY / 2.0):
                hazards.append(r)
        
        front_dist = min([h['distance'] for h in hazards] + [15.0])

        # 2. STATE MACHINE: Irreversible Decision
        if self.state == "DODGE":
            self.commit_timer += 1
            # Hard Hysteresis: Don't exit until the path is PERFECTLY clear for a sustained period
            if front_dist >= 14.9 and self.commit_timer > 35: 
                self.state = "FORWARD"
                self.locked_side = 0
                self.commit_timer = 0
        else:
            if front_dist < DANGER_ZONE:
                self.state = "DODGE"
                self.commit_timer = 0
                # Choose the side with the most peripheral space to bypass
                left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
                self.locked_side = 1 if right_space > left_space else -1

        # 3. SECTOR ANALYSIS: "Turn Sharply to Green"
        best_angle = 0
        if self.state == "DODGE":
            # Identify "Green Roads" (Safe Gaps)
            gaps = []
            curr_gap = []
            for r in sorted(all_rays, key=lambda x: x['angle']):
                if r['distance'] >= SAFE_CORRIDOR_DIST:
                    curr_gap.append(r)
                else:
                    if len(curr_gap) >= 3: gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= 3: gaps.append(curr_gap)
            
            # Target the best gap on our locked side
            side_gaps = [g for g in gaps if (sum(r['angle'] for r in g)/len(g)) * self.locked_side > 0]
            
            if side_gaps:
                # Target the largest gap on our side
                best_gap = max(side_gaps, key=lambda g: len(g))
                target_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
                
                # SURGICAL BYPASS: Ensure the turn is aggressive enough to PASS the rock
                # The closer the rock, the sharper we turn.
                proximity_multiplier = max(1.0, 15.0 / (front_dist + 0.1))
                best_angle = target_angle * 0.5 + (80 * self.locked_side * 0.5)
                # Ensure a minimum decisive turn of 80 degrees
                if abs(best_angle) < 80:
                    best_angle = 80 * self.locked_side
            else:
                # Emergency: Maximum defensive pivot
                best_angle = 145 * self.locked_side
            
            throttle = 0.5 # Gliding momentum
        else:
            best_angle = 0
            throttle = 1.0 if abs(self.last_steering) < 0.2 else 0.8

        # 4. STEERING RESOLUTION
        target_steering = best_angle / 90.0
        # Aggressive steering during dodge state to bypass the obstacle quickly
        if self.state == "DODGE":
            # Steering is now highly aggressive (1.8x) to ensure sharp passes
            target_steering *= 1.8
            
        target_steering = max(-1.6, min(1.6, target_steering))
        
        # Immediate response snapping
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
