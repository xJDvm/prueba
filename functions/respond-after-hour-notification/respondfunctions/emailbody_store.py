import json
from int_respond_config import get_respond_config

respond_config = json.loads(get_respond_config())
respond_space = respond_config["respondSpace"]

def build_html_store(e):
    try:
        store = e.get('store', '')  # Nombre del analista
        client_name = e.get('clientName', '')  # Nombre del cliente
        client_email = e.get('clientEmail', '')  # Email del cliente
        client_phone = e.get('clientPhone', '')  # Teléfono del cliente
        client_id = e.get('clientId', '')  # ID del cliente
        cllient_identification = e.get('clientCedula', '')  # Cédula del cliente
        last_message_time = e.get('lastMessageTime', '')
        incoming_messages = e.get('incomingMessages', '').split(" - ") or ""
        incoming_photos = e.get('incomingPhotos', '').split(',') or ""

        last_messages = incoming_messages
        message_bubbles = ""
        total_length = 0
        photos_html = ""
        image_adviser = f'''
            <span style="background:transparent">
                En caso de cualquier inconveniente por favor contactar a soporte <br>.
                <a href="https://app.respond.io/space/{respond_space}/inbox/{client_id}" style="text-decoration:underline;color:#0b5394;">Abrir conversación</a>
            </span>
        '''

        # Concatenar los mensajes hasta alcanzar 2000 caracteres
        for message in last_messages:
            if total_length + len(message) <= 2000:
                message_bubbles += f'''
                    <div style="margin-left:15px; margin-top: 5px; padding: 5px; background-color: #e0e0e0; border-radius: 15px;">
                        <div style="padding: 5px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); font-style: italic;">
                            {message}
                        </div>
                    </div>
                '''
                total_length += len(message)
            else:
                break  # Si el total de caracteres supera 2000, para de agregar mensajes

        # Construir las imágenes HTML
        if incoming_photos != [""]:
            photos_html = ''.join([f'''
                <div style="position: relative; width: 100%; max-width: 500px; height: 300px; margin-bottom: 20px; display: inline-block; text-align: center;">
                    <img src="{photo}" style="width: 100%; height: 100%; object-fit: cover; display: block; margin: 0 auto;">
                </div>
            ''' for photo in incoming_photos])

            image_adviser = f'''
                <span style="background:transparent">
                    A continuación se anexan las imágenes enviadas por el cliente:<br>
                    <a href="https://app.respond.io/space/{respond_space}/inbox/{client_id}" style="text-decoration:underline;color:#0b5394;">Abrir conversación</a>
                </span>
            '''

        body_html = f"""
            <html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
                <head>
                <meta charset="UTF-8">
                <meta content="width=device-width, initial-scale=1" name="viewport">
                <meta name="x-apple-disable-message-reformatting">
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                <meta content="telephone=no" name="format-detection">
                <title></title>
                <!--[if (mso 16)]>
                <style type="text/css">
                a {{text-decoration: none;}}
                </style>
                <![endif]-->
                <!--[if gte mso 9]><style>sup {{ font-size: 100% !important; }}</style><![endif]-->
                <!--[if gte mso 9]>
            <noscript>
                    <xml>
                        <o:OfficeDocumentSettings>
                        <o:AllowPNG></o:AllowPNG>
                        <o:PixelsPerInch>96</o:PixelsPerInch>
                        </o:OfficeDocumentSettings>
                    </xml>
                    </noscript>
            <![endif]-->
                <!--[if mso]><xml>
                <w:WordDocument xmlns:w="urn:schemas-microsoft-com:office:word">
                    <w:DontUseAdvancedTypographyReadingMail/>
                </w:WordDocument>
                </xml><![endif]-->
                </head>
                <body class="body">
                <div dir="ltr" class="es-wrapper-color">
                    <!--[if gte mso 9]>
                    <v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
                    <v:fill type="tile" color="#f6f6f6"></v:fill>
                    </v:background>
                <![endif]-->
                    <table width="100%" cellspacing="0" cellpadding="0" class="es-wrapper">
                    <tbody>
                        <tr>
                        <td valign="top" class="esd-email-paddings">
                            <table cellspacing="0" cellpadding="0" align="center" class="esd-header-popover es-header">
                            <tbody>
                                <tr>
                                <td align="center" bgcolor="transparent" class="esd-stripe" style="background-color:transparent">
                                    <table width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center" class="es-header-body">
                                    <tbody>
                                        <tr>
                                        <td align="left" bgcolor="#ffffff" class="esd-structure es-p20" style="background-color:#ffffff">
                                            <!--[if mso]><table width="560" cellpadding="0" cellspacing="0"><tr><td width="93" valign="top"><![endif]-->
                                            <table cellspacing="0" cellpadding="0" align="left" class="es-left">
                                            <tbody>
                                                <tr>
                                                <td width="93" valign="top" align="center" class="es-m-p0r es-m-p20b esd-container-frame">
                                                    <table width="100%" cellspacing="0" cellpadding="0">
                                                    <tbody>
                                                        <tr>
                                                        <td align="left" class="esd-block-image es-m-txt-c" style="font-size:0">
                                                            <a target="_blank">
                                                            <img src="https://ebowiic.stripocdn.email/content/guids/CABINET_5ec98a9c69d68e739e9927b98229fec056175cbadea6e9455bb74959855b8f02/images/epa_logo_1.png" alt="" width="93" class="img-5001">
                                                            </a>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                            <!--[if mso]></td><td width="20"></td><td width="447" valign="top"><![endif]-->
                                            <table cellspacing="0" cellpadding="0" align="right" class="es-right">
                                            <tbody>
                                                <tr>
                                                <td width="447" align="left" class="esd-container-frame">
                                                    <table width="100%" cellspacing="0" cellpadding="0">
                                                    <tbody>
                                                        <tr>
                                                        <td align="right" class="esd-block-text es-text-6853">
                                                            <h3 class="es-m-txt-c" style="color:#0b5394;font-family:verdana,geneva,sans-serif;font-size:18px;line-height:150%">

                                                            <strong>Respond.io | Mensaje fuera de horario {store}</strong>
                                                            </h3>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                            <!--[if mso]></td></tr></table><![endif]-->
                                        </td>
                                        </tr>
                                    </tbody>
                                    </table>
                                </td>
                                </tr>
                            </tbody>
                            </table>
                            <table cellspacing="0" cellpadding="0" align="center" class="es-content">
                            <tbody>
                                <tr>
                                <td align="center" bgcolor="transparent" class="esd-stripe">
                                    <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" align="center" class="es-content-body">
                                    <tbody>
                                        <tr>
                                        <td align="left" class="esd-structure es-p10">
                                            <table cellpadding="0" cellspacing="0">
                                            <tbody>
                                                <tr>
                                                <td width="580" align="left" class="esd-container-frame">
                                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation">
                                                    <tbody>
                                                        <tr>
                                                        <td align="center" class="esd-block-spacer" style="font-size:0">
                                                            <table border="0" width="100%" height="100%" cellpadding="0" cellspacing="0" class="es-spacer">
                                                            <tbody>
                                                                <tr>
                                                                <td style="border-bottom:1px solid #cccccc;background:none;height:1px;width:100%;margin:0px 0px 0px 0px">
                                                                </td>
                                                                </tr>
                                                            </tbody>
                                                            </table>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                    </tbody>
                                    </table>
                                </td>
                                </tr>
                            </tbody>
                            </table>
                            <table cellspacing="0" cellpadding="0" align="center" class="es-content">
                            <tbody>
                                <tr>
                                <td align="center" bgcolor="transparent" class="esd-stripe">
                                    <table bgcolor="#000000" align="center" width="600" cellpadding="0" cellspacing="0" class="es-content-body" style="background-color:#000000">
                                    <tbody>
                                    </tbody>
                                    </table>
                                </td>
                                </tr>
                            </tbody>
                            </table>
                            <table cellspacing="0" cellpadding="0" align="center" class="es-content">
                            <tbody>
                                <tr>
                                <td align="center" bgcolor="transparent" class="esd-stripe">
                                    <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" align="center" class="es-content-body">
                                    <tbody>
                                        <tr>
                                        <td align="left" class="esd-structure es-p20r es-p20l es-p15b es-p15t">
                                            <table cellpadding="0" cellspacing="0">
                                            <tbody>
                                                <tr>
                                                <td width="560" align="left" class="esd-container-frame">
                                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation">
                                                    <tbody>
                                                        <tr>
                                                        <td align="center" class="esd-block-text">
                                                            <p align="left">
                                                            Estimado equipo de tienda <strong>{store}</strong>,
                                                            </p>
                                                            <p align="left">
                                                            Este correo es para para informarles que se ha recibido un mensaje fuera del horario de atención en la oficina central, por el cliente:
                                                            </p>
                                                            <ul style="text-align: left; list-style-position: inside; padding-left: 0">
                                                            <li> <strong>Cliente:</strong> {client_name}</li>
                                                            <li> <strong>Cedula:</strong> {cllient_identification}</li>
                                                            <li> <strong>Email:</strong> {client_email}</li>
                                                            <li> <strong>Teléfono:</strong> {client_phone}</li>
                                                            </ul>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                        <tr>
                                        <td align="left" class="esd-structure es-p20t es-p20r es-p20l">
                                            <table cellspacing="0" width="100%" cellpadding="0">
                                            <tbody>
                                                <tr>
                                                <td width="560" align="left" class="esd-container-frame">
                                                    <table width="100%" role="presentation" cellpadding="0" cellspacing="0">
                                                    <tbody>
                                                        <tr>
                                                        <td align="left" class="esd-block-html">
                                                            <table cellpadding="0" cellspacing="0" style="width: 100%; font-family: Arial; margin: 10px;">
                                                            <tr>
                                                                <td align="left" class="esd-block-html">
                                                                <table cellpadding="0" cellspacing="0" style="width: 100%; font-family: Arial; margin: 10px;">
                                                                    <tr>
                                                                    <td style="width: 50px; vertical-align: middle;">
                                                                        <img src="https://ebowiic.stripocdn.email/content/guids/CABINET_f20f14b5288b802be785dfb2876491a9fcc4cf8cf2363c84f7b7fe91e81343f6/images/user_account_profile2256.png" 
                                                                            alt="Imagen de perfil" 
                                                                            style="width: 40px; height: 40px; border-radius: 50%; display: inline-block;">
                                                                    </td>
                                                                    <td style="vertical-align: middle; padding-left: 10px;">
                                                                        <div style="font-weight: bold; display: inline-block;">
                                                                        {client_name}
                                                                        </div>
                                                                        <div style="color: gray; font-style: italic;">
                                                                            (Inició la conversacion: {last_message_time})
                                                                        </div>
                                                                    </td>
                                                                    </tr>
                                                                </table>
                                                                </td>
                                                            </tr>
                                                            <tr>
                                                                <td>
                                                                {message_bubbles}
                                                                </td>
                                                            </tr>
                                                            </table>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                        <tr>
                                        <td align="left" class="esd-structure es-p20r es-p20l es-p10t es-p5b">
                                            <table cellpadding="0" cellspacing="0">
                                            <tbody>
                                                <tr>
                                                <td width="560" align="left" class="esd-container-frame">
                                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation">
                                                    <tbody>
                                                        <tr>
                                                        <td align="left" class="esd-block-text">
                                                            <p>
                                                            Por favor, asegúrense de gestionar estas solicitudes pendientes en el menor tiempo posible para mantener el estándar de servicio esperado.
                                                            </p>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                    </tbody>
                                    </table>
                                </td>
                                </tr>
                            </tbody>
                            </table>
                            <table cellspacing="0" cellpadding="0" align="center" class="es-content">
                            <tbody>
                                <tr>
                                <td align="center" bgcolor="transparent" class="esd-stripe">
                                    <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" align="center" class="es-content-body">
                                    <tbody>
                                        <tr>
                                        <td align="left" class="esd-structure es-p20r es-p20l es-p10t es-p10b">
                                            <table cellpadding="0" cellspacing="0">
                                            <tbody>
                                                <tr>
                                                <td width="560" align="left" class="esd-container-frame">
                                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation">
                                                    <tbody>
                                                        <tr>
                                                        <td align="center" class="esd-block-spacer es-p5" style="font-size:0">
                                                            <table border="0" width="100%" height="100%" cellpadding="0" cellspacing="0" class="es-spacer">
                                                            <tbody>
                                                                <tr>
                                                                <td style="border-bottom:1px solid #cccccc;background:none;height:1px;width:100%;margin:0px 0px 0px 0px">
                                                                </td>
                                                                </tr>
                                                            </tbody>
                                                            </table>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                        <br>
                                        <tr>
                                        <td align="left" class="esd-structure es-p20t es-p20r es-p20l">
                                            <table cellspacing="0" width="100%" cellpadding="0">
                                            <tbody>
                                                <tr>
                                                <td width="560" align="left" class="esd-container-frame">
                                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation">
                                                    <tbody>
                                                        <tr>
                                                        <td align="center" bgcolor="#efefef" class="esd-block-text es-p10t es-p10b es-p20l es-p20r" style="margin-top:20px;border-radius:8px;border:2px #3d85c6">
                                                            <p class="es-m-txt-c" style="color:#0b5394;line-height:150% !important">
                                                            {image_adviser}
                                                            </p>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                        <tr>
                                        <td align="left" class="esd-structure es-p20t es-p20r es-p20l">
                                            <table cellspacing="0" width="100%" cellpadding="0">
                                            <tbody>
                                                <tr>
                                                <td width="560" align="left" class="esd-container-frame">
                                                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                                    <tbody>
                                                        <tr>
                                                        <td align="center" class="esd-block-html">
                                                            <p class="photos-container" style="margin-top: 5%; text-align: center">
                                                            {photos_html}
                                                            </p>
                                                        </td>
                                                        </tr>
                                                    </tbody>
                                                    </table>
                                                </td>
                                                </tr>
                                            </tbody>
                                            </table>
                                        </td>
                                        </tr>
                                    </tbody>
                                    </table>
                                </td>
                                </tr>
                            </tbody>
                            </table>
                        </td>
                        </tr>
                    </tbody>
                    </table>
                </div>
                </body>
            </html>"""


        return body_html

    except Exception as e:
        print(json.dumps({'ErrorRespond': str(e)}))
        return ""