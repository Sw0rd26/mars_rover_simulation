import random

def calculate_drive_command(lidar_data: list) -> dict:
    """
    Continuous Reactive Navigation Engine.
    Uses a weighted danger-field approach to steer while maintaining momentum.
    """
    if not lidar_data:
        return {"throttle": 0.0, "steering": 0.0}

    # 1. Setup danger zones
    # We define danger inversely proportional to distance for objects within 10 meters
    DANGER_THRESHOLD_DIST = 10.0
    left_danger = 0.0
    right_danger = 0.0
    center_danger = 0.0
    
    for r in lidar_data:
        if r['hit'] and r['distance'] < DANGER_THRESHOLD_DIST:
            # Danger increases as we get closer to the object
            danger_val = (DANGER_THRESHOLD_DIST - r['distance'])
            
            # Weighted by angle position (Front 180 degree sweep)
            angle = r['angle']
            if angle < -15 and angle >= -90:
                left_danger += danger_val
            elif angle > 15 and angle <= 90:
                right_danger += danger_val
            elif abs(angle) <= 15:
                center_danger += danger_val * 2.0 # Center is the most critical vector
            # We ignore objects behind us for forward navigation

    max_danger = max(left_danger, center_danger, right_danger)

    # 2. Decision Logic: Continuous Momentum
    throttle = 1.0  # Always try to move forward
    steering = 0.0

    if max_danger > 0:
        # Obstacle detected! Slow down slightly to handle the turn
        throttle = 0.6
        
        if center_danger > left_danger and center_danger > right_danger:
            # Head-on collision imminent!
            # Pick the side with less overall danger to escape
            if left_danger < right_danger:
                steering = -1.0 # Steer Left
            else:
                steering = 1.0  # Steer Right
            
            # If it's extremely close, stop and pivot harder
            if center_danger > (DANGER_THRESHOLD_DIST * 0.8):
                throttle = 0.0 # Pivot in place
        
        elif left_danger > right_danger:
            # Danger on the left, steer right
            steering = 1.0
        else:
            # Danger on the right, steer left
            steering = -1.0
    
    # Optional: Small random meander if completely clear to make it look 'alive'
    elif random.random() > 0.98:
        steering = random.uniform(-0.1, 0.1)

    return {"throttle": throttle, "steering": steering}
