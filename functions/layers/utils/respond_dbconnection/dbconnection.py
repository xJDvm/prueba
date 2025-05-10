import json
import psycopg2
import os

def connect(credentials):
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect(
            dbname=credentials['dbname'],
            user=credentials['username'],
            password=credentials['password'],
            host=credentials['host']
        )
        print("Database connection successful")  # Debug

        return conn

    except json.JSONDecodeError as e:
        print(f"Error parsing secret as JSON: {e}")
        raise ValueError("Secret is not a valid JSON")
    except KeyError as e:
        print(f"Missing key in credentials: {e}")
        raise ValueError(f"Missing key in credentials: {e}")
    except Exception as e:
        print(f"Error in database connection: {e}")
        print(json.dumps({'ErrorRespond': str(e)}))
        raise e