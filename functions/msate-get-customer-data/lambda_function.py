from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus

def lambda_handler(event, context):

    print(event)

    try:

        # Obtener el cuerpo de la solicitud
        body = event.get('body', {})

        # Obtener el nombre del cliente de la solicitud
        customer_name = body.get('customer_name', '')

        # Conexión a la base de datos
        conn = connect(body.get('country'))

        # Crear un cursor
        cursor = conn.cursor()

        # Generar la consulta
        cursor.execute("SELECT * FROM global.clients WHERE name = %s", ("XX",))

        # Obtener los datos
        customer_data = cursor.fetchall()

        # Cerrar el cursor
        cursor.close()
        # Cerrar la conexión
        conn.close()

        print(customer_data)

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