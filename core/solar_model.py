import math
from datetime import datetime, timedelta

def equation_of_time(n: int) -> float:
    """Calculate Equation of Time (EoT) in minutes given day of year n."""
    B = math.radians((n - 1) * 360.0 / 365.0)
    eot = 229.18 * (
        0.000075 
        + 0.001868 * math.cos(B) 
        - 0.032077 * math.sin(B) 
        - 0.014615 * math.cos(2 * B) 
        - 0.040849 * math.sin(2 * B)
    )
    return eot

def get_day_of_year(dt: datetime) -> int:
    return dt.timetuple().tm_yday

def solar_declination(n: int) -> float:
    """Calculate Solar Declination (δ) in degrees."""
    angle_rad = math.radians((360.0 / 365.0) * (284 + n))
    return 23.45 * math.sin(angle_rad)

def standard_meridian(utc_offset_hours: float) -> float:
    """Calculate standard meridian longitude."""
    return utc_offset_hours * 15.0

def solar_time_correction(longitude: float, utc_offset_hours: float, n: int) -> float:
    """Calculate Time Correction (TC) in minutes."""
    lambda_std = standard_meridian(utc_offset_hours)
    eot = equation_of_time(n)
    # Longitude is positive for East, negative for West.
    # TC = 4 * (longitude - lambda_std) + EoT  (if longitude is standard convention)
    # The prompt formula: 4(λ_std - λ) + EoT often depends on sign conventions.
    # Let's use the formula: TC = 4(Longitude - Lst) + EoT
    tc = 4.0 * (longitude - lambda_std) + eot
    return tc

def calculate_solar_time(dt_local: datetime, longitude: float, utc_offset_hours: float) -> float:
    """Calculate Solar Time in fractional hours."""
    n = get_day_of_year(dt_local)
    tc_minutes = solar_time_correction(longitude, utc_offset_hours, n)
    local_time_hours = dt_local.hour + dt_local.minute / 60.0 + dt_local.second / 3600.0
    solar_time_hours = local_time_hours + tc_minutes / 60.0
    
    # Wrap to 0-24
    solar_time_hours = solar_time_hours % 24
    return solar_time_hours

def hour_angle(solar_time_hours: float) -> float:
    """Calculate Hour Angle (H) in degrees."""
    # H = 15°(SolarTime − 12)
    return 15.0 * (solar_time_hours - 12.0)

def zenith_and_azimuth(latitude: float, declination: float, hour_angle_deg: float) -> tuple[float, float]:
    """Calculate Solar Zenith Angle (θz) and Azimuth Angle (γ) in degrees."""
    lat_rad = math.radians(latitude)
    dec_rad = math.radians(declination)
    h_rad = math.radians(hour_angle_deg)

    # Zenith Angle
    cos_theta_z = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(h_rad)
    cos_theta_z = max(-1.0, min(1.0, cos_theta_z)) # Clamping to avoid domain errors
    zenith_rad = math.acos(cos_theta_z)
    zenith_deg = math.degrees(zenith_rad)

    # Azimuth Angle
    # cos(γ) = (sin(δ) cos(φ) - cos(δ) sin(φ) cos(H)) / sin(θz)
    # Alternatively: cos(γ) = (sin(α)sin(φ) - sin(δ)) / (cos(α)cos(φ)) where α = 90 - θz
    elevation_rad = math.pi / 2 - zenith_rad
    
    sin_theta_z = math.sin(zenith_rad)
    if sin_theta_z > 0.001:
        cos_gamma = (math.sin(dec_rad) * math.cos(lat_rad) - math.cos(dec_rad) * math.sin(lat_rad) * math.cos(h_rad)) / sin_theta_z
        cos_gamma = max(-1.0, min(1.0, cos_gamma))
        azimuth_rad = math.acos(cos_gamma)
        azimuth_deg = math.degrees(azimuth_rad)
        
        # Adjust based on hour angle for true azimuth (relative to South or North depending on convention)
        if hour_angle_deg > 0:
            azimuth_deg = 360 - azimuth_deg
    else:
        # Sun is at zenith
        azimuth_deg = 0.0

    return zenith_deg, azimuth_deg

def get_target_angles(dt_local: datetime, latitude: float, longitude: float, utc_offset_hours: float) -> dict:
    """Compute optimal tilt (β) and azimuth (γ) for dual-axis tracking."""
    n = get_day_of_year(dt_local)
    declination = solar_declination(n)
    solar_time = calculate_solar_time(dt_local, longitude, utc_offset_hours)
    h_deg = hour_angle(solar_time)
    
    zenith, azimuth = zenith_and_azimuth(latitude, declination, h_deg)
    
    # Tilt angle (β) = Zenith angle (θz) for optimal tracking
    tilt = zenith
    
    return {
        "tilt": tilt,
        "azimuth": azimuth,
        "zenith": zenith,
        "declination": declination,
        "solar_time": solar_time,
        "hour_angle": h_deg
    }
