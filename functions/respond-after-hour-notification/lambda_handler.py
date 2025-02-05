import json
from respondfunctions.send_emails import send_email

def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}
    
    for record in event["Records"]: 
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
            print(data)
            
            contact = data["contact"]["firstName"]
            contactId = data["contact"]["id"]
            
            sender = 'respond@arqintelix.biz'
            recipient = 'jvaldes@intelix.biz'
            subject = contact
            body_text = f"Contacto de  + {contactId}"
            body_html = f"""
            <html>
            <head></head>
            <body>
                <h1>Contacto de {contactId}</h1>
                <p>Hola {contact},</p>
                <p>Este es un mensaje de contacto.</p>
            </body>
            </html>
            """

            if not all([sender, recipient, subject, body_text, body_html]):
                raise ValueError("Missing email parameters")

            send_email(sender, recipient, subject, body_text, body_html)
            
            
        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response