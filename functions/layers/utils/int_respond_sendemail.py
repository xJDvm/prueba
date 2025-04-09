import boto3
import json
from botocore.exceptions import ClientError
from int_respond_config import get_respond_config

respond_config = json.loads(get_respond_config())
email_sender = respond_config["senderEmail"]
print(respond_config)
print(email_sender)

def send_email(recipients, subject, body_text, body_html, cc_addresses=None, bcc_addresses=None):

    ses_client = boto3.client('ses')

    email_message = {
        'Source': email_sender,
        'Destination': {
            'ToAddresses': recipients,
            'CcAddresses': cc_addresses if cc_addresses else [],
            'BccAddresses': bcc_addresses if bcc_addresses else []
        },
        'Message': {
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body_text,
                    'Charset': 'UTF-8'
                },
                'Html': {
                    'Data': body_html,
                    'Charset': 'UTF-8'
                }
            }
        }
    }

    try:
        response = ses_client.send_email(**email_message)
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    except ClientError as e:
        print("Error sending email: ", e.response['Error']['Message'])