import json
import psycopg2.extras
import datetime
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

db_credentials = get_database_credentials()


def handle_create_contact(data):
    contact_id = str(data["contact"]["id"])
    # status = data["contact"]["status"]
    assignee_id = str(data["contact"]["assignee"]["id"])
    assignee_firstname = data["contact"]["assignee"]["firstName"]
    assignee_lastname = data["contact"]["assignee"]["lastName"]
    assignee_email = data["contact"]["assignee"]["email"]
    
    dl_modified_at = datetime.datetime.now().isoformat()

    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Buscar el contacto en la tabla respond_io.contacts
    select_query = "SELECT * FROM respond_io.contacts WHERE contact_id = %s"
    cursor.execute(select_query, (contact_id,))
    old_contact = cursor.fetchone()

    if old_contact:
        insert_query = """
            INSERT INTO respond_io.contacts_moved (contact_id, contact_firstname, contact_lastname, contact_phone, contact_email, assignee_id, assignee_firstname, assignee_lastname, assignee_email, contact_identification, agent_name, agent_email, leader_name, leader_email, contact_province, contact_canton, contact_district, contact_sector, contact_bp_code, contact_code_country, dl_created_at, dl_modified_at, dl_condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Moved')
        """
        cursor.execute(insert_query, (old_contact['contact_id'], old_contact['firstname'], old_contact['lastname'], old_contact['phone'], old_contact['email'], old_contact['assignee_id'], old_contact['assignee_firstname'], old_contact['assignee_lastname'], old_contact['assignee_email'], old_contact["contact_identification"], old_contact["agent_name"], old_contact["agent_email"], old_contact['leader_name'], old_contact["leader_email"], old_contact['contact_province'], old_contact['contact_canton'], old_contact['contact_district'], old_contact['contact_sector'], old_contact['contact_bp_code'], old_contact['contact_code_country'], old_contact['dl_created_at'], old_contact['dl_modified_at']))
        
        
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
            data = message
                        
            handle_create_contact(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response