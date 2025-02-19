import boto3
import json
import os
from botocore.exceptions import ClientError

def send_email(sender, recipient, subject, body_text, body_html, cc_addresses=[]):

    ses_client = boto3.client('ses')

    email_message = {
        'Source': sender,
        'Destination': {
            'ToAddresses': [recipient],
            'CcAddresses': cc_addresses
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
        print(f"Email sent! Message ID: ", response['MessageId'], "To address: ", recipient)
    except ClientError as e:
        print("Error sending email: ", e.response['Error']['Message'])