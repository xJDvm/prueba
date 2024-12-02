import json
import psycopg2
from dbconnection.dbconnection import connect
from queries.getdata import generate_query
from datetime import datetime
from lambda_response import lambda_response
from status_http import HttpStatus

def lambda_handler(event, context):

    print(event)

    try:

        # Obtener el cuerpo de la solicitud
        body = event.get('body', {})

        # Obtener el nombre del cliente de la solicitud
        customer_name = body.get('customer_name', '')

        # Obtener la conexión a la base de datos
        # connection = get_postgres_connection()

        # Realizar la consulta a la base de datos
        # cursor = connection.cursor()
        # cursor.execute("SELECT * FROM customers WHERE name = %s", (customer_name,))
        # customer_data = cursor.fetchone()

        # Cerrar el cursor y la conexión
        # cursor.close()
        # connection.close()

        # Construir la respuesta
        response_body = {
            "message": "Customer data retrieved successfully",
            "customer_name": customer_name,
            # "customer_data": customer_data
        }

        # Retornar la respuesta
        return lambda_response(HttpStatus.OK, response_body)

    except Exception as e:
        # Manejar el error
        return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

    pass