import json
import psycopg2.extras
from dbconnection.dbconnection import connect
from respondfunctions.keyword_check import keyword_checker
from respondfunctions.send_emails import send_email
from respondfunctions.emailbody import build_html


def get_contact_info(contact_id, conn):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT lider_email FROM respond_io.contacts WHERE contact_id = %s", (str(contact_id),))
        contact = cursor.fetchone()
        lider_email = contact['lider_email'] if contact else None
        cursor.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        lider_email = None
    
    return json.dumps({"lider_email": lider_email})

def lambda_handler(event, context):

    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]: 
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
            
            contact_name = data["contact"]["firstName"] + " " + data["contact"]["lastName"]
            contact_id = data["contact"]["id"]
            message_text = data["message"]["message"]["text"]
            assignee_email = data["contact"]["assignee"]["email"]
            
            result = keyword_checker(message_text, contact_id)
            
            if result["success"]:
                
                keywords = ", ".join(result['keywords'])
                
                body_html = build_html(contact_name, contact_id, keywords)
                
                print(f"Palabra clave encontrada: '{keywords}' en el contacto con ID: {contact_id}")
                

                conn = connect()
                contact_info_json = get_contact_info(contact_id, conn)
                contact_info = json.loads(contact_info_json)
                conn.close()
                
                lider_email = contact_info['lider_email'] if contact_info else []
                
                sender = 'respond@arqintelix.biz'
                recipient = [assignee_email]
                cc = [lider_email]
                bcc = ['projas@intelix.biz', 'jvaldes@intelix.biz']
                subject = "Respond.io | Notificación palabra clave detectada"
                body_text = "Respond.io | Notificación palabra clave detectada"

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html, cc, bcc)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print(f"ERROR: {e}")
        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print(f"Unexpected error: {e}")

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response