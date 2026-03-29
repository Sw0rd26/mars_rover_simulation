def extract_features(lidar_data: list) -> dict:
    """
    Extracts numerical features from JSON LiDAR array.
    """
    features = {
        'left_danger': 0.0,
        'center_danger': 0.0,
        'right_danger': 0.0,
        'max_danger': 0.0
    }
    
    DANGER_THRESHOLD_DIST = 8.0
    
    for r in lidar_data:
        if r['hit'] and r['distance'] < DANGER_THRESHOLD_DIST:
            danger_val = (DANGER_THRESHOLD_DIST - r['distance'])
            
            if r['angle'] < -15:
                features['left_danger'] += danger_val
            elif r['angle'] > 15:
                features['right_danger'] += danger_val
            else:
                features['center_danger'] += danger_val * 1.5 
                
    features['max_danger'] = max(features['left_danger'], features['center_danger'], features['right_danger'])
    return features
