# Intelligent Dual-Axis Solar Tracking System (Industry 4.0)

A Real-Time, Location-Specific Intelligent Dual-Axis Solar Tracking System optimized for sustainable energy architectures under Industry 4.0.

## Core Features

- **Precise Solar Geometry Engine**: Highly accurate mathematical models calculating Solar Declination, Zenith, and Azimuth Angles continuously.
- **Winter Optimization Mode**: Actively senses temperature < 2°C and snow to tilt panels ≥ 60° for snow shedding, locking azimuth to preserve motor energy and extending tracking frequency.
- **AI Predictive Enhancement**: Uses Machine Learning (Random Forest) irradiance predictions and constrained optimization algorithms. If predicted irradiance gain is less than motor energy cost, tracking is intelligently paused.
- **IoT Edge Simulation**: A modular `edge_controller.py` script mimics an ESP32 microcontroller pinging sensors and updating cloud telemetry.
- **Simulation Dashboard**: A Streamlit application rendering tracker angles over 24-hours comparing Fixed, Single-Axis, and Dual-Axis setups, including carbon offset (`CO₂_saved`) and efficiency metric calculations.

## Installation & Setup

1. Create a Python Virtual Environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```
4. Run Edge Controller Simulation:
   ```bash
   python iot_edge/edge_controller.py
   ```

## Architecture Layout
- `core/`: Math logic (`solar_model.py`), Tracker Logic (`tracking_logic.py`), AI (`ai_predictive.py`).
- `iot_edge/`: Simulated microcontroller for Cloud integration.
- `simulation/`: Day simulation logic extracting data for fixed/single/dual setups.
- `dashboard/`: User-facing interactive dashboard (`app.py`).
