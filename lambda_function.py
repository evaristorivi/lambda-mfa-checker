#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys, traceback
import boto3
from dateutil.parser import parse
import datetime
from pprint import pprint

def lambda_handler(context,event):

    #MÁXIMO DE DIAS SIN MFA PERMITIDOS
    maxnomfa=120

    #Control de errores, maxnomfa debe de ser un Int
    if not type(maxnomfa) == int:
        print 'Variable maxnomfa debe de ser un Int'
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
    virtualEnabled          = []
    physicalString          = ''

    # recorre el mfa virtual para encontrar usuarios que realmente lo tengan
    for virtual in userVirtualMfa['VirtualMFADevices']:
        virtualEnabled.append(virtual['User']['UserName'])
            
    # recorre los usuarios para encontrar un MFA fisico ### response['Users'] no existe por ahora.
    for user in response['Users']:
        userMfa  = client.list_mfa_devices(UserName=user['UserName'])
        
        if len(userMfa['MFADevices']) == 0:
            if user['UserName'] not in virtualEnabled:
                mfaNotEnabled.append(user['UserName'] +  " con " + str(days_old(str(user['CreateDate']))) + " días de antiguedad")
            if user['UserName'] not in virtualEnabled and days_old(str(user['CreateDate'])) > maxnomfa:
                mfaNotEnabledymasdeX.append(user['UserName'] +  " con " + str(days_old(str(user['CreateDate']))) + " días de antiguedad")



    if len(mfaNotEnabled) > 0:
        physicalString = 'MFA no habilitado en los siguientes usuarios: \n\n' + '\n'.join(mfaNotEnabled)
    else:
        physicalString = 'Todos los usuarios tienen MFA habilitado.'

    if len(mfaNotEnabledymasdeX) > 0:
        physicalStringmasd30 = 'Han pasado más de ' + str(maxnomfa) + ' días y los siguientes usuarios tienen MFA deshabilitado: \n\n' + '\n'.join(mfaNotEnabledymasdeX)
        response = sns.publish(
        TopicArn='<<TU ARN TOPIC SNS AQUÍ>>',
        Message= physicalStringmasd30,
        Subject='Usuarios con más de ' + str(maxnomfa) + ' días sin MFA',
        )

    #print physicalString
    #print physicalStringmasd30

    response = sns.publish(
        TopicArn='<<TU ARN TOPIC SNS AQUÍ>>',
        Message= physicalString,
        Subject='Total de usuarios sin MFA',
    )

#return (mfaNotEnabled, mfaNotEnabledymasdeX)




