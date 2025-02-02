import os
import re
import json
import requests
from send_respond_comment import create_comment

def normalize_text(text):
    return text.lower().encode('utf-8').decode('utf-8', 'ignore')

def keyword_checker(message, contact):
    keywords = [
        "No me llegó el pedido", "Mal despacho", "Mal cotizado", "Chofer indispuesto",
        "Tardan mucho en contestar", "Inútiles", "Inoperancia", "Ineficiencia",
        "Molesto", "Enojado", "No me avisaron antes", "Compro en la competencia",
        "Tardan mucho en cotizar", "Lentos", "No me han llamado", "Cuando llega el pedido",
        "Ocupo hablar con un supervisor", "Guindando", "Me pueden atender", "Urgente",
        "Error", "Incompleto", "Pendiente", "No me contestan", "No tengo respuesta",
        "Me precisa", "Lo necesitaba para ayer", "Me pueden contestar",
        "Me pueden dar respuesta", "Me ignoraron", "Me dejaron en visto",
        "Me falta", "Cómo puede ser posible", "Nadie me ayuda"
    ]

    if not message:
        return {"success": False, "message": "message no definido"}

    normalized_message = normalize_text(message)
    found_keywords = []

    for word in keywords:
        normalized_word = normalize_text(word)
        if re.search(normalized_word, normalized_message, re.IGNORECASE):
            found_keywords.append(word)

    if found_keywords:
        comment = f'Se detectaron las siguientes palabras clave: "{", ".join(found_keywords)}" en el message.'

        url_contact = f"https://api.respond.io/v2/contact/id:{contact}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.environ['RESPOND_API_TOKEN']}",  # Obtener el token de las variables de entorno
            "Content-Type": "application/json"
        }

        try:
            comment_response = create_comment(comment, contact)
            response_contact = requests.get(url_contact, headers=headers)

            return {
                "success": True,
                "content_contact": response_contact.json(),
                "content_comment": comment_response["content_comment"],
                "keywords": found_keywords
            }

        except Exception as error:
            print(error)
            return {"success": False, "error": str(error)}

    else:
        return {"success": False, "message": "No se encontraron words clave"}

respuesta = keyword_checker("Hola, no me llegó el pedido", '230625691')
print(json.dumps(respuesta, indent=4))