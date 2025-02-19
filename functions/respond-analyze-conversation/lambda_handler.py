import json
import psycopg2.extras
import boto3
import logging
from datetime import datetime, timezone
from dbconnection.dbconnection import connect  # Asegúrate de que este módulo esté correctamente implementado
from respondfunctions.send_emails import send_email  # Asegúrate de que este módulo esté correctamente implementado

# Configuración básica del logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Crear el cliente para el servicio Bedrock Runtime
bedrock_client = boto3.client('bedrock-runtime')

def get_conversation_messages(conversation_cod):
    """
    Obtiene los mensajes de una conversación desde la base de datos.
    """
    try:
        # Conectar a la base de datos
        conn = connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    
    # Consultar la base de datos
    try:
        query = """
            SELECT * 
            FROM respond_io.messages 
            WHERE conversation_cod = %s
            ORDER BY message_timestamp ASC
        """
        cursor.execute(query, (conversation_cod,))
        messages = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error al ejecutar la consulta: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    finally:
        cursor.close()
        conn.close()
    
    # Estructura base de la respuesta
    response = {
        "conversation_cod": conversation_cod,
        "contact_id": messages[0]['contact_id'] if messages else None,  # Tomamos el contact_id del primer mensaje
        "messages": []
    }
    
    # Formatear cada mensaje
    for message in messages:
        formatted_message = {
            "assignado_id": message['assignado_id'],
            "message": {
                "messageId": message['message_id'],
                "timestamp": int(message['message_timestamp'].timestamp() * 1000),  # Convertir a milisegundos
                "type": message['message_type'],
                "classification": message['message_classification'],
                "datatype": message['message_datatype'],
                "content": {}
            }
        }
        
        # Determinar el tipo de mensaje y formatear según corresponda
        if message['message_datatype'] == 'text':
            formatted_message['message']['content'] = {
                'text': message['text_message']
            }
        elif message['message_datatype'] == 'attachment':
            formatted_message['message']['content'] = {
                'filename': message['filename'],
                'url': message['url'],
                'text_message': message['text_message'],  # Incluir text_message
                'description': message['text_message']  # Usamos text_message para la descripción
            }
        elif message['message_datatype'] == 'location':
            formatted_message['message']['content'] = {
                'latitude': message['latitude'],
                'longitude': message['longitude'],
                'address': message['address']
            }
        elif message['message_datatype'] == 'template':
            formatted_message['message']['content'] = {
                'template_id': message['template_id']
            }
        elif message['message_datatype'] == 'quick_reply':
            formatted_message['message']['content'] = {
                'type': 'quick_reply',
                'text_message': message['text_message'],  # Incluir text_message
                'replies': json.loads(message['replies'])  # Parsear replies desde JSON
            }
        
        # Agregar el mensaje formateado a la lista de mensajes
        response['messages'].append(formatted_message)
    
    return response

def format_conversation(messages):
    """
    Formatea los mensajes en una conversación legible para Bedrock.
    """
    conversation = []
    for message in messages:
        speaker = "Cliente" if message['message']['type'] == "message.received" else "Agente"
        content = message['message']['content']
        
        if message['message']['datatype'] == 'text':
            text = content.get('text', '')
        elif message['message']['datatype'] == 'attachment':
            text = f"Archivo adjunto: {content.get('filename', '')} - {content.get('description', '')}"
        elif message['message']['datatype'] == 'location':
            text = f"Ubicación: Latitud {content.get('latitude', '')}, Longitud {content.get('longitude', '')}, Dirección: {content.get('address', '')}"
        elif message['message']['datatype'] == 'template':
            text = f"Plantilla: {content.get('template_id', '')}"
        elif message['message']['datatype'] == 'quick_reply':
            text = f"Respuesta rápida: {content.get('text_message', '')} - Opciones: {', '.join(content.get('replies', []))}"
        else:
            text = "Mensaje no reconocido"
        
        conversation.append({
            "speaker": speaker,
            "message": text,
            "timestamp": datetime.fromtimestamp(message['message']['timestamp'] / 1000, timezone.utc).isoformat()
        })
    
    return conversation

def analyze_conversation_with_bedrock(conversation):
    """
    Envía la conversación a Bedrock para su análisis.
    """
    try:
        # Construir el prompt para el análisis
        prompt = (
            "Analiza la siguiente conversación que involucra a un cliente y un agente. "
            "Responde únicamente en formato JSON con los siguientes campos:\n"
            '- "cliente_satisfecho": "si" o "no".\n'
            '- "motivo_insatisfaccion": si el cliente está insatisfecho, indica el motivo; de lo contrario, una cadena vacía.\n'
            '- "resumen_conversation": un resumen breve de la conversación.\n'
            '- "nivel_nps": un valor numérico (asegúrate de que siempre sea un número, sin descripciones textuales).\n'
            '- "inquietud_resuelta": "si" o "no".\n'
            '- "nivel_atencion_agente": uno de los siguientes: "profesional", "poco profesional", "grosero", "atento", "amable".\n'
            '- "sugerencia_mejora": si existe oportunidad de mejora para el agente, proporciona una sugerencia concreta; de lo contrario, una cadena vacía.\n'
            '- "puntos_atencion_workflow": indica puntos de atención en el workflow basados en los comentarios, si los hubiese; de lo contrario, una cadena vacía.\n'
            '- "inconveniente_barrera_idiomatica": "si" o "no", detectando si existen inconvenientes por barreras idiomáticas. Si es "si", opcionalmente puedes incluir detalles en un campo adicional "detalle_barrera_idiomatica"; de lo contrario, déjalo vacío.\n'
            '- "tiempo_atencion_incorrecto": "si" o "no". Si la conversación incluye marcas de tiempo, determina si el tiempo de atención fue incorrecto; de lo contrario, asigna "no".\n'
            '- "detalle_tiempo_atencion": una explicación del valor asignado en "tiempo_atencion_incorrecto" si corresponde; de lo contrario, una cadena vacía.\n'
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(conversation, ensure_ascii=False)
                        }
                    ]
                }
            ]
        }

        # Invocar el modelo de Bedrock
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-haiku-20241022-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        # Leer y decodificar la respuesta del modelo
        response_body = response["body"].read().decode("utf-8")
        logger.info("Respuesta del modelo: %s", response_body)

        # Intentar interpretar la respuesta como JSON
        resultado = json.loads(json.loads(response_body)["content"][0]["text"])

        return resultado

    except Exception as ex:
        logger.error("Error al analizar la conversación con Bedrock: %s", str(ex))
        raise

def lambda_handler(event, context):
    # Obtener el código de conversación del evento
    conversation_cod = event.get('conversation_cod')
    
    if not conversation_cod:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'conversation_cod is required'})
        }
    
    # Obtener los mensajes de la conversación
    response = get_conversation_messages(conversation_cod)
    
    # Verificar si hubo un error al obtener los mensajes
    if 'statusCode' in response and response['statusCode'] != 200:
        return response
    
    # Formatear la conversación para Bedrock
    formatted_conversation = format_conversation(response['messages'])
    
    # Analizar la conversación con Bedrock
    try:
        analysis_result = analyze_conversation_with_bedrock(formatted_conversation)
        
        # Combinar la respuesta original con el análisis de Bedrock
        response['analysis'] = analysis_result
        
        # Enviar un correo electrónico con el análisis
        sender = 'respond@arqintelix.biz'
        recipient = 'jvaldes@intelix.biz'
        cc='projas@intelix.biz'
        subject = "Respond.io | Notificación de mensaje fuera de horario"
        body_text = "Respond.io | Notificación de mensaje fuera de horario"
        body_html = f"""
        <html>
        <head>
            <title>Respond.io | Notificación de mensaje fuera de horario</title>
        </head>
        <body>
            <h1>Respond.io | Notificación de mensaje fuera de horario</h1>
            <p><strong>Conversation Code:</strong> {response['conversation_cod']}</p>
            <p><strong>Contact ID:</strong> {response['contact_id']}</p>
            <h2>Messages:</h2>
            <ul>
            {''.join(f"<li><strong>{msg['message']['timestamp']} - {msg['assignado_id']}:</strong> {msg['message']['content']}</li>" for msg in response['messages'])}
            </ul>
            <h2>Analysis:</h2>
            <pre>{json.dumps(response['analysis'], indent=4, ensure_ascii=False)}</pre>
        </body>
        </html>
        """
        
        send_email(sender, recipient, subject, body_text, body_html, cc)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response, ensure_ascii=False)
        }
    
    except Exception as ex:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(ex)})
        }