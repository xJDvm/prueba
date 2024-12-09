from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus

def lambda_handler(event, context):

    print(event)

    try:
        # Obtener el cuerpo de la solicitud
        body = event.get('body', {})

        country = event.get('pathParameters', {}).get('country')

        print('pais: ', country)

        # Obtener el nombre del cliente de la solicitud
        customer_name = body.get('customer_name', '')

        try:
            # Conexión a la base de datos
            conn = connect(country)
            print(conn)
        except Exception as e:
            print('error en la conexión a la base de datos')
            print(e)
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": "Database connection failed"})

        # Crear un cursor
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM config.users WHERE name = 'jvaldes'")
            print('consulta exitosa')

            customer_data = cursor.fetchall()

            # Cerrar el cursor
            cursor.close()
            # Cerrar la conexión
            conn.close()

            print(customer_data)
        except Exception as e:
            print('error en la consulta')
            print(e)
            cursor.close()
            conn.close()
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

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