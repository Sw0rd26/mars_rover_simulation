import random
import math

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_gap_angle = 0
        self.dodge_timer = 0
        self.side_preference = 1.0 # 1 for Right, -1 for Left

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # Constants for smooth alignment
        STEERING_SENSITIVITY = 0.8 # Proportional gain
        DODGE_TRIGGER_DIST = 9.0
        DODGE_EXIT_DIST = 14.0
        
        # 1. SCAN FOR HAZARDS
        # Look in a 40-degree front cone
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 20] + [15.0])

        # STATE 1: DODGING (Committed to a specific gap)
        if self.state == "DODGE":
            self.dodge_timer += 1
            
            # Check if the path directly in front is now 'Bone Clear'
            if front_dist > DODGE_EXIT_DIST or self.dodge_timer > 100:
                self.state = "FORWARD"
                self.dodge_timer = 0
                return {"throttle": 1.0, "steering": 0.0}

            # PROPORTIONAL STEERING: Turn toward the locked gap angle
            # The further the angle, the harder we turn. As we align, we slow the turn.
            # This prevents 'Violent Spinning' and 'Overshooting'.
            error = self.locked_gap_angle
            steering = (error / 90.0) * STEERING_SENSITIVITY
            
            # Clamp steering for stability
            steering = max(-1.0, min(1.0, steering))
            
            return {"throttle": 0.5, "steering": steering}

        # STATE 2: FORWARD (Scanning for the next best path)
        else:
            if front_dist < DODGE_TRIGGER_DIST:
                self.state = "DODGE"
                self.dodge_timer = 0
                
                # PATHFINDING: Find the absolute widest gap in the front 180 sweep
                best_gap_angle = 0
                max_gap_val = 0
                
                # Evaluate paths every 10 degrees
                for r in lidar_data:
                    # Only look at the 180-degree front arc (-90 to 90)
                    if abs(r['angle']) <= 90:
                        # Weight paths closer to the center slightly higher to keep forward progress
                        weight = 1.0 - (abs(r['angle']) / 180.0)
                        score = r['distance'] * weight
                        
                        if score > max_gap_val:
                            max_gap_val = score
                            best_gap_angle = r['angle']
                
                # If front is totally blocked, pick a hard side based on overall space
                if max_gap_val < 5.0:
                    left_space = sum(r['distance'] for r in lidar_data if r['angle'] < 0)
                    right_space = sum(r['distance'] for r in lidar_data if r['angle'] > 0)
                    best_gap_angle = 120 if right_space > left_space else -120

                self.locked_gap_angle = best_gap_angle
                
                # Initial steering pulse to get moving
                initial_steering = max(-1.0, min(1.0, self.locked_gap_angle / 90.0))
                return {"throttle": 0.4, "steering": initial_steering}

            # Clean path cruising
            return {"throttle": 1.0, "steering": 0.0}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
