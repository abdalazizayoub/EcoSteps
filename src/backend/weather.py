import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import numpy as np

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def get_latest_weather_data():
    """
    Fetches the latest hourly weather and air quality data for a specific location,
    processes it into DataFrames, and returns the latest available entry.
    """
    LATITUDE = 48.3064
    LONGITUDE = 14.2861
    TIMEZONE = "Europe/Berlin"
    current = pd.Timestamp.utcnow().floor('H') # Floor to the hour for matching

    # --- 1. Fetch Air Quality (AQI) Data ---
    aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    aq_params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ["european_aqi"],
        "timezone": TIMEZONE,
    }
    aq_responses = openmeteo.weather_api(aq_url, params=aq_params)
    aq_response = aq_responses[0]
    
    hourly_aq = aq_response.Hourly()
    hourly_european_aqi = hourly_aq.Variables(0).ValuesAsNumpy()
    
    aq_timestamps = pd.date_range(
        start = pd.to_datetime(hourly_aq.Time(), unit="s", utc=True),
        end = pd.to_datetime(hourly_aq.TimeEnd(), unit="s", utc=True),
        freq = pd.Timedelta(seconds=hourly_aq.Interval()),
        inclusive = "left"
    ).tz_convert('UTC').floor('H') # Ensure UTC and hourly frequency for consistent merging

    aq_dataframe = pd.DataFrame({"date": aq_timestamps, "european_aqi": hourly_european_aqi})
    
    # --- 2. Fetch Detailed Weather Data (From your original script) ---
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        # Only include variables needed for hourly insert (daily is omitted for simplicity)
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "precipitation"],
        "timezone": TIMEZONE,
    }
    weather_responses = openmeteo.weather_api(weather_url, params=weather_params)
    weather_response = weather_responses[0]

    hourly_w = weather_response.Hourly()
    # Note: Variable indices must match the requested hourly list above
    hourly_temperature_2m = hourly_w.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly_w.Variables(1).ValuesAsNumpy()
    hourly_precipitation_probability = hourly_w.Variables(2).ValuesAsNumpy()
    hourly_precipitation = hourly_w.Variables(3).ValuesAsNumpy()

    w_timestamps = pd.date_range(
        start = pd.to_datetime(hourly_w.Time(), unit="s", utc=True),
        end = pd.to_datetime(hourly_w.TimeEnd(), unit="s", utc=True),
        freq = pd.Timedelta(seconds=hourly_w.Interval()),
        inclusive = "left"
    ).tz_convert('UTC').floor('H') # Ensure UTC and hourly frequency

    w_dataframe = pd.DataFrame({
        "date": w_timestamps,
        "temperature_2m": hourly_temperature_2m,
        "relative_humidity_2m": hourly_relative_humidity_2m,
        "precipitation_probability": hourly_precipitation_probability,
        "precipitation": hourly_precipitation
    })
    
    # --- 3. Merge and Extract Latest Data ---
    
    # Merge weather and AQI dataframes on the date column
    # Use outer merge just in case timestamps don't perfectly align (though they usually do)
    merged_df = pd.merge(w_dataframe, aq_dataframe, on='date', how='outer')

    # Filter for the latest completed hourly entry
    past_hours = merged_df[merged_df["date"] <= current].dropna(subset=['temperature_2m', 'european_aqi'])
    
    if past_hours.empty:
        raise Exception("No current or past hourly data available.")

    latest_entry = past_hours.iloc[-1]
    
    # Return the dictionary expected by main.py
    return {
        "timestamp": latest_entry["date"].isoformat(),
        "temperature_2m": float(latest_entry["temperature_2m"]),
        "relative_humidity_2m": float(latest_entry["relative_humidity_2m"]),
        "precipitation_probability": float(latest_entry["precipitation_probability"]),
        "precipitation": float(latest_entry["precipitation"]),
        "aqi": float(latest_entry["european_aqi"])
    }