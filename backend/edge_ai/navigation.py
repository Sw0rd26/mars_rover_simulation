import random
import math

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.target_angle = 0
        self.timer = 0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constant check for immediate front clearance
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])

        # STATE 1: DODGING (Locked onto a safe pathway)
        if self.state == "DODGE":
            self.timer += 1
            
            # Find current clearance at the target angle
            # We look in a small cone around our target to see if it's still viable
            target_clearance = min([r['distance'] for r in lidar_data if abs(r['angle'] - self.target_angle) <= 15] + [15.0])
            
            # EXIT CONDITION: We are facing a clear path > 13m OR we've been dodging too long
            if front_dist > 13.0 or self.timer > 80:
                self.state = "FORWARD"
                return {"throttle": 1.0, "steering": 0.0}

            # Steering: Close the gap to the target angle
            # Normalized -1 to 1. Positive angle = Right Steering
            steering = self.target_angle / 90.0
            steering = max(-1.0, min(1.0, steering))
            
            return {"throttle": 0.4, "steering": steering}

        # STATE 2: FORWARD (Scanning for obstacles)
        else:
            # Trigger Dodge if front is blocked (< 9.0m)
            if front_dist < 9.0:
                self.state = "DODGE"
                self.timer = 0
                
                # PATHFINDING: Find the widest gap in the full 360 scan
                # We prioritize gaps in the front 180 degrees first
                best_gap_angle = 0
                max_gap_dist = 0
                
                # Check every 10 degrees for the clearest vector
                for r in lidar_data:
                    # We give a slight bias to forward-facing gaps to prevent 'U-turns'
                    bias = 1.0 - (abs(r['angle']) / 360.0) 
                    weighted_dist = r['distance'] * bias
                    
                    if weighted_dist > max_gap_dist:
                        max_gap_dist = weighted_dist
                        best_gap_angle = r['angle']
                
                self.target_angle = best_gap_angle
                
                return {"throttle": 0.4, "steering": self.target_angle / 90.0}

            # Normal cruising
            return {"throttle": 1.0, "steering": 0.0}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
