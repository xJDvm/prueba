import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect
from datetime import datetime, timezone


def handle_update_conversation(data):
    timestamp = data["message"]["timestamp"]
    contact_id = str(data["contact"]["id"])
    
    message_timestamp = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    
    dl_modified_at = datetime.now().isoformat()
    
    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    update_query = """
        UPDATE respond_io.conversation
        SET dl_modified_at = %s,
            time_last_mess_out = %s
        WHERE contact_id = %s
        AND conversation_status = 'open'
    """
    cursor.execute(update_query, (dl_modified_at, message_timestamp, contact_id))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos actualizados correctamente en la tabla respond_io.conversation")

def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
            
            handle_update_conversation(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response