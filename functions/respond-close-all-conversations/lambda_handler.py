import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from respondfunctions.send_respond_request import close_conversations
from datetime import datetime
from botocore.exceptions import ClientError

def close_conversation_manually(contact_id):
    try:
        con = connect()
        cursor = con.cursor(cursor_factory=psycopg2.extras.DictCursor)

        conversation_query = """
            SELECT conversation_cod, conversation_opened_at
            FROM respond_io.conversation
            WHERE contact_id = %s
            AND conversation_status = 'open'
        """
        
        cursor.execute(conversation_query, (contact_id,))
        conversation = cursor.fetchone()
        
        conversation_cod = conversation['conversation_cod']
        conversation_opened_at = conversation['conversation_opened_at']
        closed_time = datetime.datetime.now().isoformat()
        close_by_id = 'api'
        conversation_status = 'closed'
        dl_modified_at = datetime.datetime.now().isoformat()
        
                # Actualizar la conversación en la tabla respond_io.conversation
        update_query = """
            UPDATE respond_io.conversation
            SET closed_time = %s,
                close_by_id = %s,
                conversation_status = %s,
                dl_modified_at = %s
            WHERE conversation_cod = %s
        """
        
        insert_conversation_cod_query = """
            UPDATE respond_io.messages
            SET conversation_cod = %s,
                dl_modified_at = %s
            WHERE contact_id = %s
            AND message_timestamp between %s and %s
            """
        
        cursor.execute(update_query, (closed_time, close_by_id, conversation_status, dl_modified_at, conversation_cod))
        
        cursor.execute(insert_conversation_cod_query, (conversation_cod, dl_modified_at, contact_id, conversation_opened_at, closed_time))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    except Exception as e:
        print(f'ERROR: {e}')
    

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
            response = close_conversations(contact_id)
            if response['success']:
                print(f"Conversación cerrada para contact_id: {contact_id}")
            elif response['status'] == 404:
                print(f"Conversación no encontrada para contact_id: {contact_id}")
                close_conversation_manually(contact_id)
            else:
                print(f"Error al cerrar la conversación para contact_id: {contact_id}")
            print(response)
            
        conn.commit()
        cursor.close()

    except Exception as e:
        print(f'ERROR: {e}')
        print("Error al ejecutar la lambda")