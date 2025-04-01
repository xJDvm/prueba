import os
import re
import json
import requests
import boto3

def assign_conversation(contact, assignee, api_token):
    contact = int(contact)  # Convert contact to integer
    assignee = int(assignee)  # Convert assignee to integer

    url_assignee_contact = f"https://api.respond.io/v2/contact/id:{contact}/conversation/assignee"

    ssm = boto3.client('ssm')
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_token}",  # Usar la variable respond_token
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