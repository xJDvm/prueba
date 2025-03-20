import os
import requests
import json
import boto3

def close_conversations(contact):
    url = f"https://api.respond.io/v2/contact/id:{contact}/conversation/status"

    ssm = boto3.client('ssm')
    respond_token = os.environ['RESPOND_API_TOKEN']
    print("Respond Token:", respond_token)
    
    response = ssm.get_parameter(Name=respond_token, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    


    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {parameter_value}",  # Usar la variable respond_token
        "Content-Type": "application/json"
    }

    payload = {
        "status": "close"
    }

    try:
        response_conversations = requests.post(url, headers=headers, data=json.dumps(payload))

        return {
            "success": True,
            "content_contacts": response_conversations.json()
        }

    except Exception as error:
        print(error)
        return {"success": False, "error": str(error)}
