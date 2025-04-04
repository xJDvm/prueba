import os
import boto3

def get_respond_config():
    """Obtiene el API token de AWS SSM solo una vez por ejecución."""
    ssm = boto3.client('ssm')
    token_param = os.environ['RESPOND_CONFIG_PARAMETER']
    response = ssm.get_parameter(Name=token_param, WithDecryption=True)
    return response['Parameter']['Value']