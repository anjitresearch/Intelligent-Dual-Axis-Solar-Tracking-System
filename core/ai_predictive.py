import numpy as np
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime

class IrradiancePredictor:
    def __init__(self):
        # We use a Random Forest model as a baseline for AI prediction
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        
    def train(self, history_data: dict):
        """
        Train the model using historical weather and irradiance data.
        history_data: dictionary containing 'features' and 'target'
        features: [[hour, temp, cloud_cover, humidity, zenith_angle], ...]
        target: [irradiance, ...]
        """
        X = np.array(history_data['features'])
        y = np.array(history_data['target'])
        self.model.fit(X, y)
        self.is_trained = True
        
    def train_synthetic(self):
        """Applies a synthetic dataset to train the model for simulation."""
        np.random.seed(42)
        # Synthetic data: 1000 samples
        hours = np.random.uniform(0, 24, 1000)
        temps = np.random.uniform(-10, 45, 1000)
        cloud_covers = np.random.uniform(0, 100, 1000)
        zenith = np.random.uniform(0, 180, 1000)
        
        # Fake irradiance function: peaks at noon (hour 12), lower with high cloud cover, 0 if zenith > 90
        irradiance = np.where(
            zenith > 90, 0,
            1000 * np.cos(np.radians(zenith)) * (1 - (cloud_covers / 100.0) * 0.7)
        )
        irradiance = np.maximum(0, irradiance + np.random.normal(0, 20, 1000))
        
        features = np.column_stack((hours, temps, cloud_covers, zenith))
        target = irradiance
        
        self.model.fit(features, target)
        self.is_trained = True

    def predict(self, hour: float, temp: float, cloud_cover: float, zenith_angle: float) -> float:
        if not self.is_trained:
            self.train_synthetic() # Auto-train on synthetic if not trained
        return self.model.predict([[hour, temp, cloud_cover, zenith_angle]])[0]


class PredictiveController:
    def __init__(self, motor_energy_cost_wh: float = 2.5):
        self.predictor = IrradiancePredictor()
        self.motor_energy_cost = motor_energy_cost_wh
        
    def optimize_movement(self, current_tilt: float, target_tilt: float, 
                          current_azimuth: float, target_azimuth: float,
                          dt_local: datetime, temp: float, cloud_cover: float, 
                          zenith: float, area: float = 2.0, efficiency: float = 0.2) -> dict:
        """
        Decides whether to move the tracker based on AI-predicted irradiance and constrained optimization.
        """
        hour = dt_local.hour + dt_local.minute / 60.0
        
        # Predict irradiance (W/m^2) based on weather
        predicted_irradiance = self.predictor.predict(hour, temp, cloud_cover, zenith)
        
        # Calculate expected power (W) with and without moving
        # Simplifying assumption: power = irradiance * area * efficiency * cos(incidence_angle)
        # Moving perfectly means incidence_angle = 0 -> cos(0) = 1
        # Not moving means incidence_angle is the difference between current and target angles.
        
        expected_power_moving = predicted_irradiance * area * efficiency
        
        tilt_diff_rad = np.radians(target_tilt - current_tilt)
        az_diff_rad = np.radians(target_azimuth - current_azimuth)
        
        # Approximate incidence angle cosine using dot product of normal vectors
        # For simplicity, if we don't move, we suffer a cosine loss
        incidence_cos = max(0.0, np.cos(tilt_diff_rad) * np.cos(az_diff_rad))
        expected_power_staying = predicted_irradiance * area * efficiency * incidence_cos
        
        # Expected energy gain in roughly 10 minutes (0.166 hours)
        time_delta_h = 10.0 / 60.0 
        expected_energy_moving_wh = expected_power_moving * time_delta_h
        expected_energy_staying_wh = expected_power_staying * time_delta_h
        
        energy_gain = expected_energy_moving_wh - expected_energy_staying_wh
        
        # If the energy gain by moving is LESS than what the motors will consume, do not move.
        if energy_gain <= self.motor_energy_cost:
            return {
                "move_approved": False,
                "reason": f"Energy gain ({energy_gain:.2f} Wh) < motor cost ({self.motor_energy_cost} Wh)",
                "predicted_irradiance": predicted_irradiance,
                "final_tilt": current_tilt,
                "final_azimuth": current_azimuth
            }
            
        return {
            "move_approved": True,
            "reason": f"Energy gain ({energy_gain:.2f} Wh) justifies move",
            "predicted_irradiance": predicted_irradiance,
            "final_tilt": target_tilt,
            "final_azimuth": target_azimuth
        }

