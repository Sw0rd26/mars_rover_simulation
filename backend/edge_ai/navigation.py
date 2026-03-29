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

        # --- HEDGEHOG V7: SPATIAL CLEARANCE HYSTERESIS ---
        ROVER_WIDTH_SAFETY = 3.0   # 3.0m corridor for evasion triggering
        DANGER_ZONE = 11.5         # Proactive trigger distance
        
        all_rays = lidar_data
        
        # 1. TRIGGER: SURGICAL CORRIDOR
        # Check if anything is PHYSICALLY in the way of the rover's width
        corridor_hazards = []
        for r in all_rays:
            # We only care about rocks in front for the TRIGGER
            if abs(r['angle']) > 90: continue 
            lateral_offset = abs(r['distance'] * math.sin(math.radians(r['angle'])))
            if r['distance'] < DANGER_ZONE and lateral_offset < (ROVER_WIDTH_SAFETY / 2.0):
                corridor_hazards.append(r)
        
        is_blocked = len(corridor_hazards) > 0

        # 2. CLEARANCE: 180-DEGREE PROXIMITY
        # We only exit DODGE if the ENTIRE front semicircle is clear.
        # This stops the "Circling" (Orbiting) behavior.
        proximity_front = min([r['distance'] for r in all_rays if abs(r['angle']) <= 95] + [15.0])
        is_fully_clear = (proximity_front >= 13.5)

        # 3. STATE MACHINE
        if self.state == "DODGE":
            self.commit_timer += 1
            # CRITICAL: Stay in DODGE until the environment is 100% clear.
            if is_fully_clear and self.commit_timer > 30: 
                self.state = "FORWARD"
                self.locked_side = 0
                self.commit_timer = 0
        else:
            if is_blocked:
                self.state = "DODGE"
                self.commit_timer = 0
                # Choose escape side based on total peripheral clearance
                left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
                right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
                self.locked_side = 1 if right_space > left_space else -1

        # 4. DECISIVE BYPASS VECTOR
        best_angle = 0
        if self.state == "DODGE":
            # Search for the best "Green Road" (Gap) on the locked side
            gaps = []
            curr_gap = []
            for r in sorted(all_rays, key=lambda x: x['angle']):
                if r['distance'] >= 14.5: curr_gap.append(r)
                else:
                    if len(curr_gap) >= 3: gaps.append(curr_gap)
                    curr_gap = []
            if len(curr_gap) >= 3: gaps.append(curr_gap)
            
            side_gaps = [g for g in gaps if (sum(r['angle'] for r in g)/len(g)) * self.locked_side > 0]
            
            if side_gaps:
                # Target the largest gap on our side
                best_gap = max(side_gaps, key=lambda g: len(g))
                target_angle = sum(r['angle'] for r in best_gap) / len(best_gap)
                
                # SHARP PASS LOGIC:
                # The closer the rock, the more we rotate AWAY from it.
                # Min dodge angle is 85 degrees to ensure we clear the side footprint.
                best_angle = target_angle
                if abs(best_angle) < 85:
                    best_angle = 85 * self.locked_side
            else:
                # Emergency: Maximum evasive pivot
                best_angle = 145 * self.locked_side
            
            throttle = 0.5 # Maintain gliding momentum
        else:
            # FORWARD: Normal cruise
            best_angle = 0
            # Stability: Slow down if turning
            throttle = 1.0 if abs(self.last_steering) < 0.2 else 0.8

        # 5. STEERING RESOLUTION
        target_steering = best_angle / 90.0
        # Aggressive steering override (2.0x) to clear obstacles decisively
        if self.state == "DODGE":
            target_steering *= 2.0
            
        target_steering = max(-1.8, min(1.8, target_steering))
        
        # High-response snapping
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
