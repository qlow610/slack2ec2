# coding:utf-8

import boto3
import json 
import pprint
import re

ec2 = boto3.client('ec2')
dev_list = []
Name_Tag = []
Status_list = []

# def
#サーバーリスト取得
def get_list():
  instance_list = ec2.describe_instances(
    Filters=[{'Name': 'tag:env', 'Values': ['dev']}]
    #Filters=[{'Name': 'tag:slack', 'Values': ['']}]
  )
  for Reservations in instance_list['Reservations']:
    for dev_instances in Reservations['Instances']:
      dev_list.append(dev_instances["InstanceId"])

#NameTag取得
def ec2_tag(dev_list):
  get_list()
  for instance_id in dev_list:
    instance_Info = ec2.describe_instances(
    Filters =[{'Name':'instance-id','Values':[instance_id]}]
    )
    for Reservations in instance_Info['Reservations']:
      for dev_instances in Reservations['Instances']:
        #pprint.pprint(dev_instances)
        #Name_Tag.append(dev_instances["KeyName"])
        pprint.pprint()) 

ec2_tag(dev_list)

#ステータス取得
def ec2_status(dev_list):
  for instance_id in dev_list:
    instance_Info = ec2.describe_instances(
    Filters =[{'Name':'instance-id','Values':[instance_id]}]
    )
    for Reservations in instance_Info['Reservations']:
      for dev_instances in Reservations['Instances']:
        Status_list.append(dev_instances["State"]['Name'])

#取得データのリスト化
def dict_create():
  get_list()
  ec2_tag(dev_list)
  ec2_status(dev_list)
  x = list(range(len(dev_list)))
  Rdict = dict()
  for l in x:
    li1 = [
      ("instance",dev_list[l]),
      ("Tag",Name_Tag[l]),
      ("Status",Status_list[l])
    ]
    dict1 = dict(li1)
    instanceIDs = dev_list[l]
    Rdict[instanceIDs] = dict1


#メイン処理 
def lambda_handler(event, context):
  dict_create()
  #body = str(event['body'])
  if 'status' in event:
    x = list(range(len(dev_list)))
    for j in x:
      message = Name_Tag[j] + ':' + Status_list[j]    
      print(message)
#  elif 'start' in event:
    


event = 'status'
context = 'test'
#lambda_handler(event,context)
