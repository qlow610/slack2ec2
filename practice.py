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

#
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ec2 = boto3.client('ec2')
ec3 = boto3.resource('ec2')

class dictcreate:
    def __init__(self,Action):
        global dict_i
        dict_i = {}
        list1 = ec2.describe_instances(
            Filters = [{'Name':'tag:Slack','Values':['']}]
        )
        instanceid = [x['Instances'][0]['InstanceId'] for x in list1['Reservations']]
        self.instanceid = instanceid
        self.list1 = list1
        self.Action = Action

    def status(self,Action):
        Name = [y['Value'] for x in self.instanceid for y in ec3.Instance(id=x).tags if y['Key'] == 'Name']
        Status = [x['Instances'][0]['State']['Name'] for x in self.instanceid['Reservations']]
        dict_i = [(x,Status[Name.index(x)]) for x in Name]
        return(dict_i)

    def instancedict(self):
        NSG = [x['Instances'][0]['NetworkInterfaces'][0]['Groups'][0]['GroupId'] for x in self.list1['Reservations'] ]
        Status = [x['Instances'][0]['State']['Name'] for x in self.list1['Reservations']]
        Name = [y['Value'] for x in self.instanceid for y in ec3.Instance(id=x).tags if y['Key'] == 'Name']
        Dict_key = ['instanceid','NSG','Status','Name']
        Dict_item = [ dict((zip(Dict_key,(x,NSG[self.instanceid.index(x)],Status[self.instanceid.index(x)],Name[self.instanceid.index(x)])))) for x in self.instanceid ]       
        for x in Name:
            dict_i[x] = Dict_item[Name.index(x)]
        return(dict_i)


class actioncheck:
    def __init__(self,body):
        self.body = body
        global Action
    
    def acitonchekc(self):
        if 'status' in self.body:
            Action = 'status'
            dictcreate.status(self,Action)
            print(dict_i)


def lambda_handler(event, context):
    body = str(event['body'])
    acc = actioncheck(body)
    acc.acitonchekc()
    #logger.info("Event: " + str(body))
    #logger.info("Event: " + str(instance_dict))





event = {
    'body':'$server Instance status'
}  
context = "test"
lambda_handler(event,context)