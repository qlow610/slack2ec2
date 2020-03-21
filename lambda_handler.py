"""This is Slack to Ec2/NSG operating """
#############################
#language pytho
#ec2 start/stop/status/SG Change
#############################

from __future__ import print_function

#import
from pprint import pprint
import boto3
import json

#
EC2 = boto3.client('ec2')


def dict_create():
    """
    Instance Dict Create
    """
    ins_dict = {}
    temp_list1 = EC2.describe_instances()
    for iprange in temp_list1['Reservations']:
        for temp_list2 in iprange['Instances']:
            instanceid = temp_list2['InstanceId']
            nsg = temp_list2['NetworkInterfaces'][0]['Groups'][0]['GroupId']
            status = temp_list2["State"]['Name']
            name_tag = [x["Value"] for x in temp_list2['Tags'] if x['Key'] == 'Name']
            name = name_tag[0] if name_tag else ''
            dict_key = ['instanceid', 'Name', 'Status', 'NSG']
            dict_value = [instanceid, name, status, nsg]
            ins_dict[name] = dict(zip(dict_key, dict_value))
    return ins_dict

def instance_status(instance_dict):
    """
    Instance Status Notification
    """
    temp_list = []
    for j in instance_dict.keys():
        temp_list.append(j + ":" + instance_dict[j]['Status'])
    message = '\n'.join(temp_list)
    return message

def instance_action(action, body, instance_dict):
    """
    Operation Instance Start/Stop
    action: start / stop
    body : instanceid
    instance_dict : func dict_create
    """
    try:
        target_name = [x for x in instance_dict.keys() if x in body]
        target_id = instance_dict[target_name[0]]['instanceid']
    except IndexError:
        message = "No Target.You're probably misspelled."
        return message
    try:
        if 'start' in action:
            print("action start")
            response = EC2.start_instances(InstanceIds=[target_id])
            current_status = response['StartingInstances'][0]['CurrentState']['Name']
        elif 'stop' in action:
            print("action stop")
            response = EC2.stop_instances(InstanceIds=[target_id])
            current_status = response['StoppingInstances'][0]['CurrentState']['Name']
        else:
            message = "No Target.You're probably misspelled."
            return message
        message = "You " + action + " " + target_name[0] \
            + ". The current status is " + current_status  + "."
    except IndexError:
        message = "No Target.You're probably misspelled."
    return message

def whoname(body):
    """
    slack userid
    """
    body_list = [j for j in body.split('&') if 'user_id' in j]
    user_id = str(body_list)
    user_id = user_id.replace('user_id=', '')
    del_table = str.maketrans('', '', "[]'")
    user_id = user_id.translate(del_table)
    user_id = "<@" + user_id + ">"
    return user_id

def default_message():
    """
    NG/help message
    """
    message = "$server (status | help | [server name] start \
        | [server name] stop | ipshow \
        | ipadd/ipdell [server name] -FromPort xx -IpRanges xx.xx.xx.xx/xx -Description xxxx"
    return message

def lambda_handler(event,context):
    """
    main
    """
    instance_dict = dict_create()
    body = str(event['body'])
    if 'status' in body:
        message = instance_status(instance_dict)
    elif 'start' in body:
        action = 'start'
        message = instance_action(action, body, instance_dict)
    elif 'stop' in body:
        action = 'stop'
        message = instance_action(action, body, instance_dict)
    else:
        message = default_message()
    user_id = whoname(body)
    if "ipshow" in body:
        message_json = json.dumps(
            {
                'text': user_id,
                'attachments': message}
            )
    else:
        message_json = user_id + '\n' + message    
        message_json = json.dumps({'text': message_json})
    return {
        'statusCode': 200,
        'body': message_json
    }
