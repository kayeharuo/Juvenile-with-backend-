import psycopg2
import os
from dotenv import load_dotenv


load_dotenv() 

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS") or os.getenv("DB_PASSWORD"),
            # sslmode="disable"
        )
        return conn
    except psycopg2.OperationalError as e:
        print("Error: Unable to connect to the database.", e)
        return None