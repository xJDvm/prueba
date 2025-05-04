import psycopg2.extras
import json
from datetime import datetime,timedelta
from respondfunctions.send_respond_request import close_conversations
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials
from int_respond_token import get_respond_token
from int_respond_config import get_respond_config

db_credentials = get_database_credentials()
api_token = get_respond_token()
respond_config = json.loads(get_respond_config())



def close_conversation_manually(contact_id):
    """Cierra una conversación manualmente en la base de datos si la API no la puede cerrar."""
    try:
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Obtener conversación abierta
        cursor.execute("""
            SELECT conversation_cod, conversation_opened_at
            FROM respond_io.conversation
            WHERE contact_id = %s AND conversation_status = 'open'
        """, (contact_id,))
        
        conversation = cursor.fetchone()
        if not conversation:
            print(f"No se encontró conversación abierta para contact_id: {contact_id}")
            return

        conversation_cod = conversation['conversation_cod']
        conversation_opened_at = conversation['conversation_opened_at']
        closed_time = datetime.now().isoformat()
        dl_modified_at = datetime.now().isoformat()

        # Actualizar la conversación en la base de datos
        cursor.execute("""
            UPDATE respond_io.conversation
            SET closed_time = %s, close_by_id = 'api', conversation_status = 'closed', dl_modified_at = %s
            WHERE conversation_cod = %s
        """, (closed_time, dl_modified_at, conversation_cod))

        cursor.execute("""
            UPDATE respond_io.messages
            SET conversation_cod = %s, dl_modified_at = %s
            WHERE contact_id = %s AND message_timestamp BETWEEN %s AND %s
        """, (conversation_cod, dl_modified_at, contact_id, conversation_opened_at, closed_time))

        conn.commit()
        cursor.close()
        conn.close()
        print(f"Conversación cerrada manualmente para contact_id: {contact_id}")

    except Exception as e:
        print(f'Error al cerrar manualmente la conversación: {e}')

def lambda_handler(event, context):
    """Handler principal de la Lambda."""
    try:
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Obtener todas las conversaciones abiertas
        cursor.execute("SELECT contact_id FROM respond_io.conversation WHERE conversation_status = 'open'")
        conversations = cursor.fetchall()

        for conversation in conversations:
            contact_id = conversation['contact_id']
            response = close_conversations(contact_id, api_token)

            if response['status'] == 404 or response['status'] == 403:
                print(f"Intentando cerrar manualmente la conversación para contact_id: {contact_id}")
                close_conversation_manually(contact_id)
            elif response['status'] == 200:
                print(f"Conversación cerrada con éxito para contact_id: {contact_id}")
            else:
                print(f"Error al cerrar la conversación para contact_id: {contact_id}: {response}")

        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"ERROR en lambda_handler: {e}")