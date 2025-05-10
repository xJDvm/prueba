import json
import psycopg2.extras
import datetime
from respond_dbconnection.dbconnection import connect
from respond_dbconnection.secretManager import get_database_credentials

db_credentials = get_database_credentials()

def handle_create_contact(data):
    contact_id = str(data["contact"]["id"])
    contact_firstname = data["contact"]["firstName"]
    contact_lastname = data["contact"]["lastName"]
    contact_phone = data["contact"]["phone"]
    contact_email = data["contact"]["email"]
    assignee_id = str(data["contact"]["assignee"]["id"])
    assignee_firstname = data["contact"]["assignee"]["firstName"]
    assignee_lastname = data["contact"]["assignee"]["lastName"]
    assignee_email = data["contact"]["assignee"]["email"]
    contact_identification = data["contact"]["cedula"]
    agent_name = data["contact"]["agente"]
    agent_email = data["contact"]["correo_agente"]
    leader_name = data["contact"]["lider_agente"]
    leader_email = data["contact"]["correo_del_lider"]
    contact_province = data["contact"]["provincia"]
    contact_canton = data["contact"]["canton"]
    contact_district = data["contact"]["distrito"]
    contact_sector = data["contact"]["sector"]
    contact_bp_code = data["contact"]["bp"]
    contact_code_country = data["contact"]["countryCode"]
    
    dl_created_at = datetime.datetime.now().isoformat()
    dl_modified_at = datetime.datetime.now().isoformat()
    dl_condition = 'Active'

    conn = connect(db_credentials)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Buscar el contacto en la tabla respond_io.contacts
    select_query = "SELECT * FROM respond_io.contacts WHERE contact_id = %s"
    cursor.execute(select_query, (contact_id,))
    old_contact = cursor.fetchone()

    if old_contact:
        # Mover el contacto a la tabla respond_io.contacts_moved
        move_query = """
            INSERT INTO respond_io.contacts_moved (contact_id, contact_firstname, contact_lastname, contact_phone, contact_email, assignee_id, assignee_firstname, assignee_lastname, assignee_email, contact_identification, agent_name, agent_email, leader_name, leader_email, contact_province, contact_canton, contact_district, contact_sector, contact_bp_code, contact_code_country, dl_created_at, dl_modified_at, dl_condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Moved')
        """
        cursor.execute(move_query, (old_contact['contact_id'], old_contact['firstname'], old_contact['lastname'], old_contact['phone'], old_contact['email'], old_contact['assignee_id'], old_contact['assignee_firstname'], old_contact['assignee_lastname'], old_contact['assignee_email'], old_contact["contact_identification"], old_contact["agent_name"], old_contact["agent_email"], old_contact['leader_name'], old_contact["leader_email"], old_contact['contact_province'], old_contact['contact_canton'], old_contact['contact_district'], old_contact['contact_sector'], old_contact['contact_bp_code'], old_contact['contact_code_country'], old_contact['dl_created_at'], old_contact['dl_modified_at']))
        
        # Eliminar el contacto de la tabla respond_io.contacts
        delete_query = "DELETE FROM respond_io.contacts WHERE contact_id = %s"
        cursor.execute(delete_query, (contact_id,))

    # Insertar la nueva data en la tabla respond_io.contacts
    insert_query = """
        INSERT INTO respond_io.contacts (contact_id, contact_firstname, contact_lastname, contact_phone, contact_email, assignee_id, assignee_firstname, assignee_lastname, assignee_email, contact_identification, agent_name, agent_email, leader_name, leader_email, contact_province, contact_canton, contact_district, contact_sector, contact_bp_code, contact_code_country, dl_created_at, dl_modified_at, dl_condition)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (contact_id, contact_firstname, contact_lastname, contact_phone, contact_email, assignee_id, assignee_firstname, assignee_lastname, assignee_email, contact_identification, agent_name, agent_email, leader_name, leader_email, contact_province, contact_canton, contact_district, contact_sector, contact_bp_code, contact_code_country, dl_created_at, dl_modified_at, dl_condition))
    
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
            data = message
                        
            handle_create_contact(data)

        except Exception as e:
            print('Error procesando el mensaje')
            print(json.dumps({'ErrorRespond': str(e), 'Record': record}))
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    return sqs_batch_response