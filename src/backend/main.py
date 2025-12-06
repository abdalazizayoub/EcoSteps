from fastapi import FastAPI
import sqlite3
from weather import get_latest_weather_data

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post('/fetch_weather')
async def fetch_weather():
    try:
        data = get_latest_weather_data()
        
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