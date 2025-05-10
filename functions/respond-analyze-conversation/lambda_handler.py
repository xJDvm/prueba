import json
import psycopg2.extras
import boto3
import logging
from datetime import datetime, timezone
from int_respond_sendemail import send_email  # Asegúrate de que este módulo esté correctamente implementado
from respond_dbconnection.dbconnection import connect  # Asegúrate de que este módulo esté correctamente implementado
from respond_dbconnection.secretManager import get_database_credentials

db_credentials = get_database_credentials()

# Configuración básica del logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Crear el cliente para el servicio Bedrock Runtime
bedrock_client = boto3.client('bedrock-runtime')

def get_conversation_messages(conversation_cod):
    try:
        # Conectar a la base de datos
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {str(e)}")
        print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
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
        # print(cursor.mogrify(query, (conversation_cod,)).decode('utf-8'))
        messages = cursor.fetchall()
        print(messages)
    except Exception as e:
        logger.error(f"Error al ejecutar la consulta: {str(e)}")
        print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
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
            "assigned_user_id": message['assigned_user_id'],
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
                'message_text': message['message_text']
            }
        elif message['message_datatype'] == 'attachment':
            formatted_message['message']['content'] = {
                'message_filename': message['message_filename'],
                'message_url': message['message_url'],
                'message_text': message['message_text'],  # Incluir message_text
            }
        elif message['message_datatype'] == 'location':
            formatted_message['message']['content'] = {
                'message_latitude': message['message_latitude'],
                'message_longitude': message['message_longitude'],
                'message_address': message['message_address']
            }
        elif message['message_datatype'] == 'template':
            formatted_message['message']['content'] = {
                'template_id': message['template_id']
            }
        elif message['message_datatype'] == 'quick_reply':
            formatted_message['message']['content'] = {
                'type': 'quick_reply',
                'message_text': message['message_text'],  # Incluir message_text
                'replies': json.loads(message['message_replies'])  # Parsear replies desde JSON
            }
        
        # Agregar el mensaje formateado a la lista de mensajes
        response['messages'].append(formatted_message)
        
        logger.info(f"Total messages retrieved: {len(response['messages'])}")
    
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
            text = content.get('message_text', '')
        elif message['message']['classification'] == 'attachment':
            text = f"Archivo adjunto: {content.get('message_filename', '')} - {content.get('message_text', '(Archivo adjunto sin texto)')}"
        elif message['message']['datatype'] == 'location':
            text = f"Ubicación: Latitud {content.get('message_latitude', '')}, Longitud {content.get('message_longitude', '')}, Dirección: {content.get('message_address', '')}"
        elif message['message']['datatype'] == 'template':
            text = f"Plantilla: {content.get('template_id', '')}"
        elif message['message']['datatype'] == 'quick_reply':
            text = f"Respuesta rápida: {content.get('message_text', '(Quick reply adjunta sin texto)')} - Opciones: {', '.join(content.get('replies', []))}"
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
        """prompt = (
            "Analiza la conversación entre un cliente y un agente tomando en cuenta los siguientes criterios antes de determinar el nivel de atención del agente:\n"
            "- Evalúa si el cliente realmente interactuó con el agente antes de concluir que el nivel de atención fue deficiente.\n"
            "- Si el cliente no respondió o no completó el workflow, no penalices al agente injustamente.\n"
            "- Calcula correctamente los tiempos de respuesta del agente sin incluir períodos en los que el cliente no interactuó.\n"
            "- Un tiempo de atención incorrecto se considera solo si la marca del ultimo mensaje enviado por el cliente y la primera respuesta del asesor supera los 30 minutos.\n\n"
            "Responde únicamente en formato JSON con los siguientes campos:\n"
            '{\n'
            '  "cliente_satisfecho": "si | no",\n'
            '  "motivo_insatisfaccion": "Si el cliente está insatisfecho, indica el motivo; de lo contrario, una cadena vacía.",\n'
            '  "resumen_conversacion": "Resumen breve de la conversación.",\n'
            '  "nivel_nps": "Número entero entre 0 y 10 (sin descripciones textuales).",\n'
            '  "inquietud_resuelta": "si | no",\n'
            '  "nivel_atencion_agente": "Enum: profesional | poco profesional | grosero | atento | amable",\n'
            '  "sugerencia_mejora": "Si existe oportunidad de mejora para el agente, proporciona una sugerencia concreta; de lo contrario, una cadena vacía.",\n'
            '  "puntos_atencion_workflow": "Indica puntos de atención en el workflow basados en los comentarios, si los hubiese; de lo contrario, una cadena vacía.",\n'
            '  "inconveniente_barrera_idiomatica": "si | no",\n'
            '  "detalle_barrera_idiomatica": "Si existe barrera idiomática, detalla la dificultad encontrada; de lo contrario, una cadena vacía.",\n'
            '  "tiempo_atencion_incorrecto": "si | no. Se asigna \'sí\' solo si el tiempo entre el primer mensaje del cliente y la primera respuesta del asesor supera los 30 minutos.",\n'
            '  "detalle_tiempo_atencion": "Explicación del valor asignado en tiempo_atencion_incorrecto si corresponde; de lo contrario, una cadena vacía.",\n'
            '  "tiempo_promedio_respuesta_primera_interaccion": "Número en minutos. Calcula el tiempo transcurrido desde el último mensaje del cliente hasta la primera respuesta del asesor.",\n'
            '  "tiempo_promedio_respuesta": "Número en minutos. Calcula el tiempo promedio de respuesta del asesor sin incluir períodos en los que el cliente no interactúa.",\n'
            '  "tiempo_total_resolucion": "Número en minutos. Calcula el tiempo total desde el primer mensaje del cliente hasta la resolución de la consulta.",\n'
            '  "cantidad_interacciones": "Número entero. Cuantifica cuántos mensajes intercambiaron el cliente y el agente antes de llegar a una conclusión.",\n'
            '  "desviacion_tiempo_respuesta": "Número en minutos. Calcula la desviación estándar de los tiempos de respuesta del asesor para identificar respuestas fuera del promedio.",\n'
            '  "conversacion_abandonada_cliente": "si | no. Determina si el cliente dejó de interactuar sin cerrar la conversación.",\n'
            '  "conversacion_abandonada_asesor": "si | no. Determina si el asesor dejó de responder antes de que la consulta fuera resuelta, sin aviso o seguimiento.",\n'
            '  "analisis_sentimiento_cliente": "Enum: positivo | neutral | negativo. Evalúa el tono del cliente basándose en sus mensajes."\n'
            '}'
        )"""
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT prompt FROM respond_io.ia_prompts WHERE category = 'analyze_conversation'")
        prompt = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logger.info("Prompt obtenido de la base de datos: %s", prompt)
        
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
            modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0",
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

    except Exception as e:
        logger.error("Error al analizar la conversación con Bedrock: %s", str(e))
        print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
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
        
        
        print(response)
        # Convertir el análisis a un diccionario de Python
        analysis_dict = response['analysis'] if isinstance(response['analysis'], dict) else json.loads(response['analysis'])
        print(analysis_dict)
        
        # Guardar los valores en variables
        cliente_satisfecho = analysis_dict.get('cliente_satisfecho')
        motivo_insatisfaccion = analysis_dict.get('motivo_insatisfaccion')
        resumen_conversation = analysis_dict.get('resumen_conversacion')
        nivel_nps = analysis_dict.get('nivel_nps')
        inquietud_resuelta = analysis_dict.get('inquietud_resuelta')
        nivel_atencion_agente = analysis_dict.get('nivel_atencion_agente')
        sugerencia_mejora = analysis_dict.get('sugerencia_mejora')
        puntos_atencion_workflow = analysis_dict.get('puntos_atencion_workflow')
        inconveniente_barrera_idiomatica = analysis_dict.get('inconveniente_barrera_idiomatica')
        detalle_barrera_idiomatica = analysis_dict.get('detalle_barrera_idiomatica')
        tiempo_atencion_incorrecto = analysis_dict.get('tiempo_atencion_incorrecto')
        detalle_tiempo_atencion = analysis_dict.get('detalle_tiempo_atencion')
        tiempo_promedio_respuesta_primera_interaccion = analysis_dict.get('tiempo_promedio_respuesta_primera_interaccion')
        tiempo_promedio_respuesta = analysis_dict.get('tiempo_promedio_respuesta')
        tiempo_total_resolucion = analysis_dict.get('tiempo_total_resolucion')
        cantidad_interacciones = analysis_dict.get('cantidad_interacciones')
        desviacion_tiempo_respuesta = analysis_dict.get('desviacion_tiempo_respuesta')
        conversacion_abandonada_cliente = analysis_dict.get('conversacion_abandonada_cliente')
        conversacion_abandonada_asesor = analysis_dict.get('conversacion_abandonada_asesor')
        analisis_sentimiento_cliente = analysis_dict.get('analisis_sentimiento_cliente')
        
        # Conectar a la base de datos
        conn = connect(db_credentials)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        update_query = """
            UPDATE respond_io.conversation
            SET customer_satisfaction = %s,
                dissatisfaction_reason = %s,
                conversation_summary = %s,
                nps_level = %s,
                concern_resolved = %s,
                agent_attention_level = %s,
                improvement_suggestion = %s,
                workflow_attention_points = %s,
                language_barrier_issue = %s,
                language_barrier_details = %s,
                incorrect_response_time = %s,
                response_time_details = %s,
                avg_first_response_time = %s,
                avg_response_time = %s,
                total_resolution_time = %s,
                interaction_count = %s,
                response_time_deviation = %s,
                abandoned_by_client = %s,
                abandoned_by_agent = %s,
                customer_sentiment_analysis = %s
            WHERE conversation_cod = %s
        """
        
        cursor.execute(update_query, (
            cliente_satisfecho,
            motivo_insatisfaccion,
            resumen_conversation,
            nivel_nps,
            inquietud_resuelta,
            nivel_atencion_agente,
            sugerencia_mejora,
            puntos_atencion_workflow,
            inconveniente_barrera_idiomatica,
            detalle_barrera_idiomatica,
            tiempo_atencion_incorrecto,
            detalle_tiempo_atencion,
            tiempo_promedio_respuesta_primera_interaccion,
            tiempo_promedio_respuesta,
            tiempo_total_resolucion,
            cantidad_interacciones,
            desviacion_tiempo_respuesta,
            conversacion_abandonada_cliente,
            conversacion_abandonada_asesor,
            analisis_sentimiento_cliente,
            conversation_cod
        ))
        conn.commit()
        print("Datos actualizados correctamente en la tabla respond_io.conversation")
        cursor.close()
        conn.close()
        
        
        # Enviar un correo electrónico con el análisis
        recipient = ['jvaldes@intelix.biz']
        cc=['projas@intelix.biz']
        subject = "Respond.io | Analisis conversacion"
        body_text = "Respond.io | Analisis Conversacion"
        body_html = f"""
            <html>
            <head>
                <title>Respond.io | Análisis de Conversación</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        color: #333333;
                        backgrsound-color: #f4f4f4;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: #ffffff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #3d85c6;
                    }}
                    h2 {{
                        color: #333333;
                        border-bottom: 2px solid #3d85c6;
                        padding-bottom: 5px;
                    }}
                    p {{
                        font-size: 14px;
                    }}
                    .message {{
                        margin-bottom: 10px;
                        padding: 10px;
                        border-radius: 5px;
                    }}
                    .agent {{
                        background-color: #e7f3fe;
                        border-left: 5px solid #3d85c6;
                    }}
                    .client {{
                        background-color: #f9f9f9;
                        border-left: 5px solid #333333;
                    }}
                    .analysis {{
                        background-color: #f1f1f1;
                        padding: 10px;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Respond.io | Análisis de Conversación</h1>
                    <p><strong>Código de Conversación:</strong> {response['conversation_cod']}</p>
                    <p><strong>ID de Contacto:</strong> {response['contact_id']}</p>
                    <h2>Mensajes:</h2>
                    <ul>
                        {''.join(f"<li class='message {'agent' if msg['message']['type'] == 'message.sent' else 'client'}'><strong>{msg['message']['timestamp']} - {msg['assigned_user_id']}:</strong> {msg['message']['content']}</li>" for msg in response['messages'])}
                    </ul>
                    <h2>Análisis:</h2>
                    <div class="analysis">
                        <p><strong>Cliente Satisfecho:</strong> {response['analysis']['cliente_satisfecho']}</p>
                        <p><strong>Motivo de Insatisfacción:</strong> {response['analysis']['motivo_insatisfaccion']}</p>
                        <p><strong>Resumen de la Conversación:</strong> {response['analysis']['resumen_conversacion']}</p>
                        <p><strong>Nivel NPS:</strong> {response['analysis']['nivel_nps']}</p>
                        <p><strong>Inquietud Resuelta:</strong> {response['analysis']['inquietud_resuelta']}</p>
                        <p><strong>Nivel de Atención del Agente:</strong> {response['analysis']['nivel_atencion_agente']}</p>
                        <p><strong>Sugerencia de Mejora:</strong> {response['analysis']['sugerencia_mejora']}</p>
                        <p><strong>Puntos de Atención en el Workflow:</strong> {response['analysis']['puntos_atencion_workflow']}</p>
                        <p><strong>Inconveniente por Barrera Idiomática:</strong> {response['analysis']['inconveniente_barrera_idiomatica']}</p>
                        <p><strong>Detalle de la Barrera Idiomática:</strong> {response['analysis']['detalle_barrera_idiomatica']}</p>
                        <p><strong>Tiempo de Atención Incorrecto:</strong> {response['analysis']['tiempo_atencion_incorrecto']}</p>
                        <p><strong>Detalle del Tiempo de Atención:</strong> {response['analysis']['detalle_tiempo_atencion']}</p>
                        <p><strong>Tiempo Promedio de Respuesta en la Primera Interacción:</strong> {response['analysis']['tiempo_promedio_respuesta_primera_interaccion']}</p>
                        <p><strong>Tiempo Promedio de Respuesta:</strong> {response['analysis']['tiempo_promedio_respuesta']}</p>
                        <p><strong>Tiempo Total de Resolución:</strong> {response['analysis']['tiempo_total_resolucion']}</p>
                        <p><strong>Cantidad de Interacciones:</strong> {response['analysis']['cantidad_interacciones']}</p>
                        <p><strong>Desviación del Tiempo de Respuesta:</strong> {response['analysis']['desviacion_tiempo_respuesta']}</p>
                        <p><strong>Conversación Abandonada por el Cliente:</strong> {response['analysis']['conversacion_abandonada_cliente']}</p>
                        <p><strong>Conversación Abandonada por el Asesor:</strong> {response['analysis']['conversacion_abandonada_asesor']}</p>
                        <p><strong>Análisis de Sentimiento del Cliente:</strong> {response['analysis']['analisis_sentimiento_cliente']}</p>
                    </div>
                </div>
            </body>
            </html>
        """
        
        # send_email(recipient, subject, body_text, body_html, cc)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response, ensure_ascii=False)
        }
    
    except Exception as e:
        print(f"Error al analizar la conversación: {str(e)}")
        print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }