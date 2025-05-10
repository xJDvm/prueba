import boto3
import json
import os

def get_database_credentials():
    
    secret_name = os.environ['secretRespondIO']
    
    try:
        print(f"Obteniendo secreto de AWS Secrets Manager: {secret_name}")
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        
        secret = response.get('SecretString')
        if not secret:
            raise ValueError("No se encontró SecretString en la respuesta")
        # Parsear y guardar en caché
        credentials = json.loads(secret)
        
        return credentials
    
    except ClientError as e:
        print(f"Error de AWS al obtener secreto: {e.response['Error']['Code']}")
        raise
    except Exception as e:
        print(f"Error inesperado: {e}")
        print(json.dumps({'ErrorRespond': str(e)}))
        raise