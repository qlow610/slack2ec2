"""This is Slack to Ec2/NSG operating """
#############################
#language pytho
#ec2 start/stop/status/SG Change
#############################

from __future__ import print_function

#import
from pprint import pprint
import json
import boto3

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
        temp_list.append(j + " : " + instance_dict[j]['Status'])
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

def nsg_list(body, instance_dict):
    """
    Network Security Group Listing
    """
    temp_message = []
    try:
        target_name = [x for x in instance_dict.keys() if x in body]
        targetid = instance_dict[target_name[0]]['NSG']
        describe_sg = EC2.describe_security_groups(GroupIds=[targetid])
    except IndexError:
        message = "No Target.You're probably misspelled."
        return message
    ippermission = describe_sg['SecurityGroups'][0]['IpPermissions']
    for iptable in ippermission:
        iprange = iptable['IpRanges']
        fromport = str(iptable['FromPort'])
        toport = str(iptable['ToPort'])
        for k in iprange:
            cidrip = k['CidrIp']
            try:
                description = k['Description']
            except KeyError:
                description = '-'
            temp_fields = [{
                "title":cidrip,
                "value":\
                "FromPort: " + fromport +'\n' + \
                    "ToPort: " + toport +'\n'  + \
                    "Description:" + description,
                "short": "true"
                }]
            temp_message.extend(temp_fields)
    message = [{
        "fallback":"SecrutiGroup List",
        "pretext": target_name,
        "color":"#A9E2F3",
        "fields":temp_message
        }]
    return message

def nsg_add(body, instance_dict, fport, iprange, description):
    """
    Network Security Group ADD IP
    """
    try:
        target_name = [x for x in instance_dict.keys() if x in body]
        target_id = instance_dict[target_name[0]]['NSG']
    except IndexError:
        message = "No Target.You're probably misspelled."
        return message
    try:
        response = EC2.authorize_security_group_ingress(
            DryRun=False,
            GroupId=target_id,
            IpPermissions=[
                {
                    'FromPort': fport,
                    'IpProtocol': 'tcp',
                    'IpRanges': [
                        {
                            'CidrIp': iprange,
                            'Description': description
                            },
                            ],
                            'ToPort': fport,
                            }])
        message = "NSG add Success"
    except:
        message = "NSG add Failed"
    return message

def nsg_dell(body,instance_dict,fport,iprange):
    try:
        target_name = [x for x in instance_dict.keys() if x in body]
        target_id = instance_dict[target_name[0]]['NSG']
    except IndexError:
        message = "No Target.You're probably misspelled."
        return message
    try:
        response = EC2.revoke_security_group_ingress(
            DryRun=False,
            GroupId=target_id,
            IpPermissions=[
                {
                    'FromPort': fport,
                    'IpProtocol': 'tcp',
                    'IpRanges': [
                        {
                            'CidrIp': iprange
                            },
                            ],
                            'ToPort': fport
                            }])
        message = "NSG dell Success"
    except:
        message = "NSG dell Failed"
    return message

def bodysplit(action, body):
    """
    slack message split when Change Network SecurityGroup
    """
    body_list = [j for j in body.split('&') if 'text' in j]
    body_list = str(body_list)
    del_table = str.maketrans('', '', "[]'")
    body_list = body_list.translate(del_table)
    body_list = [j for j in str(body_list).split('+')]
    fromportnum = (body_list.index("-FromPort") + 1)
    fport = int(body_list[fromportnum])
    iprangenum = (body_list.index("-IpRanges") + 1)
    iprange = (body_list[iprangenum]).replace('%2F', '/')
    if 'ipadd' in  action:
        descriptionnum = (body_list.index("-Description") + 1)
        description = body_list[descriptionnum]
    else:
        description = ""
    return fport, iprange, description

def lambda_handler(event, context):
    """
    main
    """
    instance_dict = dict_create()
    body = str(event['body'])
    user_id = whoname(body)
    if 'status' in body:
        message = instance_status(instance_dict)
    elif 'start' in body:
        action = 'start'
        message = instance_action(action, body, instance_dict)
    elif 'stop' in body:
        action = 'stop'
        message = instance_action(action, body, instance_dict)
    elif 'ipadd' in body:
        action = 'ipadd'
        fport, iprange, description = bodysplit(action, body)
        message = nsg_add(body, instance_dict, fport, iprange, description)
    elif 'ipdell' in body:
        action = 'ipdell'
        fport, iprange, description = bodysplit(action, body)
        message = nsg_dell(body, instance_dict, fport, iprange)
    else:
        message = "$server (status | help | [server name] start \
        | [server name] stop | ipshow \
        | ipadd/ipdell [server name] -FromPort xx -IpRanges xx.xx.xx.xx/xx -Description xxxx"
    if "ipshow" in body:
        message = nsg_list(body, instance_dict)
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
