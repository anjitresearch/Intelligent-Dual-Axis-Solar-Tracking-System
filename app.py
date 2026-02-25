import streamlit as st
import pandas as pd
import datetime
import sys
import os

# Add parent dir to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.simulator import simulate_day

st.set_page_config(page_title="Intelligent Solar Tracker Dashboard", layout="wide")

st.title("☀️ Intelligent Dual-Axis Solar Tracking System")
st.markdown("### Location-Specific Tracker with Winter Optimization & Edge AI")

# Sidebar Configuration
st.sidebar.header("Simulation Parameters")

lat = st.sidebar.number_input("Latitude (°)", min_value=-90.0, max_value=90.0, value=35.0)
lon = st.sidebar.number_input("Longitude (°)", min_value=-180.0, max_value=180.0, value=-118.0)
utc_offset = st.sidebar.number_input("UTC Offset (Hours)", min_value=-12.0, max_value=14.0, value=-8.0)
date_input = st.sidebar.date_input("Date", value=datetime.date(2025, 1, 15))

st.sidebar.markdown("---")
st.sidebar.header("Weather Conditions")
avg_temp = st.sidebar.slider("Average Temp (°C)", min_value=-20, max_value=45, value=-5)
temp_profile = [avg_temp] * 24 # Simplified constant temp for simulation
snow_detected = st.sidebar.checkbox("Snow Detected", value=True)

st.sidebar.markdown("---")
st.sidebar.header("Tracker Specs")
panel_area = st.sidebar.number_input("Totale Area (m²)", value=10.0)
efficiency = st.sidebar.slider("Panel Efficiency (%)", 10, 25, 20) / 100.0

if st.sidebar.button("Run Simulation"):
    with st.spinner("Simulating Dual-Axis tracking with Winter Optimization..."):
        # Run Simulation
        df = simulate_day(date_input, lat, lon, utc_offset, temp_profile, snow_detected)
        
        # Adjust power to actual energy based on area and efficiency
        df["Power_Dual_W"] = df["Power_Dual"] * panel_area * efficiency
        df["Power_Single_W"] = df["Power_Single"] * panel_area * efficiency
        df["Power_Fixed_W"] = df["Power_Fixed"] * panel_area * efficiency
        
        st.subheader(f"Tracker Behavior Analysis for {date_input}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Tracker Angle Traces")
            st.line_chart(df.set_index("Hour")[["Dual_Tilt", "Opt_Tilt", "Dual_Azimuth"]])
            st.caption("Note: Dual_Tilt diverges from Opt_Tilt during Winter/Stow Modes (e.g., locked at ≥ 65° for snow).")
            
        with col2:
            st.markdown("### Energy Output Comparison")
            st.line_chart(df.set_index("Hour")[["Power_Dual_W", "Power_Single_W", "Power_Fixed_W"]])

        # Summary Metrics
        st.markdown("---")
        st.header("Sustainability & Energy Modeling")
        
        # Energy integrates power over 10 min intervals (1/6 hour)
        energy_dual = df["Power_Dual_W"].sum() * (10 / 60) / 1000.0  # kWh
        energy_single = df["Power_Single_W"].sum() * (10 / 60) / 1000.0 # kWh
        energy_fixed = df["Power_Fixed_W"].sum() * (10 / 60) / 1000.0 # kWh
        
        gain_vs_fixed = (energy_dual - energy_fixed) / energy_fixed * 100 if energy_fixed > 0 else 0
        gain_vs_single = (energy_dual - energy_single) / energy_single * 100 if energy_single > 0 else 0
        
        # Carbon saving approx: 0.4 kg CO2 per kWh
        co2_saved = energy_dual * 0.4
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Dual-Axis Energy", f"{energy_dual:.2f} kWh")
        m2.metric("Fixed-Axis Energy", f"{energy_fixed:.2f} kWh", f"+{gain_vs_fixed:.1f}% gain")
        m3.metric("Single-Axis Energy", f"{energy_single:.2f} kWh", f"+{gain_vs_single:.1f}% gain")
        m4.metric("CO₂ Mitigated", f"{co2_saved:.2f} kg")
        
        st.markdown(f"**Status:** Winter Mode triggered: `{(df['Is_Winter'] == True).any()}`")
        if (df['Is_Winter'] == True).any():
            st.success("❄️ Winter Optimization Active: Tilt increased to shed snow, azimuth locked to save actuator energy.")
            
else:
    st.info("Configure the parameters in the sidebar and click 'Run Simulation'.")
