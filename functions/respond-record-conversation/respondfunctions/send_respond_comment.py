import os
import requests
import json

def create_comment(message, contact):
    url_comment = f"https://api.respond.io/v2/contact/id:{contact}/comment"

    headers = {
        "Accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6OTk3Miwic3BhY2VJZCI6MTgwMzI3LCJvcmdJZCI6MTgwNjcyLCJ0eXBlIjoiYXBpIiwiaWF0IjoxNzMxMDc1OTk1fQ.5B0D-TAwrs2jq5XmoUtHmr6NftmMKVVT3WBjXJLvnkg",  # Reemplaza con tu token real
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
