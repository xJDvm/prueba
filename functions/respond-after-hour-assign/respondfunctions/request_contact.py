import os
import re
import json
import requests
import boto3

def request_contact_info(contact):

    url_contact = f"https://api.respond.io/v2/contact/id:{contact}"

    ssm = boto3.client('ssm')
    respond_token = os.environ['RESPOND_API_TOKEN']
    response = ssm.get_parameter(Name=respond_token, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {parameter_value}",  # Usar la variable respond_token
        "Content-Type": "application/json"
    }

    try:
        response_contact = requests.get(url_contact, headers=headers)

        return {
            "success": True,
            "content_contact": response_contact.json(),
        }

    except Exception as error:
        print(error)
        return {"success": False, "error": str(error)}