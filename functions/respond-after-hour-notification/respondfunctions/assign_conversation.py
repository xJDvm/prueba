import os
import re
import json
import requests
import boto3

def assign_conversation(contact, assignee):
    contact = int(contact)  # Convert contact to integer
    assignee = int(assignee)  # Convert assignee to integer

    url_assignee_contact = f"https://api.respond.io/v2/contact/id:{contact}/conversation/assignee"

    ssm = boto3.client('ssm')
    respond_token = os.environ['RESPOND_API_TOKEN']
    response = ssm.get_parameter(Name=respond_token, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {parameter_value}",  # Usar la variable respond_token
        "Content-Type": "application/json"
    }
    
    payload = {
        "assignee": assignee
    }

    try:
        response_assign = requests.post(url_assignee_contact, headers=headers, data=json.dumps(payload))

        return {
            "success": True,
            "content_contact": response_assign.json(),
        }

    except Exception as error:
        print(error)
        return {"success": False, "error": str(error)}