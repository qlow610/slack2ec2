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
    def __init__(self):
        dict_i = {}

    def instancedict(self):
        list1 = ec2.describe_instances(
            Filters = [{'Name':'tag:Slack','Values':['']}]
        )
        #list2 = [ x['Instances'] for x in list1['Reservations'] ]
        instanceid = [x['Instances'][0]['InstanceId'] for x in list1['Reservations']]
        NSG = [x['Instances'][0]['NetworkInterfaces'][0]['Groups'][0]['GroupId'] for x in list1['Reservations'] ]
        Status = [x['Instances'][0]['State']['Name'] for x in list1['Reservations']]
        Name = [y['Value'] for x in instanceid for y in ec3.Instance(id=x).tags if y['Key'] == 'Name']
        Dict_key = ['instanceid','Name','Status','NSG']
        #Dict_item = [ for x in instanceid for y in NSG for z in Status for aa in Name]
            #dict_i[instanceid] = {
            #    'instanceid' : instanceid[x],
            #    'Name' : Name[x],
            #    'Status' : Status[x],
            #    'NSG' : NSG[x]
            #}
        #print(dict_i)
        #return(dict_i)

test1 = dictcreate()
test1.instancedict()