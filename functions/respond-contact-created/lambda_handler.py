import json
import psycopg2.extras
import datetime
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

db_credentials = get_database_credentials()

def handle_create_contact(data):
    contact_id = data["contact"]["id"]
    firstname = data["contact"]["firstName"]
    lastname = data["contact"]["lastName"]
    phone = data["contact"]["phone"]
    email = data["contact"]["email"]
    assignee_id = data["contact"]["assignee"]["id"]
    assignee_firstname = data["contact"]["assignee"]["firstName"]
    assignee_lastname = data["contact"]["assignee"]["lastName"]
    assignee_email = data["contact"]["assignee"]["email"]
    client_identification = data["contact"]["cedula"]
    asesor_name = data["contact"]["agente"]
    asesor_email = data["contact"]["correo_agente"]
    lider_email = data["contact"]["correo_del_lider"]
    
    dl_created_at = datetime.datetime.now().isoformat()
    dl_modified_at = datetime.datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    insert_query = """
        INSERT INTO respond_io.contacts (contact_id, firstname, lastname, phone, email, assignee_id, assignee_firstname, assignee_lastname, assignee_email, client_identification, asesor_name, asesor_email, lider_email, dl_created_at, dl_modified_at, dl_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, firstname, lastname, phone, email, assignee_id, assignee_firstname, assignee_lastname, assignee_email, client_identification, asesor_name, asesor_email, lider_email, dl_created_at, dl_modified_at, dl_condition))
    conn.commit()
    cursor.close()
    conn.close()
    print("Datos insertados correctamente en la tabla respond_io.contacts")


def lambda_handler(event, context):
    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            message = json.loads(body["Message"])
            data = message["detail"]
                        
            handle_create_contact(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(e)
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response