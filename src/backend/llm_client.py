# llm_client.py

from google import genai
from google.genai import types
import os
import dotenv
import json # <-- Import the json library

dotenv.load_dotenv()
key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=key)

def co2_emissions(distance_meters: float, mode: str):
    distance_km = distance_meters / 1000.0

    system_prompt = (
        "You are an assistant that calculates CO2 emissions for trips.\n"
        "Never guess or estimate distance. ONLY use the provided value 'distance_km'.\n"
        "Use these emission factors:\n"
        "- car: 0.192 kg per km\n"
        "- public_transport: 0.041 kg per km\n"
        "- bicycle: 0 kg per km\n"
        "Return **ONLY** valid JSON in this format, with **NO** surrounding text or markdown (no triple backticks):\n"
        "{'co2_kg': number, 'mode': string, 'distance_km': number}"
    )

    user_prompt = (
        f"Calculate emissions for a trip using mode='{mode}' and distance_km={distance_km}."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
        contents=user_prompt
    )
    
    # --- FIX 1: Clean and Parse the JSON ---
    response_text = response.text.strip()
    # Attempt to remove common markdown wrapper if the model still includes it
    if response_text.startswith("```json"):
        response_text = response_text.strip("```json\n").strip("```")

    try:
        # Parse the cleaned string into a Python dictionary
        data = json.loads(response_text.replace("'", "\"")) # Replace single quotes with double quotes for valid JSON
        # Extract the required float value
        return data.get('co2_kg') 
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        print(f"Raw response text: {response.text}")
        # Return a safe default value on failure
        return 0.0