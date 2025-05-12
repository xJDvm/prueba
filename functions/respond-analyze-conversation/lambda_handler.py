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
        print(json.dumps({'ErrorRespond': str(e), 'ConversationCod': conversation_cod, 'DeveloperMessage': 'Error al conectar a la base de datos'}))
        raise
    
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
        print(json.dumps({'ErrorRespond': str(e), 'ConversationCod': conversation_cod, 'DeveloperMessage': 'Error al ejecutar la consulta de obtención de mensajes'}))
        raise
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
        print(json.dumps({'ErrorRespond': str(e), 'Conversation': conversation}))
        raise
   
   
   
   
    
def update_database(conversation_cod, analysis_result):
    try:
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(response, ensure_ascii=False)
        }
        
    except Exception as e:
        print(json.dumps({'ErrorRespond': str(e), "ConversationCod": conversation_cod, "DeveloperMessage": "Error al actualizar la base de datos"}))
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def lambda_handler(event, context):
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            conversation_cod = str(json.loads(body["conversation_cod"]))            
            
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
            analysis_result = analyze_conversation_with_bedrock(formatted_conversation)
            
            update_database(conversation_cod, analysis_result)
            print(json.dumps({'Success': 'Conversation analyzed and updated successfully', 'ConversationCod': conversation_cod}))
    
        except Exception as e:
            print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
            batch_item_failures.append({"itemIdentifier": record['messageId']})
            continue
    return {
        'batchItemFailures': batch_item_failures
    }