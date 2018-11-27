# coding:utf-8

#############################
#language pytho
#ec2 start/stop/status/SG Change
#############################

from __future__ import print_function

#import
import boto3
import json 
import pprint
import re
import logging
import os
import zlib
import urllib.request

logger = logging.getLogger()
logger.setLevel(logging.INFO)


#
ec2 = boto3.client('ec2')
ec3 = boto3.resource('ec2')

def dict_create():
    global instance_dict
    instance_dict = {}
    list1 = ec2.describe_instances(
        Filters = [{'Name':'tag:Slack','Values':['']}]
    )
    for IPRange in list1['Reservations']:
        for list3 in IPRange['Instances']:
            instanceid = list3['InstanceId']
            NSG = list3['NetworkInterfaces'][0]['Groups'][0]['GroupId']
            Status = list3["State"]['Name']
            instance = ec3.Instance(id=instanceid)
            name_tag = [x['Value'] for x in instance.tags if x['Key'] == 'Name']
            name = name_tag[0] if len(name_tag) else ''
            Dict_Key = ['instanceid','Name','Status','NSG']
            Dict_value = [instanceid,name,Status,NSG]
            instance_dict[name] = dict(zip(Dict_Key, Dict_value))
    return(instance_dict)

def Instance_Status(instance_dict):
    global message
    Instance_list = []
    for j in instance_dict.keys():
        Instance_list.append(j + ":" + instance_dict[j]['Status'] )
    message = ""
    message = '\n'.join(Instance_list)
    return(message)

def Instance_Action(Action,body,instance_dict):
    global message
    for j in instance_dict.keys():
        if instance_dict[j]['Name'] in body:
            Target = instance_dict[j]['Name']
            Targetid = instance_dict[Target]['instanceid']
        else :
            message = "No Target.You're probably misspelled."
            success = 1
        if 'start' in Action:
            print('start')
            try :
                response = ec2.start_instances(InstanceIds=[Targetid])
                Status = response['StartingInstances'][0]['CurrentState']['Name']
                success = 0
            except:
                message = "No Target.You're probably misspelled."            
        elif 'stop' in Action:
            print('stop')
            try:
                response = ec2.stop_instances(InstanceIds=[Targetid])
                pprint.pprint(response)
                Status = response['StoppingInstances'][0]['CurrentState']['Name']
                success = 0
            except:
                message = "No Target.You're probably misspelled."            
        else:
            message = "No Target.You're probably misspelled."
            success = 1
        if success == 0:
            message = "You " + Action + " " + Target + ". The current status is " + Status  + "."
    return(message)

def whoname(body):
    global user_id
    Body_list = [j for j in body.split('&') if 'user_id' in j]
    user_id = str(Body_list)
    user_id = user_id.replace('user_id=','')
    del_table = str.maketrans('', '', "[]'")
    user_id = user_id.translate(del_table)
    user_id = "<@" + user_id + ">"
    return(user_id)

def NGmessage():
    global message
    message = "$server (status | help | [server name] start | [server name] stop | ipshow | ipadd/ipdell [server name] -FromPort xx -IpRanges xx.xx.xx.xx/xx -Description xxxx"
    return(message)

def NSG_list(instance_dict):
    global message
    message = []
    for j in instance_dict.keys():
        Tergetid = instance_dict[j]['NSG']
        Describe_SG = ec2.describe_security_groups(GroupIds=[Tergetid])
        IpPermission = Describe_SG['SecurityGroups'][0]['IpPermissions']
        Count = 0
        for Iptable in IpPermission:
            IPRange = Iptable['IpRanges']
            Port_list = Iptable['FromPort']
            for k in IPRange:
                if Count is 0:
                    message.append('[ ' + j + ' ]' + '\n'+"SGID: "+  Tergetid)
                    Count = 1
                if 'Description' in k.keys():
                    message.append("Port :" + str(Port_list) + '\n' + k['CidrIp'] + " \n  Description :" +k['Description'] )  
                else:
                    message.append( k['CidrIp'] + "\n  Description :") 
    message = '\n'.join(message)
    print(message)
    return(message)

def Bodysplit(Action,body):
    global FPort
    global IpRange
    global Description
    Body_list = [j for j in body.split('&') if 'text' in j]
    Body_list = str(Body_list)
    del_table = str.maketrans('', '', "[]'")
    Body_list = Body_list.translate(del_table)
    Body_list = [j for j in str(Body_list).split('+')]
    print(Body_list)
    FromPortNum = (Body_list.index("-FromPort") + 1)
    FPort = int(Body_list[FromPortNum])
    IpPangesNum = (Body_list.index("-IpRanges") + 1)
    IpRange = (Body_list[IpPangesNum]).replace('%2F','/')
    print(IpRange)
    if 'ipadd' in  Action:
        DescriptionNum = (Body_list.index("-Description") + 1)
        Description = Body_list[DescriptionNum]
    else:
        Description = ""
    return(FPort,IpRange,Description)


def NSG_add(body,instance_dict,FPort,IpRange,Description):
    global message
    for j in instance_dict.keys():
        if instance_dict[j]['Name'] in body:
            Target = instance_dict[j]['Name']
            print(Target)
            Tergetid = instance_dict[j]['NSG']
            print(Tergetid)
            security_group = ec3.SecurityGroup(Tergetid)
        else:
            message = "No Target.You're probably misspelled."
    try:
        response = security_group.authorize_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'FromPort': FPort,
                    'IpProtocol': 'tcp',
                    'IpRanges': [
                        {
                            'CidrIp': IpRange,
                            'Description': Description
                            },
                            ],
                            'ToPort': FPort,
                            }])
        logger.info(response)
        message = "NSG add Success"
    except:
        message = "NSG add Failed"
    return(message)

def NSG_dell(body,instance_dict,FPort,IpRange):
    global message
    for j in instance_dict.keys():
        if instance_dict[j]['Name'] in body:
            Target = instance_dict[j]['Name']
            print(Target)
            Tergetid = instance_dict[j]['NSG']
            print(Tergetid)
            security_group = ec3.SecurityGroup(Tergetid)
        else:
            message = "No Target.You're probably misspelled."
    try:
        response = security_group.revoke_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'FromPort': FPort,
                    'IpProtocol': 'tcp',
                    'IpRanges': [
                        {
                            'CidrIp': IpRange
                            },
                            ],
                            'ToPort': FPort
                            }])
        logger.info(response)
        message = "NSG dell Success"
    except:
        message = "NSG dell Failed"
    return(message)

#メイン処理

def lambda_handler(event, context):
    dict_create()
    body = str(event['body'])
    logger.info(event)
    print(body)
    logger.info(instance_dict)
    if 'status' in body:
        logger.info(Instance_Status(instance_dict))
    elif 'start' in body:
        Action = 'start'
        logger.info(Instance_Action(Action,body,instance_dict))
    elif 'stop' in body:
        Action = 'stop'
        logger.info(Instance_Action(Action,body,instance_dict))
    elif 'ipshow' in body:
        logger.info(NSG_list(instance_dict))
    elif "ipadd" in body:
        print("ipadd")
        Action = "ipadd"
        logger.info(Bodysplit(Action,body))
        logger.info(NSG_add(body,instance_dict,FPort,IpRange,Description))
    elif "ipdell" in body:
        Action = 'ipdell'
        logger.info(Bodysplit(Action,body))
        logger.info(NSG_dell(body,instance_dict,FPort,IpRange))
    else:
        NGmessage()
    whoname(body)
    message_json = user_id + '\n' + message
    message_json = json.dumps({'text': message_json})
    pprint.pprint(message_json)
    return {
        'statusCode': 200,
        'body': message_json
    }