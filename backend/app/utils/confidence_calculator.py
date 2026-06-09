
def calculate_forecast_confidence(
    temperature: float,
    humidity: int,
    forecast_type: str = "hourly"
) -> float:
    """
    Calculate a realistic forecast confidence score (percentage) based on
    weather conditions and forecast scope.
    """
    # Base confidence score depending on the forecast horizon
    if forecast_type == "hourly":
        base_confidence = 97.5
    elif forecast_type == "daily":
        base_confidence = 94.0
    else: # weekly
        base_confidence = 89.0
        
    # Penalty for extreme temperatures (where load is volatile due to HVAC/heaters)
    temp_penalty = 0.0
    if temperature > 38.0:
        temp_penalty = (temperature - 38.0) * 0.4
    elif temperature < 10.0:
        temp_penalty = (10.0 - temperature) * 0.3
        
    # Penalty for high humidity anomalies
    humidity_penalty = 0.0
    if humidity > 85:
        humidity_penalty = (humidity - 85) * 0.1
        
    # Apply penalties
    confidence = base_confidence - temp_penalty - humidity_penalty
    
    # Bound the confidence between 75% and 99.5%
    return round(max(75.0, min(99.5, confidence)), 1)
