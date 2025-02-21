import json
import psycopg2.extras
import datetime
from dbconnection.dbconnection import connect


def handle_create_contact(data):
    contact_id = str(data["contact"]["id"])
    # status = data["contact"]["status"]
    assignee_id = str(data["contact"]["assignee"]["id"])
    assignee_firstname = data["contact"]["assignee"]["firstName"]
    assignee_lastname = data["contact"]["assignee"]["lastName"]
    assignee_email = data["contact"]["assignee"]["email"]
    
    dl_modified_at = datetime.datetime.now().isoformat()

    conn = connect()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Buscar el contacto en la tabla respond_io.contacts
    select_query = "SELECT * FROM respond_io.contacts WHERE contact_id = %s"
    cursor.execute(select_query, (contact_id,))
    contact = cursor.fetchone()

    if contact:
        insert_query = """
            INSERT INTO respond_io.contacts_moved (contact_id, firstname, lastname, phone, email, status, assignee_id, assignee_firstname, assignee_lastname, assignee_email, client_identification, asesor_name, asesor_email, lider_email, dl_created_at, dl_modified_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            contact['contact_id'], 
            contact['firstname'], 
            contact['lastname'], 
            contact['phone'], 
            contact['email'], 
            contact['status'],
            contact['assignee_id'],
            contact['assignee_firstname'],
            contact['assignee_lastname'],
            contact['assignee_email'], 
            contact['client_identification'], 
            contact['asesor_name'], 
            contact['asesor_email'], 
            contact['lider_email'],
            contact['dl_created_at'], 
            dl_modified_at
        ))
        
        
        # Actualizar los datos del assignee en la tabla respond_io.contacts
        update_query = """
            UPDATE respond_io.contacts
            SET assignee_id = %s, assignee_firstname = %s, assignee_lastname = %s, assignee_email = %s, dl_modified_at = %s
            WHERE contact_id = %s
        """
        cursor.execute(update_query, (assignee_id, assignee_firstname, assignee_lastname, assignee_email, dl_modified_at, contact_id))
    else:
        print(f"No se encontró el contacto {contact_id} en la tabla respond_io.contacts, no se puede actualizar")

    conn.commit()
    cursor.close()
    conn.close()
    # print("Datos actualizados correctamente en la tabla respond_io.contacts")


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