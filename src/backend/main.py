from fastapi import FastAPI
import sqlite3
from weather import get_latest_weather_data
# Assuming your database setup file is named 'database_setup.py'
from database_setup import create_tables 
from fetch_distance import fetch_distance, calculate_ranked_rewards
from llm_client import co2_emissions


app = FastAPI()

# --- DATABASE STARTUP EVENT ---
@app.on_event("startup")
async def startup_db_init():
    """
    Function to run when the FastAPI application starts up.
    It ensures the database file and all necessary tables exist.
    """
    print("🚀 Running database startup routine...")
    # This will create 'ecosteps.db' and all tables if they don't exist.
    create_tables()
    print("✅ Database connection and table setup confirmed.")

# --- ROUTES ---
@app.get("/")
async def read_root():
    return {"Hello": "World"}



@app.post('/fetch_weather')
async def fetch_weather():
    try:
        data = get_latest_weather_data()
        
        # Note: 'ecosteps.db' is the database name defined in your setup script
        conn = sqlite3.connect('ecosteps.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO weather (date, temperature_2m, relative_humidity_2m, precipitation_probability, precipitation, european_aqi)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data["timestamp"], 
            data["temperature_2m"], 
            data["relative_humidity_2m"], 
            data["precipitation_probability"], 
            data["precipitation"], 
            data["aqi"]
        ))
        
        conn.commit()
        conn.close()
        return {'status': 'Weather data fetched and inserted successfully'}
        
    except Exception as e:
        print(f"ERROR during fetch_weather: {e}") 
        return {'status': 'error', 'message': f'Failed to fetch and insert data: {e}'}


@app.post("/route")
async def get_all_routes(origin: str, destination: str):
    try:
        modes = ["driving", "TRANSIT", "bicycling"]
        results = {}

        # 1. Fetch distances for each mode
        for mode in modes:
            results[mode] = fetch_distance(origin, destination, mode)

        # 2. Compute CO₂ for each mode
        co2_productions = {}
        for mode, data in results.items():
            distance_meters = data.get("distance_meters", 0)
            co2_productions[mode] = float(co2_emissions(distance_meters, mode))

        # 3. Calculate rewards based on CO₂ ranking
        rewards = calculate_ranked_rewards(co2_productions)

        return {
            "origin": origin,
            "destination": destination,
            "routes": results,
            "co2": co2_productions,
            "rewards": rewards
        }
    except Exception as e:
        print(f"ERROR during get_all_routes: {e}")
        return {'status': 'error', 'message': f'Failed to get routes: {e}'}
    
    
