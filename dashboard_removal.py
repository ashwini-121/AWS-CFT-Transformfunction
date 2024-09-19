import boto3
import json
import os
emr = boto3.client('emr')
cloudwatch = boto3.client('cloudwatch')
s3 = boto3.resource('s3')
cloudwatchRes = boto3.resource('cloudwatch')
metric = cloudwatchRes.Metric('namespace', 'name')
paginator = cloudwatch.get_paginator('list_metrics')
emr = boto3.client('emr')
cloudwatch = boto3.client('cloudwatch')
s3 = boto3.resource('s3')                           
def handler(event, context):
  clusterId=event['detail']['clusterId']
  print(clusterId)
  nameResponse = emr.describe_cluster(ClusterId=clusterId)
  clusterName = nameResponse['Cluster']['Name']
  clusterName=clusterName.split('-')[0]
  name = clusterName+'-'+clusterId
  paginator = cloudwatch.get_paginator('describe_alarms')
  for response in paginator.paginate(AlarmNamePrefix=name):
    # Do something with the alarm
    print(response['MetricAlarms'])
    AlarmName=[]
    if response['MetricAlarms']:
        for x in response['MetricAlarms']:
            AlarmName.append(x['AlarmName'])
            if( AlarmName):
              print('deleting Alarms')
              cloudwatch.delete_alarms(AlarmNames=AlarmName)
              cloudwatch.delete_dashboards(DashboardNames=[name])
  #cloudwatch.delete_alarms(AlarmNames=AlarmName)
  #cloudwatch.delete_dashboards(DashboardNames=[name])      
  print(AlarmName)
  print(name)
  return(AlarmName) 