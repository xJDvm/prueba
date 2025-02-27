import os
import requests
import json
import boto3

def create_comment(message, contact):
    url_comment = f"https://api.respond.io/v2/contact/id:{contact}/comment"

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
        "text": message
    }

    try:
        response_comment = requests.post(url_comment, headers=headers, data=json.dumps(payload))

        return {
            "success": True,
            "content_comment": response_comment.json()
        }

    except Exception as error:
        print(error)
        return {"success": False, "error": str(error)}
