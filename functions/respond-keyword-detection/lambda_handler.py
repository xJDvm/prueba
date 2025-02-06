import json
from respondfunctions.keyword_check import keyword_checker
from respondfunctions.send_emails import send_email
from respondfunctions.emailbody import build_html

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
            
            result = keyword_checker(message_text, contact_id)
            
            if result["success"]:
                
                keywords = ", ".join(result['keywords'])
                
                
                body = build_html(contact_name, contact_id, keywords)
                
                print(f"Palabra clave encontrada: '{keywords}' en el contacto con ID: {contact_id}")
                
                sender = 'respond@arqintelix.biz'
                recipient = 'jvaldes@intelix.biz'
                subject = f"Respond.io | Notificación palabra clave detectada"
                body_text = "Respond.io | Notificación palabra clave detectada"
                body_html = build_html(contact_name, contact_id, keywords)

                if not all([sender, recipient, subject, body_text, body_html]):
                    raise ValueError("Missing email parameters")

                send_email(sender, recipient, subject, body_text, body_html)

        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            print('ERROR')
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response