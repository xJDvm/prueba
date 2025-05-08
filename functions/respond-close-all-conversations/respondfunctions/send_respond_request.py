import requests

def close_conversations(contact, api_token):
    """Cierra la conversación de un contacto en Respond.io API."""
    url = f"https://api.respond.io/v2/contact/id:{contact}/conversation/status"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {"status": "close"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        return {
            "status": response.status_code,
            "content_contacts": response.json()
        }
    except Exception as error:
        print(f"Error en close_conversations: {error}")
        print(json.dumps({'ErrorRespond': str(error), 'Record': record}))
        return {
            "success": False,
            "status": None,
            "error": str(error)
        }