import json
import psycopg2.extras
from respondfunctions.emailbody_asesor import build_html
from datetime import datetime
from botocore.exceptions import ClientError
from int_respond_config import get_respond_config
from int_respond_sendemail import send_email
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

respond_config = json.loads(get_respond_config())
first_time_notification = respond_config["firstNotificationTime"]
second_time_notification = respond_config["secondNotificationTime"]
backup_email = respond_config["backupEmail"]
support_emails = respond_config["supportEmails"]

db_credentials = get_database_credentials()

def lambda_handler(event, context):

    try:
        message_time = datetime.now()
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        conversation_query = """
            SELECT c.contact_id, c.time_last_mess_in, c.time_last_mess_out, c.mark_30min, c.mark_60min,
                    ct.client_identification, ct.assignee_firstname || ' ' || ct.assignee_lastname as assignee_name, ct.asesor_email, ct.assignee_email, ct.lider_email, 
                    ct.firstname || ' ' || ct.lastname as full_name
            FROM respond_io.conversation c
            JOIN respond_io.contacts ct ON c.contact_id = ct.contact_id
            WHERE c.conversation_status = 'open'
        """
        cursor.execute(conversation_query)
        conversations = cursor.fetchall()

        for conversation in conversations:
            try:
                print(f"Conversacion: {conversation}")
                
                time_last_mess_in = conversation['time_last_mess_in']
                if not time_last_mess_in:
                    print("No existe time_last_mess_in, saltando esta conversación.")
                    continue
                time_last_mess_out = conversation['time_last_mess_out'] if conversation['time_last_mess_out'] else None
                mark_30min = conversation['mark_30min']
                mark_60min = conversation['mark_60min']
                
                last_hour = time_last_mess_out if time_last_mess_out else 'No hay mensajes salientes'

                client_identification = conversation['client_identification'] if conversation['client_identification'] else 'Sin cédula'
                assignee_name = conversation['assignee_name'] if conversation['assignee_name'] else 'Equipo de Respond.io'
                full_name = conversation['full_name']
                
                assignee_email = conversation['assignee_email'] if conversation['assignee_email'] else backup_email
                lider_email = conversation['lider_email'] if conversation['lider_email'] else None
                
                bcc = support_emails
                
                time_since_last_in = (message_time - time_last_mess_in).total_seconds() / 60
                
                responded_after_client = time_last_mess_out and time_last_mess_out > time_last_mess_in
                
                print(time_since_last_in)
                
                if time_since_last_in >= first_time_notification and not responded_after_client and not mark_30min:
                    subject = f"Respond.io | Notificación de mensaje pendiente (30 min) - {full_name}"
                    body_html = build_html(assignee_name, conversation['contact_id'], full_name, client_identification, last_hour)
                    
                    try:
                        send_email([assignee_email], subject, subject, body_html, [lider_email] if lider_email else None, bcc)
                        cursor.execute("UPDATE respond_io.conversation SET mark_30min = %s WHERE contact_id = %s", (True, conversation['contact_id']))
                        print(f"Correo de 30 min enviado para contact_id: {conversation['contact_id']}")
                    except ClientError as e:
                        print("Error sending email: ", e.response['Error']['Message'])

                elif time_since_last_in >= second_time_notification and not responded_after_client and not mark_60min:
                    subject = f"Respond.io | Notificación de mensaje pendiente (60 min) - {full_name}"
                    body_html = build_html(assignee_name, conversation['contact_id'], full_name, client_identification, last_hour)
                    
                    try:
                        send_email([assignee_email], subject, subject, body_html, [lider_email] if lider_email else None, bcc)
                        cursor.execute("UPDATE respond_io.conversation SET mark_60min = %s WHERE contact_id = %s", (True, conversation['contact_id']))
                        print(f"Correo de 60 min enviado para contact_id: {conversation['contact_id']}")
                    except ClientError as e:
                        print("Error sending email: ", e.response['Error']['Message'])
                        
            except Exception as e:
                print(f'ERROR: {e}')
                print("Error al ejecutar la lambda")

        conn.commit()
        cursor.close()

    except Exception as e:
        print(f'ERROR: {e}')
        print("Error al ejecutar la lambda")