import json
import psycopg2.extras
import datetime
from lambda_response import lambda_response
from status_http import HttpStatus
from datetime import datetime, timezone, timedelta
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

db_credentials = get_database_credentials()

def is_within_business_hours(timestamp):
    # Convertir el timestamp de milisegundos a datetime en UTC
    message_datetime = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    # Convertir a hora local de Costa Rica (UTC-6)
    costa_rica_tz = timezone(timedelta(hours=-6))
    message_datetime = message_datetime.astimezone(costa_rica_tz)
    
    # Obtener el día de la semana y la hora en Costa Rica
    day_of_week = message_datetime.strftime('%A')  # Ejemplo: 'Monday'
    time_of_day = message_datetime.time()  # Ejemplo: 14:30:00
    
    conn = connect(db_credentials)
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
    assigned_user_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    message_text = data["message"]["message"]["text"]
    channel_id = data["channel"]["id"]
    message_type = data["event_type"]
    message_datatype = data["message"]["message"]["type"]
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    
    data_json = json.dumps(data, ensure_ascii=False)

    
    mark_after_hours = False
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'
    
    message_user = False
    message_workflow = True

    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (
            contact_id, 
            assigned_user_id, 
            message_id, 
            message_classification, 
            message_timestamp, 
            message_type, 
            message_datatype, 
            message_text, 
            channel_id, 
            dl_created_at, 
            dl_modified_at, 
            dl_condition, 
            data_json,
            mark_after_hours, 
            message_user, 
            message_workflow
            )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        contact_id, 
        assigned_user_id, 
        message_id, 
        message_classification, 
        message_timestamp, 
        message_type, 
        message_datatype, 
        message_text, 
        channel_id, 
        dl_created_at, 
        dl_modified_at, 
        dl_condition, 
        data_json,
        mark_after_hours, 
        message_user, 
        message_workflow
        ))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")

def handle_attachment_message(data):
    contact_id = data["contact"]["id"]
    assigned_user_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    channel_id = data["channel"]["id"]
    message_filename = data["message"]["message"]["attachment"]["fileName"]
    message_url = data["message"]["message"]["attachment"]["url"]
    description = data["message"]["message"]["attachment"].get("description", "")
    message_type = data["event_type"]
    
    message_datatype = data["message"]["message"]["attachment"]["type"]

    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    
    data_json = json.dumps(data, ensure_ascii=False)

    
    mark_after_hours = False
    
    message_user = True
    message_workflow = False
    
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, message_filename, message_url, message_text, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours, message_user, message_workflow)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, message_filename, message_url, description, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours, message_user, message_workflow))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    
    
    
    pass

def handle_template_message(data):
    contact_id = data["contact"]["id"]
    assigned_user_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    template_id = data["message"]["message"]["template"]["id"]
    channel_id = data["channel"]["id"]
    message_type = data["event_type"]
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    message_datatype = data["message"]["message"]["type"]
    
    data_json = json.dumps(data, ensure_ascii=False)

    
    mark_after_hours = False
    
    message_user = False
    message_workflow = True
    
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, template_id, channel_id, data_json, dl_created_at, dl_modified_at, dl_condition, mark_after_hours, message_user, message_workflow)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, template_id, channel_id, data_json, dl_created_at, dl_modified_at, dl_condition, mark_after_hours, message_user, message_workflow))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    

def handle_quick_reply_message(data):
    contact_id = data["contact"]["id"]
    assigned_user_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    timestamp = data["message"]["timestamp"]
    message_type = data["event_type"]
    title = data["message"]["message"]["title"]
    message_replies = json.dumps(data["message"]["message"]["replies"], ensure_ascii=False)
    channel_id = data["channel"]["id"]
    message_datatype = data["message"]["message"]["type"]
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    data_json = json.dumps(data, ensure_ascii=False)
    
    mark_after_hours = False
    
    message_user = False
    message_workflow = True
    
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True

    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, message_text, message_replies, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours, message_user, message_workflow)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, title, message_replies,  channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours, message_user, message_workflow))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")
    

def handle_email_message(data):
    
    contact_id = data["contact"]["id"]
    assigned_user_id = data["contact"]["assignee"]["id"]
    message_id = data["message"]["messageId"]
    message_classification = data["message"]["message"]["type"]
    message_subject = data["message"]["message"]["subject"]
    timestamp = data["message"]["timestamp"]
    channel_id = data["channel"]["id"]
    message_type = data["event_type"]
    message_datatype = data["message"]["message"]["type"]
    
    message_text = data["message"]["message"]["message"]
    
    attachments = data["message"]["message"].get("attachments", [])

    if attachments:
        message_datatype = [attachment["type"] for attachment in attachments]
        message_filename = [attachment["fileName"] for attachment in attachments]
        message_url = [attachment["url"] for attachment in attachments]
    else: 
        message_datatype = data["message"]["message"]["type"]
        message_filename = []
        message_url = []
    
    
    # Convertir el timestamp de milisegundos a segundos y luego a datetime
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    data_json = json.dumps(data, ensure_ascii=False)
    
    mark_after_hours = False
    within_business_hours = is_within_business_hours(timestamp)
    
    if not within_business_hours:
        mark_after_hours = True
    
    dl_created_at = datetime.now().isoformat()
    dl_modified_at = datetime.now().isoformat()
    dl_condition = 'Active'
    
    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.messages (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, message_subject, message_text, message_filename, message_url, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, assigned_user_id, message_id, message_classification, message_timestamp, message_type, message_datatype, message_subject, message_text, message_filename, message_url, channel_id, dl_created_at, dl_modified_at, dl_condition, data_json, mark_after_hours))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")


    

def handle_update_conversation(data):
    timestamp = data["message"]["timestamp"]
    contact_id = str(data["contact"]["id"])
    
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    dl_modified_at = datetime.now().isoformat()
    
    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    update_query = """
        UPDATE respond_io.conversation
        SET dl_modified_at = %s,
            time_last_mess_out_wf = %s
        WHERE contact_id = %s
        AND conversation_status = 'open'
    """
    cursor.execute(update_query, (dl_modified_at, message_timestamp, contact_id))
    
        
    if cursor.rowcount == 0:
        print(f"No se encontró una conversación abierta para el contacto con ID {contact_id}")
    else:
        print("Datos actualizados correctamente en la tabla respond_io.conversation")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos actualizados correctamente en la tabla respond_io.conversation")


def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    message_handlers = {
        'text': handle_text_message,
        'attachment': handle_attachment_message,
        'whatsapp_template': handle_template_message,
        'quick_reply': handle_quick_reply_message,
        'email': handle_email_message
    }

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message

            message_type = data.get("message").get("message").get("type")
            
            
            if not message_type or message_type == 'None':
                print("No se ha recibido el tipo de mensaje")
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Message type is required"})
            
            handler = message_handlers.get(message_type)
            if handler:
                handler(data)
                handle_update_conversation(data)
            else:
                print(f"Tipo de mensaje no soportado: {message_type}")
                return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Unsupported message type"})
            
        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response