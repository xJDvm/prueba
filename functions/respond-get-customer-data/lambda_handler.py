import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus
from utils.send_emails import send_email

def fetch_client_data(cursor, client_identification):
    """Obtiene los datos del cliente y su tipo desde la base de datos."""
    cursor.execute("SELECT * FROM respond_io.clients WHERE client_identification_number = %s", (client_identification,))
    rows = cursor.fetchall()

    customer_data = []
    for row in rows:
        customer_info = dict(row)
        client_type_id = customer_info['client_type']
        
        cursor.execute("SELECT client_type FROM respond_io.client_types WHERE client_types_code = %s", (client_type_id,))
        client_type_row = cursor.fetchone()
        if client_type_row:
            customer_info['client_type'] = client_type_row['client_type']
        
        customer_data.append(customer_info)
    
    return customer_data

def send_customer_email(customer_data):
    """Envía un correo electrónico con los datos del cliente."""
    sender = 'respond@arqintelix.biz'
    recipient = 'jvaldes@intelix.biz'
    subject = "Prueba data Cliente"
    body_text = "Prueba data Cliente"
    body_html = f"""
        <html>
        <head></head>
        <body>
        <h1>Notificación de mensaje pendiente</h1>
        <p>Cliente: {json.dumps(customer_data, indent=2, ensure_ascii=False)}</p>
        <p>Por favor, revise el mensaje pendiente en la plataforma Respond.io.</p>
        </body>
        </html>
    """
    
    if not all([sender, recipient, subject, body_text, body_html]):
        raise ValueError("Missing email parameters")
    
    send_email(sender, recipient, subject, body_text, body_html)

def process_record(record):
    """Procesa un registro individual de SQS."""
    try:
        body = json.loads(record["body"])
        message = json.loads(body["Message"])
        data = message["detail"]
        
        client_identification = data.get("client_identification")
        if not client_identification or client_identification == 'None':
            return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Customer identification is required"})

        conn = connect()
        print("Conexión a la base de datos exitosa")
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            customer_data = fetch_client_data(cursor, client_identification)
            print(json.dumps(customer_data, indent=2, ensure_ascii=False))

            send_customer_email(customer_data)
            return lambda_response(HttpStatus.OK, {"customer_data": customer_data})

        except Exception as e:
            print('Error en la consulta:', e)
            return lambda_response(HttpStatus.INTERNAL_SERVER_ERROR, {"error": str(e)})

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print('Error procesando el registro:', e)
        return {"itemIdentifier": record['messageId']}

def lambda_handler(event, context):
    print(event)
    batch_item_failures = []

    for record in event["Records"]:
        result = process_record(record)
        if "itemIdentifier" in result:
            batch_item_failures.append(result)

    return {"batchItemFailures": batch_item_failures}