import json
import psycopg2
import os
from dbconnection.secretManager import getSecret
from dbconnection.secretArn import getArn

def connect(country):
    # Obtener las credenciales de la base de datos desde AWS Secrets Manager

    secret_name = getArn(country)

    credentials = json.loads(getSecret(os.environ['AWS_REGION'], secret_name))

    print(credentials)

    # Conexión a la base de datos
    conn = psycopg2.connect(
        dbname=credentials['dbname'],
        user=credentials['username'],
        password=credentials['password'],
        host=credentials['host']
    )

    return conn