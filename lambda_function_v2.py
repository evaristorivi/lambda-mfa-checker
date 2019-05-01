#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Evaristo R. Rivieccio Vega - Cloud, Middleware y Sistemas - L1
#evaristorivieccio@gmail.com

import sys, traceback
import boto3
from dateutil.parser import parse
import datetime

##CONFIG##
#################################################################################################

# CUENTA Solo afecta a la información de los emails enviados
CUENTA='<<nombre de cuenta de aws>>'

#True o False
DEBUG=True

#################################################################################################
REMITENTE='<<nombre@dominio.com>>'
DESTINATARIOEMAIL='<<nombre@dominio.com>>'
ASUNTOINFORME="[MFA - INFO] Total de usuarios sin MFA en la cuenta de AWS de " + CUENTA
EMAILDEBUG='<<nombre@dominio.com>>'
#MÁXIMO DE DIAS SIN MFA PERMITIDOS
MAXNOMFA=120
DOMINIOEMAIL='<<@dominio.com>>'
ASUNTODEMENSAJE="[MFA - CONSEJO] Mejora la seguridad de la cuenta de AWS de " + CUENTA 
MENSAJE='Loremp ipsum.\n\nVestibulum a leo ornare, fermentum justo sed, imperdiet augue. Cras sed justo tincidunt, molestie risus at, aliquet elit. Suspendisse nec interdum orci, in ullamcorper ex. Integer in fringilla nisl, eu faucibus nisl. Aliquam vulputate aliquam hendrerit. Quisque lacus lacus, suscipit at risus non, malesuada fermentum dui. Maecenas eleifend, libero ac gravida vehicula, erat est auctor ex, ut elementum velit lorem ac enim. Cras diam magna, ornare id neque ac, pretium accumsan massa. In lacus augue, ultrices vel justo sed, accumsan vulputate neque.\n\nLorem ipsum.'

#################################################################################################
#################################################################################################
#################################################################################################

if DEBUG is True:
    DESTINATARIOEMAIL=EMAILDEBUG

#Crear una función para enviar correo:
def send_email(email_subject, email_body, email_to):
        ses = boto3.client('ses')
        email_from = REMITENTE
        email_to = email_to
        email_subject = email_subject
        email_body = email_body
        response = ses.send_email(
            Source = email_from,
            Destination = {
                'ToAddresses': [
                    email_to,
                ]
            },
            Message = {
                'Subject': {
                    'Data': email_subject
                },
                'Body': {
                    'Text': {
                        'Data': email_body
                    }
                }
            }
        )
 
def lambda_handler(event, context):
    try:
        #Control de errores, MAXNOMFA debe de ser un Int
        if not type(MAXNOMFA) == int:
            print 'Variable MAXNOMFA debe de ser un Int'
            sys.exit(1)

        #Función que calcula los días que han pasado desde una fecha dada
        def days_old(date):
            get_date_obj = parse(date)
            date_obj = get_date_obj.replace(tzinfo=None)
            diff = datetime.datetime.now() - date_obj
            return diff.days

        client                  = boto3.client('iam')
        sns                     = boto3.client('sns')
        response                = client.list_users()
        userVirtualMfa          = client.list_virtual_mfa_devices()
        mfaNotEnabled           = []
        mfaNotEnabledymasdeX    = []
        mfaNotEnabledymasdeXarray = []
        physicalStringmasd30    =   ""
        virtualEnabled          = []
        physicalString          = ''

        #Recorre el mfa virtual para encontrar usuarios que realmente lo tengan
        for virtual in userVirtualMfa['VirtualMFADevices']:
            try:
                virtualEnabled.append(virtual['User']['UserName'])
            except KeyError:
                continue
                
        # recorre los usuarios para encontrar un MFA fisico ### response['Users']
        for user in response['Users']:
            if DOMINIOEMAIL in str(user):
                userMfa  = client.list_mfa_devices(UserName=user['UserName'])
                if len(userMfa['MFADevices']) == 0:
                    if user['UserName'] not in virtualEnabled:
                        mfaNotEnabled.append(user['UserName'] +  " con " + str(days_old(str(user['CreateDate']))) + " días de antiguedad")
                    if user['UserName'] not in virtualEnabled and days_old(str(user['CreateDate'])) > MAXNOMFA:
                        mfaNotEnabledymasdeXarray.append(user['UserName'])
                        mfaNotEnabledymasdeX.append(user['UserName'] +  " con " + str(days_old(str(user['CreateDate']))) + " días de antiguedad")

        if len(mfaNotEnabled) > 0:
            physicalString = 'Los siguientes usuarios no tienen MFA habilitado en la cuenta de AWS de ' + CUENTA + ' : \n\n' + '\n'.join(mfaNotEnabled)
        else:
            physicalString = 'Todos los usuarios tienen MFA habilitado en la cuenta de AWS de ' + CUENTA

        if len(mfaNotEnabledymasdeX) > 0:
            physicalStringmasd30 = ' \n \nDe los cuales han superado el tope máximo: (' + str(MAXNOMFA) + ' días) \n\n' + '\n'.join(mfaNotEnabledymasdeX)
            for cadausernotmfa in mfaNotEnabledymasdeXarray:
                email_to=cadausernotmfa
                if DEBUG is True:
                    email_to=EMAILDEBUG
                #print email_to
                send_email( ASUNTODEMENSAJE , MENSAJE , email_to )
            #Para DEBUG y que no lleguen más de una notificación
            #send_email( ASUNTODEMENSAJE , MENSAJE , email_to )

        #EL EMAIL DEL DESTINATARIO DEL INFORME GENERAL DE USUARIOS SIN MFA
        email_to = DESTINATARIOEMAIL
        send_email( ASUNTOINFORME , physicalString + physicalStringmasd30 , email_to )

    except:
        #Control de errores de la Lambda:
        email_to = EMAILDEBUG
        send_email("[LAMBDA MFA_CHECK - FAILURE]", "La Lambda MFA_CHECK se ha lanzado con errores.", email_to)
