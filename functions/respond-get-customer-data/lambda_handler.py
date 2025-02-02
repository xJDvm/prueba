import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus

def lambda_handler(event, context):
    print(event)

    try:
        # Obtener los parámetros de la consulta
        query_params = event.get('queryStringParameters', {})  # Usar un diccionario vacío por defecto

        # Asignar un valor predeterminado si query_params está vacío o es None
        if not query_params or query_params == 'None':
            customer_identification = '0303422291'  # Valor predeterminado
        else:
            # Obtener el customer_identification de los parámetros de la consulta
            customer_identification = query_params.get('customer_identification')
            if not customer_identification:
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Customer identification is required"})

        try:
            # Conexión a la base de datos
            conn = connect()
            print("Conexión a la base de datos exitosa")
        except Exception as e:
            print('Error en la conexión a la base de datos')
            print(e)
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Database connection failed"})

        # Crear un cursor
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            # Usar un parámetro en la consulta SQL para obtener datos del cliente
            cursor.execute("SELECT * FROM temporal.clients WHERE client_identification_number = %s", (customer_identification,))
            print('Consulta ejecutada exitosamente')

            rows = cursor.fetchall()

            customer_data = []
            for row in rows:
                customer_info = dict(row)

                # Consulta adicional para obtener el client_type
                client_type_id = customer_info['client_type']
                print(f"Client type ID: {client_type_id}")
                cursor.execute("SELECT client_type FROM temporal.client_types WHERE client_types_code = %s", (client_type_id,))
                client_type_row = cursor.fetchone()
                if client_type_row:
                    customer_info['client_type'] = client_type_row['client_type']

                customer_data.append(customer_info)

            print(json.dumps(customer_data, indent=2, ensure_ascii=False))  # Imprimir datos transformados en formato JSON

        except Exception as e:
            print('Error en la consulta')
            print(e)
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})
        finally:
            cursor.close()
            conn.close()

        # Construir la respuesta
        response_body = {
            "customer_data": customer_data
        }

        # Retornar la respuesta
        return lambda_response(HttpStatus.OK, response_body)

    except Exception as e:
        # Manejar el error
        print(e)
        return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})