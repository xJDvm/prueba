import os
import requests
import json

def create_comment(message, contact, api_token):
    url_comment = f"https://api.respond.io/v2/contact/id:{contact}/comment"
    

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_token}",  # Usar la variable respond_token
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
        print(json.dumps({'ErrorRespond': str(error), 'Record': record}))
        return {"success": False, "error": str(error)}
