import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from respondfunctions.send_emails import send_email
from respondfunctions.emailbody_asesor import build_html_asesor
from respondfunctions.emailbody_store import build_html_store
from respondfunctions.request_contact import request_contact_info
from datetime import datetime, timedelta


def get_photos_after_time(conn, current_time):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Convertir la hora actual a timestamp
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        ten_minutes_after = current_time_dt + timedelta(minutes=10)
        ten_minutes_after_timestamp = int(ten_minutes_after.timestamp() * 1000)
        
        select_query = """
        SELECT url 
        FROM respond_io.messages 
        WHERE message_classification = 'message.received' 
        AND message_type = 'image' 
        AND timestamp_column > %s
        """
        
        cursor.execute(select_query, (ten_minutes_after_timestamp,))
        rows = cursor.fetchall()
        
        photos = [row['url'] for row in rows]
        photos_array = ",".join(photos)
        
        cursor.close()
        return photos_array

    except Exception as ex:
        print(f"Error: {ex}")
        return ""

def get_messages_after_time(conn, current_time):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Convertir la hora actual a timestamp
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        ten_minutes_after = current_time_dt + timedelta(minutes=10)
        ten_minutes_after_timestamp = int(ten_minutes_after.timestamp() * 1000)
        
        select_query = """
        SELECT text_message 
        FROM respond_io.messages 
        WHERE message_classification = 'message.received' 
        AND message_type = 'text' 
        AND timestamp_column > %s
        """
        
        cursor.execute(select_query, (ten_minutes_after_timestamp,))
        rows = cursor.fetchall()
        
        messages = [row['text_message'] for row in rows]
        messages_array = " - ".join(messages)
        
        cursor.close()
        return messages_array

    except Exception as ex:
        print(f"Error: {ex}")
        return ""

def lambda_handler(event, context):

    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]: 
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
            contact_name = data["firstName"] + " " + data["lastName"]
            contact_id = data["id"]
            
            
            if data["store"]:
                
                conn = connect()
                current_time = data["time"]
                messages_array = get_messages_after_time(conn, current_time)
                photos_array = get_photos_after_time(conn, current_time)
                print(photos_array)
                print(messages_array)
                conn.close()
                
                store = data["store"]
                client_name = contact_name
                client_email = data["client_email"]
                client_phone = data["client_phone"]
                client_identification = data["client_identification"]
                last_message_time = data["time"]
                incoming_messages = messages_array
                incoming_photos = photos_array
                
                e = {
                    'store': store,
                    'clientName': client_name,
                    'clientEmail': client_email,
                    'clientPhone': client_phone,
                    'clientId': contact_id,
                    'clientCedula': client_identification,
                    'lastMessageTime': last_message_time,
                    'incomingMessages': incoming_messages,
                    'incomingPhotos': incoming_photos
                }
                
                body = build_html_store(e)
                print(body)
                
                sender = 'respond@arqintelix.biz'
                recipient = 'jvaldes@intelix.biz'
                subject = "Respond.io | Notificación de mensaje pendiente"
                body_text = "Respond.io | Notificación de mensaje pendiente"
                body_html = body

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html)            
            
            else:
                agent_value = data["agent"]
                document_value = data["client_identification"]

                print("Agente:", agent_value)
                print("Cedula:", document_value)
                
                body = build_html_asesor(contact_name, contact_id, agent_value, document_value)
            
                print(body)
                                
                sender = 'respond@arqintelix.biz'
                recipient = 'jvaldes@intelix.biz'
                subject = "Respond.io | Notificación de mensaje pendiente"
                body_text = "Respond.io | Notificación de mensaje pendiente"
                body_html = build_html_asesor(contact_name, contact_id, agent_value, document_value)

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html)
                

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR')
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response