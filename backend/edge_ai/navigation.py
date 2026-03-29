import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.timer = 0
        self.turn_dir = 1.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # STATE 1: Maneuvering while maintaining momentum
        if self.state == "TURN":
            self.timer += 1
            
            # Check current heading
            front_distance = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])
            
            # Find the absolute best path available in the entire 360-degree scan
            max_all_distance = max([r['distance'] for r in lidar_data] + [0.0])
            
            # EXIT STRATEGY: Stop dodging once a clear path is found or the best vector is aligned
            is_safest_aligned = (front_distance >= max_all_distance - 1.0) and (front_distance > 8.0)
            
            if front_distance > 12.0 or is_safest_aligned or self.timer > 40:
                self.state = "FORWARD"
                
            # CONTINUOUS DODGE: Keep moving forward at 40% speed while steering
            return {"throttle": 0.4, "steering": self.turn_dir}

        # STATE 2: Driving forward
        else: # self.state == "FORWARD"
            front_distance = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 20] + [15.0])
            
            # Trigger dodge if getting close
            if front_distance < 9.0:
                self.state = "TURN"
                self.timer = 0 
                
                # Pick side with more space
                left_space = sum(r['distance'] for r in lidar_data if r['angle'] < 0 and r['angle'] >= -90)
                right_space = sum(r['distance'] for r in lidar_data if r['angle'] > 0 and r['angle'] <= 90)
                
                self.turn_dir = 1.0 if right_space > left_space else -1.0
                return {"throttle": 0.4, "steering": self.turn_dir}

            return {"throttle": 1.0, "steering": 0.0}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
