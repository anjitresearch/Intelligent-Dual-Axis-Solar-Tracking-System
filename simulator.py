import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from core.solar_model import get_target_angles
from core.tracking_logic import DualAxisTracker

def simulate_day(date_obj: datetime, lat: float, lon: float, utc_offset: float, 
                 temps: list[float], snow_detected: bool, 
                 fixed_tilt: float = 30.0, fixed_azimuth: float = 180.0):
    """
    Simulates solar tracking over a single 24-hour period.
    Returns a DataFrame with minute-by-minute (or 10-minute) tracking and energy data.
    """
    tracker = DualAxisTracker(lat, lon, utc_offset)
    
    records = []
    
    # Simulate every 10 minutes
    start_of_day = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0)
    
    for minutes in range(0, 24 * 60, 10):
        current_time = start_of_day + timedelta(minutes=minutes)
        hour_frac = current_time.hour + current_time.minute / 60.0
        
        # Interpolate temperature (assuming temps is a list of 24 hourly values)
        hour_int = int(current_time.hour)
        temp_now = temps[hour_int] if hour_int < len(temps) else temps[-1]
        
        # 1. Optimal Geometry
        optimal = get_target_angles(current_time, lat, lon, utc_offset)
        zenith = optimal["zenith"]
        
        # Base Irradiance Model (simplified clear sky)
        # Max 1000 W/m^2 at zenith 0
        if zenith < 90:
            irradiance_direct = 1000 * np.cos(np.radians(zenith))
        else:
            irradiance_direct = 0.0
            
        # 2. Dual-Axis Tracking Logic (includes Winter Mode)
        tracker_state = tracker.update(current_time, temp_now, snow_detected, 10)
        dual_tilt = tracker_state["tilt"]
        dual_azimuth = tracker_state["azimuth"]
        is_winter = tracker_state["winter_mode"]
        
        # Calculate received power for Dual-Axis
        # Ideal dual-axis always faces the sun perfectly when not in winter/stow mode
        # If in winter mode or stow, we must calculate the cosine loss.
        dual_inc_cos = max(0.0, np.cos(np.radians(optimal["tilt"] - dual_tilt)) * np.cos(np.radians(optimal["azimuth"] - dual_azimuth)))
        dual_power = irradiance_direct * dual_inc_cos
        
        # 3. Fixed-Axis Logic
        fixed_inc_cos = max(0.0, np.cos(np.radians(optimal["tilt"] - fixed_tilt)) * np.cos(np.radians(optimal["azimuth"] - fixed_azimuth)))
        fixed_power = irradiance_direct * fixed_inc_cos
        
        # 4. Single-Axis Logic (Vertical axis tracking: optimal azimuth, fixed tilt)
        single_inc_cos = max(0.0, np.cos(np.radians(optimal["tilt"] - fixed_tilt)))
        single_power = irradiance_direct * single_inc_cos
        
        records.append({
            "Time": current_time,
            "Hour": hour_frac,
            "Zenith": zenith,
            "Opt_Tilt": optimal["tilt"],
            "Opt_Azimuth": optimal["azimuth"],
            "Dual_Tilt": dual_tilt,
            "Dual_Azimuth": dual_azimuth,
            "Is_Winter": is_winter,
            "Temp_C": temp_now,
            "Irradiance_W_m2": irradiance_direct,
            "Power_Dual": dual_power,
            "Power_Single": single_power,
            "Power_Fixed": fixed_power
        })
        
    df = pd.DataFrame(records)
    return df
