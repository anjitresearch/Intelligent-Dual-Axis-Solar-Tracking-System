from typing import Dict, Any
from datetime import datetime
from .solar_model import get_target_angles

class DualAxisTracker:
    def __init__(self, latitude: float, longitude: float, utc_offset_hours: float):
        self.latitude = latitude
        self.longitude = longitude
        self.utc_offset = utc_offset_hours
        
        # State
        self.current_tilt = 0.0
        self.current_azimuth = 0.0
        self.last_update_time = None
        self.is_winter_mode_active = False

    def update(self, dt_local: datetime, temperature_c: float, snow_detected: bool, min_update_interval_minutes: int = 10) -> Dict[str, Any]:
        """
        Calculates the new target angles.
        Returns the command for the actuators.
        """
        # Winter mode check
        self.is_winter_mode_active = (temperature_c < 2.0) and snow_detected
        
        # Determine tracking frequency based on mode
        update_interval = 60 if self.is_winter_mode_active else min_update_interval_minutes
        
        # Check if we need to update based on time
        if self.last_update_time is not None:
            time_diff = (dt_local - self.last_update_time).total_seconds() / 60.0
            if time_diff < update_interval:
                return {
                    "action": "skip",
                    "reason": "Update interval not reached",
                    "tilt": self.current_tilt,
                    "azimuth": self.current_azimuth,
                    "winter_mode": self.is_winter_mode_active
                }

        # Calculate optimal angles for current time
        optimal = get_target_angles(dt_local, self.latitude, self.longitude, self.utc_offset)
        target_tilt = optimal["tilt"]
        target_azimuth = optimal["azimuth"]
        
        # Apply Winter Mode Optimization
        if self.is_winter_mode_active:
            # Increase tilt to shed snow (e.g., 65 degrees)
            target_tilt = max(target_tilt, 65.0)
            
            # Pause azimuth movement (keep current)
            target_azimuth = self.current_azimuth
            action = "winter_optimized"
        else:
            action = "track"
        
        # Night mode: if Sun is below horizon (zenith > 90), return to stow position
        if optimal["zenith"] > 90.0:
            target_tilt = 0.0 # Flat to minimize wind resistance at night
            target_azimuth = 180.0 # South facing (or North depending on hemisphere)
            action = "stow"
            
            if self.is_winter_mode_active:
                target_tilt = 65.0 # Keep tilted to shed snow even at night
                
        # Limit constraints (assuming typical actuator limits: Tilt 0-90, Azimuth 0-360)
        target_tilt = max(0.0, min(90.0, target_tilt))
        target_azimuth = target_azimuth % 360.0
        
        # Update state
        self.current_tilt = target_tilt
        self.current_azimuth = target_azimuth
        self.last_update_time = dt_local
        
        return {
            "action": action,
            "tilt": self.current_tilt,
            "azimuth": self.current_azimuth,
            "winter_mode": self.is_winter_mode_active,
            "zenith": optimal["zenith"],
            "solar_time": optimal["solar_time"]
        }
