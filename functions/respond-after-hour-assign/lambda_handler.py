import json
import psycopg2.extras
from datetime import datetime, timezone
from respondfunctions.assign_conversation import assign_conversation
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials
from int_respond_token import get_respond_token
from int_respond_config import get_respond_config

respond_config = json.loads(get_respond_config())
store_assignee_map = respond_config.get("storeAssigneeMap", {})
after_hour_assign_seconds = respond_config.get("afterHourAssignSeconds", 900)  # 15 minutos

db_credentials = get_database_credentials()
api_token = get_respond_token()

def lambda_handler(event, context):

    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]: 
        try:
            print(f"Raw event data: {event}")
            
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message

            contact_id = str(data["contact_id"])
            store = data["store"]
            message_time = datetime.strptime(data["time"], '%Y-%m-%d %H:%M:%S')

            assignee = store_assignee_map.get(store, None)
            print(f"Contact ID: {contact_id}, Assignee: {assignee}")

            conn = connect(db_credentials)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            

            conversation_query = """
                SELECT time_last_mess_in, time_last_mess_out, time_last_mess_out_wf
                FROM respond_io.conversation
                WHERE contact_id = %s AND conversation_status = 'open'
            """

            cursor.execute(conversation_query, (contact_id,))
            conversation = cursor.fetchone()

            if conversation:
                now = datetime.utcnow()
                time_last_mess_in = conversation['time_last_mess_in']
                time_last_mess_out = conversation['time_last_mess_out']
                time_last_mess_out_wf = conversation['time_last_mess_out_wf']

                diff_in = (now - time_last_mess_in).total_seconds()

                if diff_in > after_hour_assign_seconds:  # 900 segundos = 15 minutos
                    print(f"Primera validacion {assignee}")
                    # Cliente lleva más de 15 minutos sin responder
                    if time_last_mess_out is None or (now - time_last_mess_out).total_seconds() > after_hour_assign_seconds:
                        print(f"Segunda validacion {assignee}")
                        if time_last_mess_out_wf is None or time_last_mess_out is None or time_last_mess_out <= time_last_mess_out_wf:
                            print(f"Assigning conversation to {assignee}")
                            
                            result = assign_conversation(contact_id, assignee, api_token)
                            
                            print(f"Result: {result}")

            cursor.close()

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR:', e)

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response