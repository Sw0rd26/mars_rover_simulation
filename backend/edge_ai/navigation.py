import random

class EdgeAIAgent:
    def __init__(self):
        self.state = "FORWARD"
        self.locked_side = 0
        self.last_steering = 0.0

    def calculate_drive_command(self, lidar_data: list) -> dict:
        if not lidar_data:
            return {"throttle": 0.0, "steering": 0.0}

        # --- RESTRAINED STABLE TANK-TURN AI ---
        SAFE_CORRIDOR = 13.0     # Clear distance required to 'Go'
        FRONT_SWEEP = 35         # 70-degree focal cone
        
        all_rays = lidar_data
        front_dist = min([r['distance'] for r in lidar_data if abs(r['angle']) <= FRONT_SWEEP] + [15.0])

        # State Determination
        if front_dist < 8.5:
            self.state = "DODGE"
        elif front_dist > 12.0:
            self.state = "FORWARD"

        if self.state == "DODGE":
            # TANK TURN LOGIC: stop and pivot toward the widest opening
            left_space = sum(r['distance'] for r in all_rays if -90 <= r['angle'] < 0)
            right_space = sum(r['distance'] for r in all_rays if 0 < r['angle'] <= 90)
            
            # Decisive vector selection
            best_angle = 120 if right_space > left_space else -120
            throttle = 0.0 # Pivot in place
        else:
            best_angle = 0
            # Adaptive speed: slow down slightly when turning just in case
            throttle = 1.0

        target_steering = best_angle / 90.0
        target_steering = max(-1.1, min(1.1, target_steering))
        
        # Immediate steering response for Tank Turns
        steering = (self.last_steering * 0.1) + (target_steering * 0.9)
        self.last_steering = steering

        return {"throttle": throttle, "steering": steering}

# Global singleton
agent = EdgeAIAgent()

def calculate_drive_command(lidar_data: list) -> dict:
    return agent.calculate_drive_command(lidar_data)
