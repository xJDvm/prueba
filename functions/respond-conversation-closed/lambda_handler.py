import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect


def handle_close_conversation(data):
    contact_id = str(data["contact"]["id"])
    conversation_cod = f"{contact_id}{data['conversation']['openedTime']}"
    closed_time = datetime.datetime.fromtimestamp(data["conversation"]["closedTime"]).isoformat()
    conversation_opened_at = datetime.datetime.fromtimestamp(data["conversation"]["openedTime"]).isoformat()
    close_by_id = str(data["conversation"]["closedBy"]["id"]) if data["conversation"]["closedBy"]["id"] else data["conversation"]["closedBySource"]
    conversation_status = data["contact"]["status"]
    dl_modified_at = datetime.datetime.now().isoformat()

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
    print("Datos actualizados correctamente en la tabla respond_io.conversation")


def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
            
            handle_close_conversation(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response