import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from respondfunctions.send_emails import send_email
from respondfunctions.emailbody_asesor import build_html
from lambda_response import lambda_response
from status_http import HttpStatus
from datetime import datetime, timedelta

def lambda_handler(event, context):
    print('Iniciando proceso de notificación de mensaje pendiente')

    try:
        message_time = datetime.now()
        conn = connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        conversation_query = """
            SELECT c.contact_id, c.time_last_mess_in, c.time_last_mess_out, c.mark_30min, c.mark_60min,
                   ct.client_identification, ct.asesor_name, ct.asesor_email, ct.lider_email, 
                   ct.firstname || ' ' || ct.lastname as full_name
            FROM respond_io.conversation c
            JOIN respond_io.contacts ct ON c.contact_id = ct.contact_id
            WHERE c.conversation_status = 'open'
        """
        cursor.execute(conversation_query)
        conversations = cursor.fetchall()

        for conversation in conversations:
            time_last_mess_in = conversation['time_last_mess_in']
            time_last_mess_out = conversation['time_last_mess_out'] if conversation['time_last_mess_out'] else None
            mark_30min = conversation['mark_30min']
            mark_60min = conversation['mark_60min']

            client_identification = conversation['client_identification']
            asesor_name = conversation['asesor_name']
            full_name = conversation['full_name']

            time_since_last_in = (message_time - time_last_mess_in).total_seconds() / 60
            responded_after_client = time_last_mess_out and time_last_mess_out > time_last_mess_in

            if time_since_last_in >= 3 and not responded_after_client and not mark_30min:
                subject = "Respond.io | Notificación de mensaje pendiente (30 min)"
                body_html = build_html(asesor_name, conversation['contact_id'], full_name, client_identification, time_last_mess_out)
                send_email('respond@arqintelix.biz', 'jvaldes@intelix.biz', subject, subject, body_html)

                cursor.execute("UPDATE respond_io.conversation SET mark_30min = %s WHERE contact_id = %s", (True, conversation['contact_id']))
                print(f"Correo de 30 min enviado para contact_id: {conversation['contact_id']}")

            elif time_since_last_in >= 6 and not responded_after_client and not mark_60min:
                subject = "Respond.io | Notificación de mensaje pendiente (60 min)"
                body_html = build_html(asesor_name, conversation['contact_id'], full_name, client_identification, time_last_mess_out)
                send_email('respond@arqintelix.biz', 'jvaldes@intelix.biz', subject, subject, body_html)

                cursor.execute("UPDATE respond_io.conversation SET mark_60min = %s WHERE contact_id = %s", (True, conversation['contact_id']))
                print(f"Correo de 60 min enviado para contact_id: {conversation['contact_id']}")

        conn.commit()
        cursor.close()

    except Exception as e:
        print(f'ERROR: {e}')
        return lambda_response(HttpStatus.BAD_REQUEST, {"error": "Error al ejecutar la lambda"})

    return lambda_response(HttpStatus.OK, {"response": "Correos enviados correctamente"})
