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
import logging
import os
import zlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)


#
ec2 = boto3.client('ec2')
ec3 = boto3.resource('ec2')
instance_dict = {}
message = {}
Instance_list = []
Body_list = []

#メイン処理

def dict_create():
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

def lambda_handler(event, context):
    dict_create()
    body = str(event['body'])
    logger.info(body)
    print(body)
    if 'status' in body:
        logger.info("MSG:StatusAction")
        list1 = instance_dict.keys()
        for j in list1:
            logger.info(j)
            Instance_list.append(j + ":" + instance_dict[j]['Status'] )
        message = '\n'.join(Instance_list)
    elif 'start' in body:
        Action = "start"
        list1 = instance_dict.keys()
        for j in list1:
            if j in body:
                Target = instance_dict[j]['Name']
                Targetid = instance_dict[Target]['instanceid']
                response = ec2.start_instances(InstanceIds=[Targetid])
                pprint.pprint(response)
                if response is not None:
                    logger.info(response)
                    message = Action + " instance " + Target
    elif 'stop' in body:
        Action = "stop"
        list1 = instance_dict.keys()
        print(list1)
        for j in list1:
            if j in body:
                Target = instance_dict[j]['Name']
                Targetid = instance_dict[Target]['instanceid']
                response = ec2.stop_instances(InstanceIds=[Targetid])
                pprint.pprint(response)
                if response is not None:
                    logger.info(response)
                    message = Action + " instance " + Target
    else :
        message = "usage: $server (status | help | [server name] start | [server name] stop)"
    Body_list = [j for j in body.split('&') if 'user_id' in j]
    user_id = str(Body_list)
    user_id = user_id.replace('user_id=','')
    user_id = user_id.replace('[','')
    user_id = user_id.replace(']','')
    user_id = user_id.replace("'","")
    user_id = "<@" + user_id + ">"
    message = user_id + '\n' + message
    message = json.dumps({'text': message})
    return {
        'statusCode': 200,
        'body': message
    }