def get_latest_weather_data():
    """Fetches the latest AQI and Weather data from Open-Meteo."""
    import openmeteo_requests
    import requests_cache
    from retry_requests import retry
    import pandas as pd
    
    # Setup
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)
    current = pd.Timestamp.utcnow()

    # --- Fetch Air Quality Data ---
    aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    aq_params = {
        "latitude": 48.3064,
        "longitude": 14.2861,
        "hourly": ["european_aqi"], # Only fetch the required variable
        "timezone": "Europe/Berlin",
    }
    aq_responses = openmeteo.weather_api(aq_url, params=aq_params)
    aq_response = aq_responses[0]
    
    hourly_aq = aq_response.Hourly()
    hourly_european_aqi = hourly_aq.Variables(0).ValuesAsNumpy()
    
    aq_timestamps = pd.date_range(
        start = pd.to_datetime(hourly_aq.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly_aq.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly_aq.Interval()),
        inclusive = "left"
    )
    aq_dataframe = pd.DataFrame({"date": aq_timestamps, "european_aqi": hourly_european_aqi})
    latest_aq_entry = aq_dataframe[aq_dataframe["date"] < current].iloc[-1]
    aqi_timestamp, aqi = latest_aq_entry["date"], latest_aq_entry["european_aqi"]


    # --- Fetch Weather Data ---
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": 48.3064,
        "longitude": 14.2861,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "precipitation"],
        "timezone": "Europe/Berlin",
    }
    weather_responses = openmeteo.weather_api(weather_url, params=weather_params)
    weather_response = weather_responses[0]

    hourly_w = weather_response.Hourly()
    # Note: Variable indices match the requested hourly list above (0 to 3)
    hourly_temperature_2m = hourly_w.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly_w.Variables(1).ValuesAsNumpy()
    hourly_precipitation_probability = hourly_w.Variables(2).ValuesAsNumpy()
    hourly_precipitation = hourly_w.Variables(3).ValuesAsNumpy()

    w_timestamps = pd.date_range(
        start = pd.to_datetime(hourly_w.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly_w.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly_w.Interval()),
        inclusive = "left"
    )

    w_dataframe = pd.DataFrame({
        "date": w_timestamps,
        "temperature_2m": hourly_temperature_2m,
        "relative_humidity_2m": hourly_relative_humidity_2m,
        "precipitation_probability": hourly_precipitation_probability,
        "precipitation": hourly_precipitation
    })
    
    latest_w_entry = w_dataframe[w_dataframe["date"] < current].iloc[-1]

    return {
        "timestamp": aqi_timestamp.isoformat(), # Using the AQI timestamp as the main time
        "aqi": float(aqi),
        "temperature_2m": float(latest_w_entry["temperature_2m"]),
        "relative_humidity_2m": float(latest_w_entry["relative_humidity_2m"]),
        "precipitation_probability": float(latest_w_entry["precipitation_probability"]),
        "precipitation": float(latest_w_entry["precipitation"]),
    }