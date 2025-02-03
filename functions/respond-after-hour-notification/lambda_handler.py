import json
from respondfunctions.send_emails import send_email

def lambda_handler(event, context):
    print(event)

    try:
        body = json.loads(event.get('body', '{}'))

        sender = body.get('sender')
        recipient = body.get('recipient')
        subject = body.get('subject')
        body_text = body.get('body_text')
        body_html = body.get('body_html')

        if not all([sender, recipient, subject, body_text, body_html]):
            raise ValueError("Missing email parameters")

        send_email(sender, recipient, subject, body_text, body_html)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Email sent successfully'})
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }