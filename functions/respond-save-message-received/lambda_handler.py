import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus

def handle_text_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["event_type"]
    timestamp = data["message"]["timestamp"]
    text_message = data["message"]["message"]["text"]
    channel_id = data["channel"]["id"]
    message_type = data["message"]["message"]["type"]
    
    dl_created_at = datetime.datetime.now().isoformat()
    dl_modified_at = datetime.datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, message_classification, timestamp, message_type, text_message, channel_id, dl_created_at, dl_modified_at, dl_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, message_classification, timestamp, message_type, text_message, channel_id, dl_created_at, dl_modified_at, dl_condition))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")

def handle_attachment_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["event_type"]
    timestamp = data["message"]["timestamp"]
    channel_id = data["channel"]["id"]
    filename = data["message"]["message"]["attachment"]["fileName"]
    url = data["message"]["message"]["attachment"]["url"]
    description = data["message"]["message"]["attachment"].get("description", "")
    message_type = data["message"]["message"]["attachment"]["type"]
    
    dl_created_at = datetime.datetime.now().isoformat()
    dl_modified_at = datetime.datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, message_classification, timestamp, message_type, filename, url, text_message, channel_id, dl_created_at, dl_modified_at, dl_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, message_classification, timestamp, message_type, filename, url, description, channel_id, dl_created_at, dl_modified_at, dl_condition))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    
    
    
    pass

def handle_location_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["event_type"]
    timestamp = data["message"]["timestamp"]
    channel_id = data["channel"]["id"]
    message_type = data["message"]["message"]["type"]
    latitude = data["message"]["message"]["latitude"]
    longitude = data["message"]["message"]["longitude"]
    address = data["message"]["message"]["address"]
    
    dl_created_at = datetime.datetime.now().isoformat()
    dl_modified_at = datetime.datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, message_classification, timestamp, message_type, latitude, longitude, address, channel_id, dl_created_at, dl_modified_at, dl_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, message_classification, timestamp, message_type, latitude, longitude, address, channel_id, dl_created_at, dl_modified_at, dl_condition))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    
    pass

def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    message_handlers = {
        'text': handle_text_message,
        'attachment': handle_attachment_message,
        'location': handle_location_message
    }

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]

            message_type = data.get("message").get("message").get("type")
            
            
            if not message_type or message_type == 'None':
                print("No se ha recibido el tipo de mensaje")
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Message type is required"})
            
            handler = message_handlers.get(message_type)
            if handler:
                handler(data)
            else:
                print(f"Tipo de mensaje no soportado: {message_type}")
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Unsupported message type"})
            
        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response