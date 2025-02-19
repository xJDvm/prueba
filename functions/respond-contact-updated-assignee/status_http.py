from enum import Enum

class HttpStatus(Enum): 
    """
    Enumeración que representa los códigos de estado HTTP estándar y su significado.
    """
    
    OK = 200
    """
    Indica que la solicitud fue correcta.
    """

    CREATED = 201
    """
    Indica que la solicitud fue correcta y resultó en la creación de un nuevo recurso.
    """

    BAD_REQUEST = 400
    """
    Indica que la solicitud HTTP enviada al servidor tiene una sintaxis incorrecta.
    """

    UNAUTHORIZED = 401
    """
    Indica que el usuario que intenta acceder al recurso enviando la solicitud no ha sido autenticado correctamente.
    """

    FORBIDDEN = 403
    """
    Significa que el servidor rechaza nuestra solicitud debido a acceso o permisos insuficientes.
    """

    NOT_FOUND = 404
    """
    Este código de estado se devuelve cuando no se encuentra el recurso solicitado.
    """

    INTERNAL_SERVER_ERROR = 500
    """
    Un error interno del servidor significa que por alguna razón el servidor no pudo procesar la solicitud debido a un error.
    """
