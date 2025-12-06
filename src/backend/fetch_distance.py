# fetch_distance.py

from dotenv import load_dotenv
import os
import requests
import json
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def fetch_distance(origin: str, destination: str, mode: str):
    """
    Fetch distance and duration for a specific travel mode using Distance Matrix API.
    """
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": origin,
        "destinations": destination,
        "mode": mode,
        "key": GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
        response_json = response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "REQUEST_ERROR", "details": f"Network or HTTP error: {e}"}
    except json.JSONDecodeError:
        return {"status": "ERROR", "details": "Could not decode JSON response."}
    
    try:
        # Check overall API status first
        if response_json.get("status") != "OK":
            return {"status": "API_ERROR", "details": response_json.get("error_message", "Unknown API error.")}
        
        element = response_json["rows"][0]["elements"][0] 

        if element["status"] != "OK":
            return {"status": element["status"], "details": f"Route element failed with status: {element['status']}"}

        return {
            "status": "OK",
            "distance_text": element["distance"]["text"],
            "distance_meters": element["distance"]["value"],
            "duration_text": element["duration"]["text"],
            "duration_seconds": element["duration"]["value"]
        }

    except KeyError as e:
        return {"status": "PARSE_ERROR", "details": f"Missing expected key in response: {e}. Full response: {response_json}"}
    except Exception as e:
        return {"status": "ERROR", "details": str(e)}


def calculate_ranked_rewards(co2_dict: dict):
    """
    Assign rewards based on CO2 emissions.
    Lowest CO2 (non-None/non-zero) → highest reward.
    """
    reward_tiers = [10, 5, 1]  # XP for rank 1, 2, 3

    # 1. Sanitize: Create a list of (mode, co2) tuples for sorting,
    # filtering out any modes where CO2 could not be calculated (value is 0 or None).
    # We treat 0 emissions (like bicycling) as the best possible rank.
    sanitized_for_ranking = []
    
    # Track all modes so we can assign a default 0 reward to failed modes later
    all_modes = set(co2_dict.keys())
    
    for mode, value in co2_dict.items():
        if value is not None and value >= 0:
            sanitized_for_ranking.append((mode, value))

    # 2. Sort modes by CO2 ascending
    # Modes with 0 CO2 (e.g., bicycling) will be ranked first.
    sorted_modes = sorted(sanitized_for_ranking, key=lambda x: x[1])

    rewards = {mode: 0 for mode in all_modes} # Initialize all to 0

    # 3. Assign rewards based on rank in the *successful* list
    for rank, (mode, co2_value) in enumerate(sorted_modes):
        tier_index = min(rank, len(reward_tiers) - 1)
        
        # Ensure only modes with a valid CO2 value (or 0 for eco) get a rank-based reward
        if co2_value >= 0:
            rewards[mode] = reward_tiers[tier_index]
        else:
            # Should not be hit if sanitized list works, but safe fallback
            rewards[mode] = 0

    return rewards