import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from respondfunctions.send_respond_request import close_conversations
from datetime import datetime
from botocore.exceptions import ClientError

def lambda_handler(event, context):

    try:
        conn = connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        conversation_query = """
            SELECT contact_id
            FROM respond_io.conversation
            WHERE conversation_status = 'open'
        """
        cursor.execute(conversation_query)
        conversations = cursor.fetchall()

        for conversation in conversations:
            contact_id = conversation['contact_id']
            try:
                close_conversations(contact_id)
                print(f"Conversación cerrada para contact_id: {contact_id}")
            except Exception as e:
                print(f"Error al cerrar la conversación para contact_id {contact_id}: {e}")

        conn.commit()
        cursor.close()

    except Exception as e:
        print(f'ERROR: {e}')
        print("Error al ejecutar la lambda")