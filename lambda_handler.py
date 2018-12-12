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
    global message 
    message = ""
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
    NSG_dict = {}
    message = []
    temp_fields = []
    temp_list2 = []
    for j in instance_dict.keys():
        Tergetid = instance_dict[j]['NSG']
        Describe_SG = ec2.describe_security_groups(GroupIds=[Tergetid])
        IpPermission = Describe_SG['SecurityGroups'][0]['IpPermissions']
        Count = 0
        for Iptable in IpPermission:
            IPRange = Iptable['IpRanges']
            #Count = Count + i
            if Iptable['FromPort'] is 0:
                PortNo = "0"
            else:
                PortNo = str(Iptable['FromPort'])
            for k in IPRange:
                CiderIp = k['CidrIp']
                if 'Description' not in k.keys():
                    Description = '-'
                else:
                    Description = k['Description']
                temp_list =(CiderIp,Description)
                if j not in NSG_dict.keys():
                    NSG_dict.setdefault(PortNo,temp_list)
                else:
                    NSG_dict[PortNo].extend(temp_list)
                temp_fields = [{
                    "title":CiderIp,
                    "value":"PortNo:" + PortNo +'\n' + "Description:" + Description,
                    "short": "true"
                }]
                temp_list2.extend(temp_fields)
        if Count is 0:
            temp_message = [
                {
                    "fallback":"SecrutiGroup List",
                    "pretext": j,
                    "color":"#A9E2F3",
                    "fields":temp_list2
                    }
                    ]
            Count = 1
        else:
            temp_message = [
                {
                    "fallback":"SecrutiGroup List",
                    "color":"#A9E2F3",
                    "fields":temp_list2
                    }
                    ]                        
        message.extend(temp_message)
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
    logger.info("Event: " + str(body))
    logger.info("Event: " + str(instance_dict))
    if 'status' in body:
        Instance_Status(instance_dict)
        logger.info("Action : Status ,Event: "+ str(message))
    elif 'start' in body:
        Action = 'start'
        Instance_Action(Action,body,instance_dict)
        logger.info("Action : Start ,Event: "+ str(message))
    elif 'stop' in body:
        Action = 'stop'
        Instance_Action(Action,body,instance_dict)
        logger.info("Action : Stop ,Event: "+ str(message))
    elif 'ipshow' in body:
        NSG_list(instance_dict)
        logger.info("Action : NSG_list ,Event: "+ str(message))
    elif "ipadd" in body:
        Action = "ipadd"
        Bodysplit(Action,body)
        logger.info("Action : ipadd ,Event : Fport" + str(FPort) +", IpRange :" + str(IpRange) + ", Description :" + str(Description))
        NSG_add(body,instance_dict,FPort,IpRange,Description)
        logger.info("Event : " + str(message))
    elif "ipdell" in body:
        Action = 'ipdell'
        Bodysplit(Action,body)
        logger.info("Action : ipadd ,Event : Fport" + str(FPort) +", IpRange :" + str(IpRange) + ", Description :" + str(Description))
        NSG_dell(body,instance_dict,FPort,IpRange)
        logger.info("Event : " + str(message))
    else:
        NGmessage()
        logger.info("Event :" + str(message))
    whoname(body)
    if "ipshow" in body:
        message_json = json.dumps(
            {
                'text': user_id,
                'attachments': message}
            )
    else:
        message_json = user_id + '\n' + message    
        message_json = json.dumps({'text': message_json})
    logger.info("Event :" + str(message_json))
    return {
        'statusCode': 200,
        'body': message_json
    }