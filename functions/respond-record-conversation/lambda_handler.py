import json
from respondfunctions.keyword_check import keyword_checker

def lambda_handler(event, context):
    print(event)

    try:
        # Capturar el cuerpo del POST
        body = json.loads(event.get('body', '{}'))

        # Verificar si el event_type es message.received
        if body.get('event_type') == 'message.received':
            message_text = body.get('message', {}).get('message', {}).get('text')
            contact_id = body.get('contact', {}).get('id')

            # Llamar a la función keyword_checker
            result = keyword_checker(message_text, contact_id)

            # Verificar si se encontraron palabras clave
            if result.get('success'):
                print('Palabra clave encontrada')


        # Retornar una respuesta exitosa
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event processed successfully'})
        }

    except Exception as e:
        # Manejar el error
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }