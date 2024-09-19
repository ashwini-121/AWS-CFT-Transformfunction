import boto3
import json
import os
from botocore.config import Config
cw_config = Config(
    retries={
        'max_attempts':20,
        'mode':'adaptive'
    }
)    
emr = boto3.client('emr')
s3 = boto3.resource('s3')

cloudwatch = boto3.client('cloudwatch',config=cw_config)
cloudwatchRes = boto3.resource('cloudwatch',config=cw_config)
metric = cloudwatchRes.Metric('namespace', 'name')
metrics_paginator = cloudwatch.get_paginator('list_metrics')
emr_paginator = emr.get_paginator('list_instances')
paginator = cloudwatch.get_paginator('describe_alarms')

def delete_alarms_in_batches(AlarmName):
    batch_size = 100  # Adjust batch size as needed
    for i in range(0, len(AlarmName), batch_size):
        batch = AlarmName[i:i + batch_size]
        cloudwatch.delete_alarms(AlarmNames=batch)

def lambda_handler(event, context):
    clusterId = event['detail']['clusterId']
    nameResponse = emr.describe_cluster(ClusterId=clusterId)
    clusterName = nameResponse['Cluster']['Name']
    clusterName=clusterName.split('-')[0]
    name = clusterName+'-'+clusterId
    state = ["TERMINATING","TERMINATED","TERMINATED_WITH_ERRORS"]
    tag = [{'Key':'value','Value':'test'}, {'Key':'Name','Value':'Rakesh'}]
    if (event['detail-type']=="EMR Cluster State Change" and event['detail']['state'] in state):
        print("Cluster is terminating/terminated")
        response = cloudwatch.describe_alarms(AlarmNamePrefix = name)
        AlarmName=[]
        if response['MetricAlarms']:
            for x in response['MetricAlarms']:
                AlarmName.append(x['AlarmName'])
        cloudwatch.delete_alarms(AlarmNames=AlarmName)
        cloudwatch.delete_dashboards(DashboardNames=[name])
    elif (event['detail-type']=="EMR Cluster State Change" and event['detail']['state']=="STARTING"):
        resp = emr.list_clusters(ClusterStates=['TERMINATED'])
        print("Cluster is starting")
        AlarmName = []
        Dashboards = []
        cleanupDashboard = []
        allDashboard = cloudwatch.list_dashboards()
        for termDash in allDashboard['DashboardEntries']:
            Dashboards.append(termDash['DashboardName'])
        for cleanup in resp['Clusters']:
            cleanupName = cleanup['Name'] + '_' + cleanup['Id']
            print(cleanupName)
            alarmCleanup = cloudwatch.describe_alarms(AlarmNamePrefix=cleanupName)
            if alarmCleanup['MetricAlarms']:
                for x in alarmCleanup['MetricAlarms']:
                    AlarmName.append(x['AlarmName'])
            if cleanupName in Dashboards:
                cleanupDashboard.append(cleanupName)
        cloudwatch.delete_alarms(AlarmNames=AlarmName)
        cloudwatch.delete_dashboards(DashboardNames=[cleanupDashboard])
    else:
        response = emr.list_instances(ClusterId=clusterId)
        nodeDownsize=[]
        ids=[]
        for y in emr_paginator.paginate(ClusterId=clusterId):
            for x in y['Instances']:
                if (x['Status']['State'] != "TERMINATED"):
                    ids.append(x['Ec2InstanceId'])
            print("Active instances:", ids)
        master_response = emr.list_instances(ClusterId=clusterId,InstanceGroupTypes=['MASTER'], InstanceStates=['RUNNING'])
        master_instance = master_response['Instances'][0]['Ec2InstanceId']
        print(master_instance)    
        if ids:
            for response in paginator.paginate(AlarmNamePrefix=name):    
                print("Total alarms associated with the cluster:", len(response['MetricAlarms']))
                if response['MetricAlarms']:
                    for x in response['MetricAlarms']:
                        if x['Dimensions']:
                            for dim in x['Dimensions']:
                                if dim['Name'] == 'InstanceId':
                                    if dim['Value'] not in ids:
                                        print("Terminated instance found. Adding to nodeDownsize:", dim['Value'])
                                        nodeDownsize.append(dim['Value'])
                            print("Instances to downsize:", nodeDownsize)

            for response in metrics_paginator.paginate(Dimensions=[{'Name': 'InstanceId', 'Value': master_instance}],MetricName='StatusCheckFailed',Namespace='AWS/EC2'):
                if response['Metrics']:
                    for d in response['Metrics']:
                        aName = name+'-'+ master_instance + '_Instance_StatusCheckFailed'
                        print(aName)
                        metric.put_alarm(
                            AlarmName=aName,
                            ComparisonOperator='GreaterThanOrEqualToThreshold',
                            EvaluationPeriods=2,
                            MetricName='StatusCheckFailed',
                            Namespace='AWS/EC2',
                            Period=300,
                            Statistic='Average',
                            TreatMissingData='breaching',
                            Threshold=1.0,
                            DatapointsToAlarm=1,
                            ActionsEnabled=True,
                            AlarmDescription='Alarm when instance status checks 1/2 fails',
                            Dimensions=d['Dimensions'],
                            AlarmActions=[os.environ['ALERTACTION']],
                            Tags=tag
                        )            
            for id in ids:
                for response in metrics_paginator.paginate(Dimensions=[{'Name': 'InstanceId', 'Value': id}],MetricName='CPUUtilization',Namespace='AWS/EC2'):
                    if response['Metrics']:
                        for d in response['Metrics']:
                            aName = name+'-'+ id + '_CPU_Utilization'
                            print(aName)
                            metric.put_alarm(
                                AlarmName=aName,
                                ComparisonOperator='GreaterThanThreshold',
                                EvaluationPeriods=1,
                                MetricName='CPUUtilization',
                                Namespace='AWS/EC2',
                                Period=10,
                                Statistic='Average',
                                Threshold=85.0,
                                # Threshold=int(os.environ['CPU_WARN_THRESHOLD']),
                                ActionsEnabled=True,
                                AlarmDescription='Alarm when server CPU exceeds 85%',
                                Dimensions=d['Dimensions'],
                                AlarmActions=[os.environ['ALERTACTION']],
                                Tags=tag
                            )
                    if response['Metrics']:
                        for d in response['Metrics']:
                            aName = name+'-'+ id + '_AlertCPU_Utilization'
                            print(aName)
                            metric.put_alarm(
                                AlarmName=aName,
                                ComparisonOperator='GreaterThanThreshold',
                                EvaluationPeriods=1,
                                MetricName='CPUUtilization',
                                Namespace='AWS/EC2',
                                Period=900,
                                Statistic='Average',
                                Threshold=95.0,
                                #Threshold=int(os.environ['CPU_CRIT_THRESHOLD']),
                                ActionsEnabled=True,
                                AlarmDescription='Alarm when server CPU exceeds 95%',
                                Dimensions=d['Dimensions'],
                                AlarmActions=[os.environ['ALERTACTION']],
                                Tags=tag
                            )        
      
            downsized = set(nodeDownsize)
            print("Downsized instances:",downsized)
            if downsized:
                for i in downsized:
                    response = cloudwatch.describe_alarms(AlarmNamePrefix=name+'-'+i)
                    AlarmName = []
                    if response['MetricAlarms']:
                        for x in response['MetricAlarms']:
                            AlarmName.append(x['AlarmName'])
                        print("Total alarms for terminated instance", i, ":", len(AlarmName))
                        delete_alarms_in_batches(AlarmName)
                        print("Terminated Alarms are: ", AlarmName)
                        #cloudwatch.delete_alarms(AlarmNames=AlarmName)

            obj = s3.Object(os.environ['BUCKET'], 'dashboard.json')
            data = json.load(obj.get()['Body'])
            json_object = data
            for i in range(0, len(json_object['widgets'])):
                if 'InstanceId' in json_object['widgets'][i]['properties']['metrics'][0]:
                    index = json_object['widgets'][i]['properties']['metrics'][0].index('InstanceId') + 1
                    json_object['widgets'][i]['properties']['metrics'][0][index] = ids[0]
                    json_object['widgets'][i]['properties']['metrics'] = json_object['widgets'][i]['properties']['metrics'][
                                                                         :1]
                    for j in range(1, len(ids)):
                        temp = json_object['widgets'][i]['properties']['metrics'][0][:]
                        temp[index] = ids[j]
                        json_object['widgets'][i]['properties']['metrics'].append(temp)
                elif 'JobFlowId' in json_object['widgets'][i]['properties']['metrics'][0]:
                    index = json_object['widgets'][i]['properties']['metrics'][0].index('JobFlowId') + 1
                    json_object['widgets'][i]['properties']['metrics'][0][index] = clusterId
            json_object = json.dumps(json_object, indent=4)
            cloudwatch.put_dashboard(
                DashboardName=name,
                DashboardBody=json_object
            )