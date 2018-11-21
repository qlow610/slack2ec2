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

"""
インスタンスリストの作成処理
"""

def dict_create():
    global instance_dict
    instance_dict = {}
    list1 = ec2.describe_instances(
        Filters = [{'Name':'tag:Slack','Values':['']}]
    )
    for list2 in list1['Reservations']:
        for list3 in list2['Instances']:
            instanceid = list3['InstanceId']
            Status = list3["State"]['Name']
            instance = ec3.Instance(id=instanceid)
            name_tag = [x['Value'] for x in instance.tags if x['Key'] == 'Name']
            name = name_tag[0] if len(name_tag) else ''
            Dict_Key = ['instanceid','Name','Status']
            Dict_value = [instanceid,name,Status]
            instance_dict[name] = dict(zip(Dict_Key, Dict_value))
    return(instance_dict)

def Instance_Status(instance_dict):
    global message
    list1 = instance_dict.keys()
    Instance_list = []
    for j in list1:
        Instance_list.append(j + ":" + instance_dict[j]['Status'] )
    message = ""
    message = '\n'.join(Instance_list)
    return(message)

def Instance_Action(Action,body,instance_dict):
    global message
    list1 = instance_dict.keys()
    for j in list1:
        if instance_dict[j]['Name'] in body:
            Target = instance_dict[j]['Name']
            Targetid = instance_dict[Target]['instanceid']
            if 'start' in Action:
                response = ec2.start_instances(InstanceIds=[Targetid])
                pprint.pprint(response)
            elif 'stop' in Action:
                response = ec2.stop_instances(InstanceIds=[Targetid])
                pprint.pprint(response)
            Status = response['StoppingInstances'][0]['CurrentState']['Name']
            message = "You " + Action + " " + Target + ". The current status is " + Status  + "."
        else:
            message = "No Target.You're probably misspelled."
    return(message)

def whoname(body):
    global user_id
    Body_list = [j for j in body.split('&') if 'user_id' in j]
    user_id = str(Body_list)
    user_id = user_id.replace('user_id=','')
    user_id = user_id.replace('[','')
    user_id = user_id.replace(']','')
    user_id = user_id.replace("'","")
    user_id = "<@" + user_id + ">"
    return(user_id)

#メイン処理

def lambda_handler(event, context):
    dict_create()
    body = str(event['body'])
    logger.info(event)
    logger.info(instance_dict)
    if 'status' in body:
        Instance_Status(instance_dict)
    elif 'start' in body:
        Action = 'start'
        Instance_Action(Action,body,instance_dict)
    elif 'stop' in body:
        Action = 'stop'
        Instance_Action(Action,body,instance_dict)
    whoname(body)
    message_json = user_id + '\n' + message
    message_json = json.dumps({'text': message_json})
    return {
        'statusCode': 200,
        'body': message_json
    }