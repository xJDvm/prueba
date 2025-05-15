import json
import psycopg2.extras
from botocore.exceptions import ClientError
from respondfunctions.emailbody import build_html
from respondfunctions.keyword_check import keyword_checker
from int_respond_sendemail import send_email
from int_respond_config import get_respond_config
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

respond_config_raw = get_respond_config()
respond_config = json.loads(respond_config_raw)
print(f"Valor de respond_config: {respond_config}")
backup_email = respond_config["backupEmail"]
support_emails = respond_config["supportEmails"]


db_credentials = get_database_credentials()


def get_contact_info(contact_id, conn):
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT leader_email FROM respond_io.contacts WHERE contact_id = %s", (str(contact_id),))
        contact = cursor.fetchone()
        lider_email = contact['leader_email'] if contact else None
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
            data = message
            
            contact_name = data["contact"]["firstName"] + " " + data["contact"]["lastName"]
            contact_id = data["contact"]["id"]
            message_content = data.get("message", {}).get("message", {})
            message_text = message_content.get("text", None)
            
            if not message_text:
                continue  # Saltar al siguiente registro si no hay texto
            
            
            assignee_email = data["contact"]["assignee"]["email"]
            
            try:
                result = keyword_checker(message_text, contact_id)
                
                if result["success"]:
                    
                    keywords = ", ".join(result['keywords'])
                    
                    body_html = build_html(contact_name, contact_id, keywords)
                    
                    print(f"Palabra clave encontrada: '{keywords}' en el contacto con ID: {contact_id}")
                    

                    conn = connect(db_credentials)
                    contact_info_json = get_contact_info(contact_id, conn)
                    contact_info = json.loads(contact_info_json)
                    conn.close()
                    
                    lider_email = contact_info['lider_email'] if contact_info else []
                    
                    recipient = [assignee_email] if assignee_email else backup_email
                    cc = [lider_email] if lider_email else []
                    bcc = support_emails
                    subject = f"Respond.io | Notificación palabra clave detectada - {contact_name}"
                    body_text = f"Respond.io | Notificación palabra clave detectada - {contact_name}"

                    if not all([recipient, subject, body_text, body_html]):
                        raise ValueError("Missing email parameters")

                    send_email(recipient, subject, body_text, body_html, cc, bcc)
            except ClientError as e:
                print("Error sending email: ", e.response['Error']['Message'])

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print(f"ErrorJson: {e}")
        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print(json.dumps({'ErrorRespond': str(e), 'Record': record}))

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response