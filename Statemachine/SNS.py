import json
import boto3
import os

def lambda_handler(event, context):
     region = 'us-east-1'
     clusterName = 'Transient'
     clusterid = ''
     # Step_Name = ''
     MyStepName = ''
     session = boto3.session.Session(region_name=region)
     emr = session.client('emr')

     page_iterator = emr.get_paginator('list_clusters').paginate(
         ClusterStates=['STARTING', 'BOOTSTRAPPING', 'RUNNING', 'WAITING']
     )
     
     for page in page_iterator:
         for item in page['Clusters']:
              if item["Name"].lower() == clusterName.lower():
                   clusterid = item['Id']
     print(clusterid)
     
     if(clusterid !=''):
         page_iterator2 = emr.get_paginator('list_steps').paginate(
             ClusterId=clusterid,
             StepStates=['FAILED','PENDING']
         )
         print(page_iterator2)
         for page in page_iterator2:
             for item in page['Steps']:
                  #print(item)
                  #print(item['Config']['Args'][2])
                  if "MyStepName" :
                      print("MyStepName is running")
                      MyStepName = 'MyStepName'
                #   if "MyStepName1" in item['Config']['Args'][2]:
                #       print("MyStepName1 is running")
                #       MyStepName1 = 'MyStepName1'
                      
                  #if item["Name"] == 'Execute_Analytic':
                  #     Step_Name = item['Name']
     #print(Step_Name)
     
#      message = 'ClusterId', 'MyStepName'
#      print(message)
#      return message
# result = lambda_handler({}, {})
# print(result)
     
     
     
     return  {'ClusterId': clusterid , 'MyStepName': MyStepName,  }