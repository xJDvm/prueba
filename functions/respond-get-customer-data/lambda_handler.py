import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus
from utils.send_emails import send_email

def lambda_handler(event, context):
    # print(event)

    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]

            client_identification = data.get("client_identification")
            
            print(client_identification)
            
            if not client_identification or client_identification == 'None':
                client_identification = '0303422291'  # Valor predeterminado
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Customer identification is required"})

            try:

                # Asignar un valor predeterminado si query_params está vacío o es None

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
                    cursor.execute("SELECT * FROM respond_io.clients WHERE client_identification_number = %s", (client_identification,))
                    print('Consulta ejecutada exitosamente')

                    rows = cursor.fetchall()

                    customer_data = []
                    for row in rows:
                        customer_info = dict(row)

                        # Consulta adicional para obtener el client_type
                        client_type_id = customer_info['client_type']
                        print(f"Client type ID: {client_type_id}")
                        cursor.execute("SELECT client_type FROM respond_io.client_types WHERE client_types_code = %s", (client_type_id,))
                        client_type_row = cursor.fetchone()
                        if client_type_row:
                            customer_info['client_type'] = client_type_row['client_type']

                        customer_data.append(customer_info)

                    # print(json.dumps(customer_data, indent=2, ensure_ascii=False))  # Imprimir datos transformados en formato JSON

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
                sender = 'respond@arqintelix.biz'
                recipient = 'jvaldes@intelix.biz'
                subject = "Prueba data Cliente"
                body_text = "Prueba data Cliente"
                body_html = f"""
                    <html>
                    <head></head>
                    <body>
                    <h1>Notificación de mensaje pendiente</h1>
                    <p>Cliente: {response_body}</p>
                    <p>Por favor, revise el mensaje pendiente en la plataforma Respond.io.</p>
                    </body>
                    </html>
                """

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html)
                # Retornar la respuesta
                return lambda_response(HttpStatus.OK, response_body)

            except Exception as e:
                # Manejar el error
                # print(e)
                return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})




        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR')
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response