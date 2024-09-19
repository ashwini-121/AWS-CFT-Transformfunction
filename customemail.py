import json
import boto3

def handler(event, context):
    # Extract SNS message from the event
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    
    # Extract relevant information for EMR cluster alarms
    cluster_id = sns_message.get('Trigger', {}).get('Dimensions', [{}])[0].get('value', 'Unknown')
    alarm_name = sns_message.get('AlarmName', 'Custom Notification')
    alarm_description = sns_message.get('AlarmDescription', 'No description provided.')
    new_state_value = sns_message.get('NewStateValue', 'Unknown')
    region = sns_message.get('Region', 'Unknown')
    state_change_time = sns_message.get('StateChangeTime', 'Unknown')
    type_of_alert = 'Warning' if sns_message.get('Trigger', {}).get('Threshold', 0) <= int(os.environ['THRESHOLD_VALUE']) else 'Alert'

    # Construct the email body
    email_body = f"EMR Cluster ID: {cluster_id}\nAlarm Name: {alarm_name}\nAlarm Description: {alarm_description}\nNew State: {new_state_value}\nRegion: {region}\nState Change Time: {state_change_time}\nType of Alert: {type_of_alert}"

    # Send email using Amazon SES (Simple Email Service)
    ses_client = boto3.client('ses', region_name='YOUR_REGION')  # Specify your region
    sender_email = 'SENDER_EMAIL_ADDRESS'
    recipient_email = 'RECIPIENT_EMAIL_ADDRESS'

    # Construct the email parameters
    email_params = {
        'Source': sender_email,
        'Destination': {'ToAddresses': [recipient_email]},
        'Message': {
            'Subject': {'Data': alarm_name},
            'Body': {'Text': {'Data': email_body}}
        }
    }

    try:
        # Send the email
        response = ses_client.send_email(**email_params)
        print("Email sent successfully.")
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully')
        }
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise
