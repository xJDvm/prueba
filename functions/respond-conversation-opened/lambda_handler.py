import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect
from dbconnection.secretManager import get_database_credentials

db_credentials = get_database_credentials()


def handle_create_conversation(data):
    contact_id = str(data["contact"]["id"])
    conversation_cod = f"{contact_id}{data['conversation']['conversationOpenedAt']}"
    conversation_status = data["contact"]["status"]
    conversation_source = data["conversation"]["source"]
    conversation_opened_at = datetime.datetime.fromtimestamp(data["conversation"]["conversationOpenedAt"]).isoformat()
    channel_id = str(data["conversation"]["firstIncomingMessageChannelId"])
    
    dl_created_at = datetime.datetime.now().isoformat()
    dl_modified_at = datetime.datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Insertar la nueva conversación en la tabla respond_io.conversation
    insert_query = """
        INSERT INTO respond_io.conversation (conversation_cod, conversation_status, contact_id, conversation_source, conversation_opened_at, channel_id, dl_created_at, dl_modified_at, dl_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (conversation_cod, conversation_status, contact_id, conversation_source, conversation_opened_at, channel_id, dl_created_at, dl_modified_at, dl_condition))
    
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.conversation")


def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
                        
            handle_create_conversation(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response