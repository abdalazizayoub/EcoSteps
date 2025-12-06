# EcoSteps
EcoSteps - Sustainable Transportation Tracker
🎯 Project Vision
EcoSteps is a gamified sustainability application that encourages users to make eco-friendly transportation choices by tracking CO2 emissions, rewarding green travel, and providing real-time environmental data.

The the frontend was built using Lovaable
To try echo steps use our deployed site here "https://ecoosteps.lovable.app/"
🏗️ Architecture Overview
The application consists of a Python FastAPI backend that integrates multiple external services and manages a local SQLite database for data persistence.
Core Components

 Application Logic Flow
1. Route Analysis & Comparison
Endpoint: POST /route
What it does:

Takes origin and destination locations from the user
Queries Google Maps API for three transportation modes: driving, transit, and bicycling
Returns distance and duration for each mode
Calculates CO2 emissions for each option using Gemini AI
Ranks routes by environmental impact and assigns XP rewards

The Ranking System:

Lowest CO2 emissions → 10 XP (typically bicycling)
Second lowest → 5 XP (typically public transit)
Highest emissions → 1 XP (typically driving)

2. Environmental Context Integration
Endpoint: POST /fetch_weather
What it does:

Retrieves current weather conditions (temperature, humidity, precipitation)
Fetches European Air Quality Index (AQI) data
Stores hourly environmental data in the database
Provides users with context for their travel decisions

3. CO2 Emission Calculation
How it works:

Gemini estimates the CO2 emission calculation based on the transportation mode and the distance from the starting to the final destination

Gemini AI processes the calculation with structured JSON output

