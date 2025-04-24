import json
import psycopg2.extras
import re
from datetime import datetime, timedelta, timezone
from respondfunctions.emailbody_asesor import build_html_asesor
from respondfunctions.emailbody_store import build_html_store
from int_respond_sendemail import send_email
from int_respond_config import get_respond_config
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

respond_config = json.loads(get_respond_config())
backup_email = respond_config["backupEmail"]
support_emails = respond_config["supportEmails"]

db_credentials = get_database_credentials()

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None


def get_contact_info(store, conn):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Obtener store_emails
        print(cursor.mogrify("SELECT email FROM respond_io.store_notifications WHERE store_name = %s AND team in ('Ventas Empresas', 'Cotizaciones')", (store,)).decode('utf-8'))
        cursor.execute("SELECT email FROM respond_io.store_notifications WHERE store_name = %s AND team in ('Ventas Empresas', 'Cotizaciones')", (store,))
        store_emails = [row['email'] for row in cursor.fetchall()]
        
        print(f"store_emails: {store_emails}")
        
        cursor.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        store_emails = []
    
    return json.dumps({"store_emails": store_emails})

def get_photos_after_time(conn, current_time, contact_id):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        
        # Convertir la hora actual a timestamp y ajustarla a UTC (hora de Costa Rica a UTC)
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        costa_rica_tz = timezone(timedelta(hours=-6))  # Costa Rica está en UTC-6
        current_time_dt = current_time_dt.replace(tzinfo=costa_rica_tz)
        current_time_utc = current_time_dt.astimezone(timezone.utc)
        ten_minutes_after = current_time_utc - timedelta(minutes=1)
        
        select_query = """
        SELECT message_url 
        FROM respond_io.messages 
        WHERE message_type = 'message.received' 
        AND message_datatype = 'image' 
        AND message_timestamp > %s
        AND contact_id = %s
        """
        
        print(cursor.mogrify(select_query, (ten_minutes_after, contact_id)).decode('utf-8'))
        cursor.execute(select_query, (ten_minutes_after, contact_id))
        rows = cursor.fetchall()
        
        print(f"Fotos encontradas: {rows}")
        
        photos = [row['message_url'] for row in rows]
        photos_array = ",".join(photos)
        
        cursor.close()
        return photos_array

    except Exception as ex:
        print(f"Error: {ex}")
        return ""

def get_messages_after_time(conn, current_time, contact_id):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Parsear la hora recibida y asignar la zona horaria de Costa Rica
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        costa_rica_tz = timezone(timedelta(hours=-6))  # Costa Rica está en UTC-6
        current_time_dt = current_time_dt.replace(tzinfo=costa_rica_tz)

        # Convertir la hora a UTC
        current_time_utc = current_time_dt.astimezone(timezone.utc)

        # Restar 1 minuto para calcular ten_minutes_after
        ten_minutes_after = current_time_utc - timedelta(minutes=1)
        
        print(f"Ten minutes after: {ten_minutes_after}")

        select_query = """
        SELECT message_text 
        FROM respond_io.messages 
        WHERE message_type = 'message.received' 
        AND message_classification = 'text' 
        AND message_timestamp > %s
        AND contact_id = %s
        ORDER BY message_timestamp DESC
        """
            
        print(cursor.mogrify(select_query, (ten_minutes_after, contact_id)).decode('utf-8'))
        cursor.execute(select_query, (ten_minutes_after, contact_id))
        rows = cursor.fetchall()
        
        print(f"Mensajes encontrados: {rows}")
        
        messages = [row['message_text'] for row in rows]
        messages_array = ",".join(messages)
        
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
            data = message
            contact_name = data["firstName"] + " " + data["lastName"]
            contact_id = data["id"]

            print(data)
            
            # Verificar si el dato 'store' está presente en el cuerpo del mensaje
            if 'store' in data:
                
                store = data["store"]
                
                conn = connect(db_credentials)
                current_time = data["time"]
                
                contact_info = get_contact_info(store, conn)
                messages_array = get_messages_after_time(conn, current_time, contact_id)
                photos_array = get_photos_after_time(conn, current_time, contact_id)
                
                store_emails = json.loads(contact_info)["store_emails"]
                
                
                conn.close()
                
                client_name = contact_name
                client_email = data["client_email"] if data.get("client_email") not in [None, 'null'] else 'Sin correo'
                client_phone = data["client_phone"]
                client_identification = data["client_identification"] if data.get("client_identification") not in [None, 'null'] else 'Sin cédula'
                last_message_time = data["time"]
                incoming_messages = messages_array
                incoming_photos = photos_array
                
                lider_email = data["lider_email"] if data["lider_email"] else backup_email
                
                print(data)
                
                
                
                
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
                
                print(f"recipient: ", store_emails )
                
                recipient = [email for email in store_emails if is_valid_email(email)]
                if not recipient:
                    recipient = backup_email
                    print("No valid store emails found, using default recipient.")
                    print(recipient)
                cc = [lider_email] if is_valid_email(lider_email) else []
                bcc = support_emails
                subject = "Respond.io | Notificación de mensaje fuera de horario"
                body_text = "Respond.io | Notificación de mensaje fuera de horario"
                body_html = body
                
                if not all([recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(recipient, subject, body_text, body_html, cc, bcc)  
                
            
            else:
                agent_value = data["agent"]
                document_value = data["client_identification"]
                
                asesor_email = data["asesor_email"] if data['asesor_email'] else backup_email
                

                
                body = build_html_asesor(contact_name, contact_id, agent_value, document_value)
            
                                
                recipient = [email for email in [asesor_email] if is_valid_email(email)]
                if not recipient:
                    recipient = backup_email
                    print("No valid asesor email found, using default recipient.")
                    print(recipient)
                cc = []
                bcc = support_emails
                subject = "Respond.io | Notificación de mensaje fuera de horario"
                body_text = "Respond.io | Notificación de mensaje fuera de horario"
                body_html = build_html_asesor(contact_name, contact_id, agent_value, document_value)

                if not all([recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(recipient, subject, body_text, body_html, cc, bcc)
                

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR')
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response