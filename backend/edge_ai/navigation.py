import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.timer = 0
        self.turn_dir = 1.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # STATE 1: Turning dynamically until the coast is clear
        if self.state == "TURN":
            self.timer += 1
            
            # Check a tight cone dead-ahead to see exactly what the front wheels are facing
            front_distance = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])
            
            # Stop turning the exact moment the physical path directly in front is clear!
            # Increased clear opening threshold to 12.0 meters (huge range!)
            if front_distance > 12.0 or self.timer > 50:
                self.state = "FORWARD"
                
            return {"throttle": 0.0, "steering": self.turn_dir}

        # STATE 2: Driving forward
        else: # self.state == "FORWARD"
            
            # Look at objects directly in front of the rover
            front_distance = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 20] + [15.0])
            
            # INCREASED RANGE: Trigger turn when 8.5 meters away! (Reduced from 9.0 to avoid jitter)
            if front_distance < 8.5:
                # Look broadly at both sides (FRONT ONLY) to definitively pick the most open path
                left_space = sum(r['distance'] for r in lidar_data if r['angle'] < 0 and r['angle'] >= -90)
                right_space = sum(r['distance'] for r in lidar_data if r['angle'] > 0 and r['angle'] <= 90)

                # Pick a random direction if the spaces are perfectly equal to avoid getting stuck
                if abs(right_space - left_space) < 0.1:
                    self.turn_dir = random.choice([1.0, -1.0])
                elif right_space > left_space:
                    self.turn_dir = 1.0 # Right
                else:
                    self.turn_dir = -1.0 # Left
                
                self.state = "TURN"
                self.timer = 0 
                return {"throttle": 0.0, "steering": self.turn_dir}

            # If the path DIRECTLY AHEAD is clear, just drive completely straight!
            return {"throttle": 1.0, "steering": 0.0}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
