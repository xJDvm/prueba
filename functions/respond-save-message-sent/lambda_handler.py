import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus
from datetime import datetime, timezone, timedelta

def is_within_business_hours(timestamp):
    # Convertir el timestamp de milisegundos a datetime en UTC
    message_datetime = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    # Convertir a hora local de Costa Rica (UTC-6)
    costa_rica_tz = timezone(timedelta(hours=-6))
    message_datetime = message_datetime.astimezone(costa_rica_tz)
    
    # Obtener el día de la semana y la hora en Costa Rica
    day_of_week = message_datetime.strftime('%A')  # Ejemplo: 'Monday'
    time_of_day = message_datetime.time()  # Ejemplo: 14:30:00
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    select_query = """
        SELECT *
        FROM respond_io.business_hours
        WHERE day_of_week = %s
        AND is_closed = FALSE
        AND %s BETWEEN open_time AND close_time
    """
    
    cursor.execute(select_query, (day_of_week, time_of_day))
    row = cursor.fetchone()
    
    if row:
        print("Mensaje dentro de horario")
        return True
    else:
        print("Mensaje fuera de horario")
        return False

def handle_text_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    text_message = data["message"]["message"]["text"]
    channel_id = data["channel"]["id"]
    message_type = data["event_type"]
    message_datatype = data["message"]["message"]["type"]
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    
    data_json = json.dumps(data)
    
    mark_after_hours = False
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (
            contact_id, 
            assignado_id, 
            message_id, 
            message_classification, 
            message_timestamp, 
            message_type, 
            message_datatype, 
            text_message, 
            channel_id, 
            dl_created_at, 
            dl_modified_at, 
            dl_condition, 
            data_json,
            mark_after_hours
            )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        contact_id, 
        assignado_id, 
        message_id, 
        message_classification, 
        message_timestamp, 
        message_type, 
        message_datatype, 
        text_message, 
        channel_id, 
        dl_created_at, 
        dl_modified_at, 
        dl_condition, 
        data_json,
        mark_after_hours
        ))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")

def handle_attachment_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    channel_id = data["channel"]["id"]
    filename = data["message"]["message"]["attachment"]["fileName"]
    url = data["message"]["message"]["attachment"]["url"]
    description = data["message"]["message"]["attachment"].get("description", "")
    message_type = data["event_type"]
    
    message_datatype = data["message"]["message"]["attachment"]["type"]

    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    
    data_json = json.dumps(data)
    
    mark_after_hours = False
    
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, message_classification, message_timestamp, message_type, message_datatype, filename, url, text_message, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, message_classification, message_timestamp, message_type, message_datatype, filename, url, description, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    
    
    
    pass

def handle_template_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    template_id = data["message"]["message"]["template"]["id"]
    channel_id = data["channel"]["id"]
    message_type = data["event_type"]
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    message_datatype = data["message"]["message"]["type"]
    
    data_json = json.dumps(data)
    
    mark_after_hours = False
    
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, message_classification, message_timestamp, message_type, message_datatype, template_id, channel_id, data_json, dl_created_at, dl_modified_at, dl_condition, mark_after_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, message_classification, message_timestamp, message_type, message_datatype, template_id, channel_id, data_json, dl_created_at, dl_modified_at, dl_condition, mark_after_hours))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    

def handle_quick_reply_message(data):
    contact_id = data["contact"]["id"]
    assignado_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    message_type = data["event_type"]
    title = data["message"]["message"]["title"]
    replies = json.dumps(data["message"]["message"]["replies"])
    channel_id = data["channel"]["id"]
    message_datatype = data["message"]["message"]["type"]
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    data_json = json.dumps(data)
    
    mark_after_hours = False
    
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True

    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assignado_id, message_id, message_classification, message_timestamp, message_type, message_datatype, text_message, replies, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assignado_id, message_id, message_classification, message_timestamp, message_type, message_datatype, title, replies,  channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    

# def handle_update_conversation(data):
#     timestamp = data["message"]["timestamp"]
#     contact_id = str(data["contact"]["id"])
    
#     message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
#     dl_modified_at = datetime.now().isoformat()
    
#     conn = connect()
#     cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     update_query = """
#         UPDATE respond_io.conversation
#         SET dl_modified_at = %s,
#             time_last_mess_out = %s
#         WHERE contact_id = %s
#         AND conversation_status = 'open'
#     """
#     cursor.execute(update_query, (dl_modified_at, message_timestamp, contact_id))
#     conn.commit()
#     cursor.close()
#     conn.close()
#     print("Datos actualizados correctamente en la tabla respond_io.conversation")


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
                # handle_update_conversation(data)
            else:
                print(f"Tipo de mensaje no soportado: {message_type}")
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Unsupported message type"})
            
        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response