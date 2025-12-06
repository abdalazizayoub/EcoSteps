from fastapi import FastAPI
import sqlite3
from weather import get_latest_weather_data
# Assuming your database setup file is named 'database_setup.py'
from database_setup import create_tables 
from fetch_distance import fetch_distance, calculate_ranked_rewards
from llm_client import co2_emissions

from pydantic import BaseModel
from datetime import datetime

class TripData(BaseModel):
    date: datetime
    origin: str
    destination: str
    distance_meters: float
    transport_mode: str
    co2_emissions_kg: float
    xp_gained: int


app = FastAPI()

# --- DATABASE STARTUP EVENT ---
@app.on_event("startup")
async def startup_db_init():
    """
    Function to run when the FastAPI application starts up.
    It ensures the database file and all necessary tables exist.
    """
    print("🚀 Running database startup routine...")
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
    


@app.post("/log_trip")
async def log_trip(trip_data: TripData):
    
    conn = None
    try:
        conn = sqlite3.connect('ecosteps.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trips (user_id, date, point_A, point_B, distance, transport_mode, co2_emissions, XP)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,  # Assuming user_id=1 for simplicity; replace with trip_data.user_id if available,
            str(trip_data.date), 
            trip_data.origin, 
            trip_data.destination, 
            trip_data.distance_meters / 1000.0, # Convert meters to kilometers for storage if that's what your schema intended
            trip_data.transport_mode,
            trip_data.co2_emissions_kg,
            trip_data.xp_gained
        ))

        # 3. Update the user's total XP in the 'users' table
        cursor.execute('''
            UPDATE users
            SET total_XP = total_XP + ?
            WHERE id = 1
        ''', (trip_data.xp_gained, 1))
        
        conn.commit()
        
        return {
            "status": "Trip logged and XP updated successfully",
            "XP_gained": trip_data.xp_gained
        }

    except sqlite3.IntegrityError as e:
        return {'status': 'error', 'message': f'Database integrity error (user_id check?): {e}'}
    except Exception as e:
        print(f"ERROR during log_trip: {e}") 
        return {'status': 'error', 'message': f'Failed to log trip: {e}'}
    finally:
        if conn:
            conn.close()