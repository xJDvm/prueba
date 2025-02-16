import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from respondfunctions.send_emails import send_email
from respondfunctions.emailbody_asesor import build_html_asesor
from respondfunctions.emailbody_store import build_html_store
from datetime import datetime, timedelta, timezone


def get_photos_after_time(conn, current_time, contact_id):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        print(f"Current Time: ", current_time)
        
        # Convertir la hora actual a timestamp y ajustarla a UTC (hora de Costa Rica a UTC)
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        costa_rica_tz = timezone(timedelta(hours=-6))  # Costa Rica está en UTC-6
        current_time_dt = current_time_dt.replace(tzinfo=costa_rica_tz)
        current_time_utc = current_time_dt.astimezone(timezone.utc)
        ten_minutes_after = current_time_utc - timedelta(minutes=1)

        print(f"Converted time costa rica: ", costa_rica_tz )

        print(f"Converted time DTC: ", current_time_dt )


        print(f"Converted time UTC: ", current_time_utc )


        print(f"Converted time -1: ", ten_minutes_after )
        
        select_query = """
        SELECT url 
        FROM respond_io.messages 
        WHERE message_type = 'message.received' 
        AND message_datatype = 'image' 
        AND message_timestamp > %s
        AND contact_id = %s
        """
        
        print(cursor.mogrify(select_query, (ten_minutes_after, contact_id)).decode('utf-8'))

        
        cursor.execute(select_query, (ten_minutes_after, contact_id))
        rows = cursor.fetchall()
        
        photos = [row['url'] for row in rows]
        photos_array = ",".join(photos)
        
        cursor.close()
        return photos_array

    except Exception as ex:
        print(f"Error: {ex}")
        return ""

def get_messages_after_time(conn, current_time, contact_id):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        print(f"Current Time: ", current_time)
        
        # Convertir la hora actual a timestamp y ajustarla a UTC (hora de Costa Rica a UTC)
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        costa_rica_tz = timezone(timedelta(hours=-6))  # Costa Rica está en UTC-6
        current_time_dt = current_time_dt.replace(tzinfo=costa_rica_tz)
        current_time_utc = current_time_dt.astimezone(timezone.utc)
        ten_minutes_after = current_time_utc - timedelta(minutes=1)

        print(f"Converted time costa rica: ", costa_rica_tz )

        print(f"Converted time DTC: ", current_time_dt )


        print(f"Converted time UTC: ", current_time_utc )


        print(f"Converted time -1: ", ten_minutes_after )
        
        select_query = """
        SELECT text_message 
        FROM respond_io.messages 
        WHERE message_type = 'message.received' 
        AND message_classification = 'text' 
        AND message_timestamp > %s
        AND contact_id = %s
        """
        
        print(cursor.mogrify(select_query, (ten_minutes_after, contact_id)).decode('utf-8'))
        
        cursor.execute(select_query, (ten_minutes_after, contact_id))
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
            
            # Verificar si el dato 'store' está presente en el cuerpo del mensaje
            if 'store' in data:
                
                conn = connect()
                current_time = data["time"]
                
                print("Hora actual:", current_time)
                messages_array = get_messages_after_time(conn, current_time, contact_id)
                photos_array = get_photos_after_time(conn, current_time, contact_id)
                # print(photos_array)
                # print(messages_array)
                conn.close()
                
                store = data["store"]
                client_name = contact_name
                client_email = data["client_email"]
                client_phone = data["client_phone"]
                client_identification = data["client_identification"]
                last_message_time = data["time"]
                incoming_messages = messages_array
                incoming_photos = photos_array
                
                agent_email = data["agent_email"]
                
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
                # print(body)
                
                sender = 'respond@arqintelix.biz'
                recipient = agent_email
                subject = "Respond.io | Notificación de mensaje pendiente"
                body_text = "Respond.io | Notificación de mensaje pendiente"
                body_html = body

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html)            
            
            else:
                agent_value = data["agent"]
                document_value = data["client_identification"]
                
                store_email = data["store_email"]
                

                print("Agente:", agent_value)
                print("Cedula:", document_value)
                
                body = build_html_asesor(contact_name, contact_id, agent_value, document_value)
            
                print(body)
                                
                sender = 'respond@arqintelix.biz'
                recipient = store_email
                cc = ['projas@intelix.biz', 'jvaldes@intelix.biz']
                subject = "Respond.io | Notificación de mensaje pendiente"
                body_text = "Respond.io | Notificación de mensaje pendiente"
                body_html = build_html_asesor(contact_name, contact_id, agent_value, document_value)

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html, cc_addresses=cc)
                

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR')
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response