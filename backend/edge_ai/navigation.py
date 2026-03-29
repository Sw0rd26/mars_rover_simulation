import random

class EdgeAIAgent:
    def __init__(self):
        # We've removed the TURN state machine to provide 'Instant' proactive steering
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # 1. ANALYZE THE FRONT HEMISPHERE (-90 to +90)
        front_lidar = [r for r in lidar_data if abs(r['angle']) <= 100]
        if not front_lidar:
            return {"throttle": 0.0, "steering": 0.0}

        # 2. FIND THE WIDEST 'GAPS' (Paths with at least 6m clearance)
        # We look for the angle that points to the most open space
        best_angle = 0
        max_dist = 0
        
        # Strategy: Find the single 'Safest Vector' in the front 180 degrees
        for r in front_lidar:
            if r['distance'] > max_dist:
                max_dist = r['distance']
                best_angle = r['angle']

        # 3. DECISION LOGIC: Proactive Steering
        # Calculate the direct steering needed to face the 'Best Angle'
        # normalized -1 (Left) to 1 (Right). 
        # Note: In our system, positive angle is Right, so steering is best_angle / 90.0
        target_steering = best_angle / 90.0
        
        # Smooth the steering to prevent 'shaking' while remaining instant
        steering = (self.last_steering * 0.4) + (target_steering * 0.6)
        self.last_steering = steering

        # 4. THROTTLE LOGIC: Dynamic Speed based on path clearance
        center_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])
        
        throttle = 1.0
        if center_dist < 4.0:
            # Dangerously close! Reverse and steer away from the nearest object
            throttle = -0.6
            # Override steering to turn away from the closest obstruction
            closest_obj = min(front_lidar, key=lambda x: x['distance'])
            steering = 1.0 if closest_obj['angle'] < 0 else -1.0
        elif center_dist < 8.0:
            # Approaching obstacle: Slow down to 40% speed and steer hard into the gap
            throttle = 0.4
        elif abs(steering) > 0.4:
            # Turning significantly: Reduce speed slightly for stability
            throttle = 0.7

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
        else: # self.state == "FORWARD"
            front_distance = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 20] + [15.0])
            
            # TRIGGER DODGE: Detect obstacle within 9.0 meters
            if front_distance < 9.0:
                # Look broadly at both sides to pick the most open path
                left_space = sum(r['distance'] for r in lidar_data if r['angle'] < 0 and r['angle'] >= -90)
                right_space = sum(r['distance'] for r in lidar_data if r['angle'] > 0 and r['angle'] <= 90)

                self.turn_dir = 1.0 if right_space > left_space else -1.0
                
                self.state = "TURN"
                self.timer = 0 
                return {"throttle": 0.2, "steering": self.turn_dir}

            # If the path DIRECTLY AHEAD is clear, just drive completely straight!
            return {"throttle": 1.0, "steering": 0.0}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
