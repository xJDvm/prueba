import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus

def lambda_handler(event, context):
    print(event)

    try:
        # Obtener los parámetros de la consulta
        query_params = event.get('queryStringParameters')
        if query_params is None or query_params == 'None':
            query_params = {}

        country = event.get('pathParameters', {}).get('country')

        print('pais: ', country)

        # Obtener el nombre del cliente de los parámetros de la consulta
        customer_name = query_params.get('customer_name', '')

        try:
            # Conexión a la base de datos
            conn = connect(country)
            print(conn)
        except Exception as e:
            print('error en la conexión a la base de datos')
            print(e)
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Database connection failed"})

        # Crear un cursor
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            # Usar un parámetro en la consulta SQL para obtener datos del cliente
            cursor.execute("SELECT * FROM global.clients WHERE client_identification_number = '3006101757'")
            print('consulta exitosa')

            rows = cursor.fetchall()

            customer_data = []
            for row in rows:
                customer_info = dict(row)

                # Consulta adicional para obtener el client_type
                client_type_id = customer_info['client_type']
                print(client_type_id)
                cursor.execute("SELECT client_type FROM global.client_types WHERE client_types_code = %s", (client_type_id,))
                client_type_row = cursor.fetchone()
                if client_type_row:
                    customer_info['client_type'] = client_type_row['client_type']

                customer_data.append(customer_info)

            print(json.dumps(customer_data, indent=2, ensure_ascii=False))  # Imprimir datos transformados en formato JSON

        except Exception as e:
            print('error en la consulta')
            print(e)
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})
        finally:
            cursor.close()
            conn.close()

        # Construir la respuesta
        response_body = {
            "message": "Customer data retrieved successfully",
            "customer_name": customer_name,
            "customer_data": customer_data
        }

        # Convertir la respuesta en JSON
        json_response_body = json.dumps(response_body, ensure_ascii=False)

        # Retornar la respuesta
        return lambda_response(HttpStatus.OK, json_response_body)

    except Exception as e:
        # Manejar el error
        print(e)
        return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

    pass