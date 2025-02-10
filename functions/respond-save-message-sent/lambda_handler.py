import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus

def handle_text_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    timestamp = data["message"]["timestamp"]
    text_message = data["message"]["message"]["text"]
    channel_id = data["channel"]["id"]
    message_type = data["message"]["message"]["type"]

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, timestamp, message_type, text_message, channel_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, timestamp, message_type, text_message, channel_id))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")

def handle_attachment_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    timestamp = data["message"]["timestamp"]
    channel_id = data["channel"]["id"]
    filename = data["message"]["message"]["attachment"]["fileName"]
    url = data["message"]["message"]["attachment"]["url"]
    description = data["message"]["message"]["attachment"].get("description", "")
    message_type = data["message"]["message"]["attachment"]["type"]
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, timestamp, message_type, filename, url, text_message, channel_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, timestamp, message_type, filename, url, description, channel_id))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    
    
    
    pass

def handle_template_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    timestamp = data["message"]["timestamp"]
    template_id = data["message"]["message"]["template"]["id"]
    channel_id = data["channel"]["id"]
    message_type = data["message"]["message"]["type"]

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, timestamp, message_type, template_id, channel_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, timestamp, message_type, template_id, channel_id))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    
    
    
    pass

def handle_quick_reply_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    timestamp = data["message"]["timestamp"]
    message_type = data["message"]["message"]["type"]
    title = data["message"]["message"]["title"]
    replies = json.dumps(data["message"]["message"]["replies"])
    channel_id = data["channel"]["id"]
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, timestamp, message_type, title, replies, channel_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, timestamp, message_type, title, replies,  channel_id))
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
        'whatsapp_template': handle_template_message,
        'quick_reply': handle_quick_reply_message,
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