# standard python libs
import json

# local lambda files
from status_http import HttpStatus

def lambda_response(httpStatus:HttpStatus, body:dict):

    """
    Genera un diccionario de respuesta HTTP para AWS Lambda.

    Parametros:
        httpStatus (HttpStatus): El tipo de estado HTTP.
        body (Dict): El cuerpo de la respuesta como un diccionario.

    Retornos:
        Dict: Un diccionario que representa la respuesta HTTP.
    """

    # Obtener el código de estado correspondiente al nombre del error de la enumeración HttpStatus
    status_code = httpStatus.value

    # Construir la respuesta HTTP con el código de estado y el cuerpo del mensaje
    return {
        "statusCode": status_code,
        "body": json.dumps(body, ensure_ascii=False),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
            "Content-Type": "application/json"
        }
    }