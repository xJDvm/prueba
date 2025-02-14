import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect
from lambda_response import lambda_response
from status_http import HttpStatus
from datetime import datetime, timezone

def save_last_message_wf(data):
    contact_id = str(data["contact"]["id"])
    timestamp = data["message"]["timestamp"]
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    
    dl_modified_at = datetime.now().isoformat()

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    update_query = """
        UPDATE respond_io.conversation
        SET time_last_mess_out_wf = %s,
            dl_modified_at = %s
        WHERE conversation_cod = (
            SELECT conversation_cod
            FROM respond_io.conversation
            WHERE contact_id = %s
            AND conversation_status = 'open'
        )
    """
    

    
    cursor.execute(update_query, (message_timestamp, dl_modified_at, contact_id,))
    
    print(cursor.mogrify(update_query, (message_timestamp, dl_modified_at, contact_id)).decode('utf-8'))
        
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.messages")

def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
            
            save_last_message_wf(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response