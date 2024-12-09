import os

def getArn(country):
    # Mapea el país al ARN correspondiente
    arn_map = {
        "CR": os.environ['secretRespondIO'],
        # "SV": os.environ['secretpostgresSV'],
        # "GT": os.environ['secretpostgresGT']
        # Añade más países y sus ARN correspondientes según sea necesario
    }

    # Devuelve el ARN para el país dado, si está en el mapa. Si no, devuelve None.
    return arn_map.get(country)