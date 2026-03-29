import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.timer = 0
        self.turn_dir = 1.0
        self.min_turn_ticks = 12 # Force at least 1.2 seconds of turning to prevent 'shaking'

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # STATE 1: Stable Turning Maneuver
        if self.state == "TURN":
            self.timer += 1
            
            # Check current heading clearance
            front_distance = min([r['distance'] for r in lidar_data if abs(r['angle']) <= 15] + [15.0])
            
            # Find the absolute best path available in the entire 360-degree scan
            max_all_distance = max([r['distance'] for r in lidar_data] + [0.0])
            
            # EXIT STRATEGY: 
            # 1. Must stay in TURN for at least min_turn_ticks to ensure a visible, stable change in heading
            # 2. After that, exit if path is clear (> 13m) or aligned with the absolute best available vector
            is_safest_aligned = (front_distance >= max_all_distance - 0.5) and (front_distance > 9.0)
            
            if self.timer >= self.min_turn_ticks:
                if front_distance > 13.0 or is_safest_aligned or self.timer > 60:
                    self.state = "FORWARD"
                    self.timer = 0
                
            return {"throttle": 0.2, "steering": self.turn_dir}

        # STATE 2: Driving forward
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
