import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_side = 0
        self.commit_timer = 0
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # REVERTED TO CLASSIC STABLE CHOICE LOGIC
        SAFE_DIST = 10.0      
        FRONT_SWEEP = 30
        
        all_rays = lidar_data
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= FRONT_SWEEP] + [15.0])

        # State: Find best path only when needed
        if front_dist < 8.0:
            left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
            right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
            best_angle = 120 if right_space > left_space else -120
            throttle = 0.0 # Stop-and-Spin Stability
        else:
            best_angle = 0
            throttle = 1.0

        target_steering = best_angle / 90.0
        target_steering = max(-1.0, min(1.0, target_steering))
        
        steering = (self.last_steering * 0.2) + (target_steering * 0.8)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
