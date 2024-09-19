import boto3

def lambda_handler(event, context):
    try:
        # Source and target bucket names
        source_bucket = 'codebuildpipeline-cftbucket'
        target_bucket = 'filetransfertestinglambda'

        # Create S3 client
        s3 = boto3.client('s3')

        # List objects in the source bucket
        response = s3.list_objects_v2(Bucket=source_bucket)

        # Check if objects were found in the source bucket
        if 'Contents' in response:
            # Iterate through each object in the source bucket
            for obj in response['Contents']:
                # Extract key (file name) from the object
                source_key = obj['Key']

                # Copy the object from the source bucket to the target bucket
                s3.copy_object(
                    Bucket=target_bucket,
                    Key=source_key,
                    CopySource={'Bucket': source_bucket, 'Key': source_key}
                )

            # If the file transfer was successful, report success to CodePipeline if available
            if 'CodePipeline.job' in event:
                codepipeline = boto3.client('codepipeline')
                response = codepipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
                return response
            else:
                return {
                    'statusCode': 200,
                    'body': 'Files transferred successfully!'
                }
        else:
            # If no objects found in source bucket, report failure to CodePipeline if available
            if 'CodePipeline.job' in event:
                codepipeline = boto3.client('codepipeline')
                response = codepipeline.put_job_failure_result(jobId=event['CodePipeline.job']['id'], failureDetails={'message': 'No objects found in source bucket', 'type': 'JobFailed'})
                return response
            else:
                return {
                    'statusCode': 500,
                    'body': 'No objects found in source bucket!'
                }
    except Exception as e:
        # If an error occurs during file transfer or reporting, report failure to CodePipeline if available
        if 'CodePipeline.job' in event:
            codepipeline = boto3.client('codepipeline')
            response = codepipeline.put_job_failure_result(jobId=event['CodePipeline.job']['id'], failureDetails={'message': str(e), 'type': 'JobFailed'})
            return response
        else:
            return {
                'statusCode': 500,
                'body': f'Error: {str(e)}'
            }