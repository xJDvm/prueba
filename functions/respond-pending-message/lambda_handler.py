import json
import psycopg2.extras
from respondfunctions.emailbody_asesor import build_html
from datetime import datetime, timedelta, timezone
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

event_log = {
    "event": "respond-pending-message",
    "event_data": {
        "conversations": [],
        "mark_30min": "",
        "mark_60min": "",
        "contact_identification": "",
        "developer_message": "",
        "status_first_email": "",
        "status_second_email": ""
    },
    "querys": {
        "conversation_query": ""
    }
}

def lambda_handler(event, context):

    try:
        message_time = datetime.now()
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        conversation_query = """
            SELECT c.contact_id, c.time_last_mess_in, c.time_last_mess_out, c.mark_30min, c.mark_60min, ct.contact_identification, ct.contact_identification, ct.assignee_firstname || ' ' || ct.assignee_lastname as assignee_name, ct.agent_email, ct.assignee_email, ct.leader_email, ct.contact_firstname || ' ' || COALESCE(ct.contact_lastname, '') as full_name,
            (EXTRACT(EPOCH FROM (now() at time zone 'UTC'- c.time_last_mess_in)) / 60)::int AS difference_min
            FROM respond_io.conversation c
            JOIN respond_io.contacts ct ON c.contact_id = ct.contact_id
            WHERE c.conversation_status 
            = 'open' and
            ( (c.mark_30min = false and (EXTRACT(EPOCH FROM (now() at time zone 'UTC'- c.time_last_mess_in)) / 60)::int >= 3/*tiempo de priemera marca de 30 minutos*/)
            or (c.mark_60min = false and (EXTRACT(EPOCH FROM (now() at time zone 'UTC'- c.time_last_mess_in)) / 60)::int >= 6/*tiempo de segunda marca de 60 minutos*/)  );
        """
        cursor.execute(conversation_query)
        conversations = cursor.fetchall()
        
        event_log["querys"]["conversation_query"] = conversation_query

        for conversation in conversations:
            try:

                # Obtener datos de la conversación
                time_last_mess_in = conversation['time_last_mess_in']
                time_last_mess_out = conversation['time_last_mess_out'] if conversation['time_last_mess_out'] else None
                mark_30min = conversation['mark_30min']
                mark_60min = conversation['mark_60min']
                difference_min = conversation['difference_min']
                
                # Valida si el asesor ya respondió
                # Guardar los datos de la conversación en el event_log
                event_log["event_data"]["conversations"] = str(conversation)
                event_log["event_data"]["contact_identification"] = conversation['contact_identification']
                event_log["event_data"]["mark_30min"] = mark_30min
                event_log["event_data"]["mark_60min"] = mark_60min   
                if not time_last_mess_in or time_last_mess_out:
                    event_log["event_data"]["developer_message"] = "El asesor ya respondió"
                    print(json.dumps({'EventLog': event_log}))
                    continue
                
                # Conversion de time_last_mess_in a objeto datetime
                last_hour = time_last_mess_in
                # Convertir a hora local de Costa Rica (UTC-6)
                costa_rica_tz = timezone(timedelta(hours=-6))
                last_hour = last_hour.astimezone(costa_rica_tz)
                # Formatear para eliminar el indicador de zona horaria
                last_hour = last_hour.strftime('%Y-%m-%d %H:%M:%S')
    
    
                # Obtener data del contacto y el agente
                contact_identification = conversation['contact_identification'] if conversation['contact_identification'] else 'Sin cédula'
                assignee_name = conversation['assignee_name'] if conversation['assignee_name'] else 'Equipo de Respond.io'
                full_name = conversation['full_name']
                assignee_email = conversation['assignee_email'] if conversation['assignee_email'] else backup_email
                leader_email = conversation['leader_email'] if conversation['leader_email'] else None
                bcc = support_emails

                # Calcular el tiempo desde el último mensaje recibido
                time_since_last_in = (message_time - time_last_mess_in).total_seconds() / 60
                
                # Verificar si el tiempo desde el último mensaje recibido supera los límites establecidos
                if time_since_last_in >= first_time_notification and not mark_30min:
                    subject = f"Respond.io | Notificación de mensaje pendiente (30 min) - {full_name}"
                    body_html = build_html(assignee_name, conversation['contact_id'], full_name, contact_identification, last_hour)
                    # Enviar correo electrónico de notificación de 30 minutos
                    try:
                        cursor.execute("UPDATE respond_io.conversation SET mark_30min = %s WHERE contact_id = %s", (True, conversation['contact_id']))
                        conn.commit()           
                        send_email([assignee_email], subject, subject, body_html, [leader_email] if leader_email else None, bcc)
                        event_log["event_data"]["status_first_email"] = "Correo de 30 min enviado"
                    except ClientError as e:
                        print("Error sending email: ", e.response['Error']['Message'])

                # Verificar si el tiempo desde el último mensaje recibido supera los límites establecidos
                elif time_since_last_in >= second_time_notification and not mark_60min:
                    subject = f"Respond.io | Notificación de mensaje pendiente (60 min) - {full_name}"
                    body_html = build_html(assignee_name, conversation['contact_id'], full_name, contact_identification, last_hour)
                    # Enviar correo electrónico de notificación de 60 minutos
                    try:
                        cursor.execute("UPDATE respond_io.conversation SET mark_60min = %s WHERE contact_id = %s", (True, conversation['contact_id']))
                        conn.commit()               
                        send_email([assignee_email], subject, subject, body_html, [leader_email] if leader_email else None, bcc)
                        event_log["event_data"]["status_second_email"] = "Correo de 60 min enviado"
                    except ClientError as e:
                        print("Error sending email: ", e.response['Error']['Message'])
                
                        
                print(json.dumps({'EventLog': event_log}))
                        
            except Exception as e:
                print(f'ERROR: {e}')
                print(json.dumps({'ErrorRespond': str(e), 'Conversation': conversation}))

        cursor.close()


    except Exception as e:
        print(f'ERROR: {e}')
        print(json.dumps({'ErrorRespond': str(e)}))