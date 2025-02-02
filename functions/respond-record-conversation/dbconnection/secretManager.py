import boto3
import json

def getSecret(region_name, secret_name):
    # Create a Secrets Manager client
    client = boto3.client('secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        print("Secret retrieved successfully")  # Debug
    except Exception as e:
        print(f"Error retrieving secret: {e}")  # Debug
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response.get('SecretString')
    if not secret:
        raise ValueError("SecretString is empty or not found in the response")

    return secret