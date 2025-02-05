import json
from respondfunctions.keyword_check import keyword_checker
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
            message_text = data["message"]["message"]["text"]
            
            result = keyword_checker(message_text, contactId)
            
            if result.get('success'):
                keywords = result.get('keywords')
                content_contact = result.get('content_contact')
                content_comment = result.get('content_comment')
                print(content_contact)
                print(content_comment)
                print(f"Palabra clave encontrada: {keywords} en el contacto con ID: {contactId}")
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
            print('ERROR')
            print(e)


    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response
    # try:
    #     # Capturar el cuerpo del POST
    #     body = json.loads(event.get('body', '{}'))

    #     # Verificar si el event_type es message.received|
    #     if body.get('event_type') == 'message.received':
    #         message_text = body.get('message', {}).get('message', {}).get('text')
    #         contact_id = body.get('contact', {}).get('id')
            
    #         print(contact_id)

    #         # Llamar a la función keyword_checker
    #         result = keyword_checker(message_text, contact_id)

    #         # Verificar si se encontraron palabras clave
    #         if result.get('success'):
    #             keywords = result.get('keywords')
    #             content_contact = result.get('content_contact')
    #             content_comment = result.get('content_comment')
    #             print(content_contact)
    #             print(content_comment)
    #             print(f"Palabra clave encontrada: {keywords} en el contacto con ID: {contact_id}")


    #     # Retornar una respuesta exitosa
    #     return {
    #         'statusCode': 200,
    #         'body': json.dumps({'message': 'Event processed successfully'})
    #     }

    # except Exception as e:
    #     # Manejar el error
    #     print(e)
    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps({'error': str(e)})
    #     }