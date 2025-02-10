import json
import psycopg2
import os
# from dbconnection.secretManager import getSecret
# from dbconnection.secretArn import getArn

def connect():
    try:
        # Obtener el ARN del secreto
        # secret_name = getArn()

        # # Obtener las credenciales de la base de datos desde AWS Secrets Manager
        # secret_value = getSecret(os.environ['AWS_REGION'], secret_name)



        # Parsear el secreto como JSON
        # credentials = json.loads(secret_value)

        # Conexión a la base de datos
        conn = psycopg2.connect(
            dbname='datalakeprd',
            user='masteradmin',
            password='J|7FG1lBX,QAI3ud',
            host='qarespond-int-respondio-auroradbinstance-lvealsayg0mo.cfrypzdu8hoe.us-west-2.rds.amazonaws.com'
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
        raise e