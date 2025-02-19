import json
import psycopg2.extras
from respondfunctions.assign_conversation import assign_conversation
from dbconnection.dbconnection import connect
from datetime import datetime, timezone

def lambda_handler(event, context):

    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]: 
        try:
            print(f"Raw event data: {event}")
            
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]

            contact_id = str(data["contact_id"])
            store = data["store"]
            message_time = datetime.strptime(data["time"], '%Y-%m-%d %H:%M:%S')

            store_assignee_map = {
                "Curridabat": 273980,
                "Escazú": 273980,
                "Belén": 273980,
                "Tibás": 475025,
                "Desamparados": 475025
            }

            assignee = store_assignee_map.get(store, None)
            print(f"Contact ID: {contact_id}, Assignee: {assignee}")

            conn = connect()
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

                if diff_in > 15:  # 900 segundos = 15 minutos
                    print(f"Primera validacion {assignee}")
                    # Cliente lleva más de 15 minutos sin responder
                    if time_last_mess_out is None or (now - time_last_mess_out).total_seconds() > 15:
                        print(f"Segunda validacion {assignee}")
                        if time_last_mess_out_wf is None or time_last_mess_out <= time_last_mess_out_wf:
                            print(f"Assigning conversation to {assignee}")
                            
                            result = assign_conversation(contact_id, assignee)
                            
                            print(f"Result: {result}")

            cursor.close()

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR:', e)

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response