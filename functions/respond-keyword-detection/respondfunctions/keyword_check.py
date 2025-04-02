import os
import re
import json
import requests
import boto3
from .send_respond_comment import create_comment
from int_respond_token import get_respond_token

api_token = get_respond_token()

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
        comment = f'Se detectaron las siguientes palabras clave: "{", ".join(found_keywords)}" en el mensaje.'

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
            comment_response = create_comment(comment, contact, api_token)
            response_contact = requests.get(url_contact, headers=headers)

            return {
                "success": True,
                "content_contact": response_contact.json(),
                "content_comment": comment_response,
                "keywords": found_keywords
            }

        except Exception as error:
            print(error)
            return {"success": False, "error": str(error)}

    else:
        return {"success": False, "message": "No se encontraron words clave"}