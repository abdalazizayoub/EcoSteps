import sqlite3
import os

DB_NAME = 'ecosteps.db'

def connect_db(db_path=DB_NAME):
    """Establishes a connection to the SQLite database."""
    # os.path.abspath is used for clarity, though typically sqlite3.connect 
    # handles relative paths just fine in most environments.
    # We will use the direct name for simplicity as it's in the same directory.
    try:
        conn = sqlite3.connect(db_path, timeout=30) 
        # Set row_factory to sqlite3.Row for dictionary-like access to rows if needed later
        # conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error for path '{db_path}': {e}")
        return None

def create_tables(db_path=DB_NAME):
    """
    Creates all necessary tables for the Ecosteps application if they do not already exist.
    """
    conn = connect_db(db_path) 
    if conn is None:
        print("Could not create tables: Database connection failed.")
        return
        
    cursor = conn.cursor()

    try:
        # --- TABLE 1: users (Must be created first for FOREIGN KEY references) ---
        print("Creating 'users' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                total_XP INTEGER NOT NULL DEFAULT 0
            )
        ''')

        # --- TABLE 2: weather (Used in your main.py's fetch_weather endpoint) ---
        print("Creating 'weather' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE, -- Use TEXT to store the ISO format timestamp
                temperature_2m REAL,
                relative_humidity_2m REAL,
                precipitation_probability REAL,
                precipitation REAL,
                european_aqi REAL
            )
        ''')

        # --- TABLE 3: trips (References 'users' table) ---
        print("Creating 'trips' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                point_A TEXT NOT NULL,
                point_B TEXT NOT NULL,
                distance REAL NOT NULL,
                transport_mode TEXT NOT NULL,
                co2_emissions REAL NOT NULL,
                XP INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # --- TABLE 4: streaks (References 'users' table) ---
        print("Creating 'streaks' table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                current_streak INTEGER NOT NULL,
                longest_streak INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        print("Tables created successfully in 'ecosteps.db'.")
        
    except sqlite3.Error as e:
        print(f"An error occurred during table creation: {e}")
    finally:
        conn.close()

