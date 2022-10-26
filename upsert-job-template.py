# Given a job template name, a mediaconvert endpoint, and a mediaconvert role, create or update a job template

import boto3
import sys
import time

def main():
    if len(sys.argv) <= 4 or len(sys.argv) > 5:
        print("Usage: python upsert-job-template.py <job template name> <mediaconvert role> <path to job template json> [mediaconvert endpoint | OPTIONAL]")
        return
    

    job_template_name = sys.argv[1]
    mediaconvert_role = sys.argv[2]
    job_template_json_path = sys.argv[3]

    # Assume role
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=mediaconvert_role,
        RoleSessionName="python-upsert-job-template"
    )

    # Create a MediaConvert client with the assumed role credentials
    credentials = assumed_role_object['Credentials']
    mediaconvert_client = boto3.client(
        'mediaconvert',
        endpoint_url=mediaconvert_endpoint,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )


    if len(sys.argv) == 5:
        mediaconvert_endpoint = sys.argv[4]
    else:
        mediaconvert_endpoint = describe_endpoint(mediaconvert_client)


    # Try to get the job template to see if it already exists
    try:
        response = mediaconvert_client.get_job_template(Name=job_template_name)
        print("Job template already exists, updating it")
        job_template = response['JobTemplate']
        update_job_template(mediaconvert_client, job_template_name, job_template_json_path)
    except mediaconvert_client.exceptions.ResourceNotFoundException:
        print("Job template does not exist, creating it")
        create_job_template(mediaconvert_client, job_template_name, job_template_json_path)


def describe_endpoint(mediaconvert_client):
    # Try to describe the endpoint, but handle rate limiting
    try:
        response = mediaconvert_client.describe_endpoints()
        # Return the first endpoint
        return response['Endpoints'][0]
    except mediaconvert_client.exceptions.TooManyRequestsException as e:
        print("Too many requests on DescribeEndpoint, sleeping for 1 minute")
        time.sleep(60)
        return describe_endpoint(mediaconvert_client)

def create_job_template(mediaconvert_client, job_template_name, job_template_json_path):
    print(f"Creating template {job_template_name}")
    # Create a job template
    response = mediaconvert_client.create_job_template(
        Name=job_template_name,
        Settings=open(job_template_json_path).read()
    )
    #Query out the jobtemplate created at and last updated at
    job_template = response['JobTemplate']
    print(f"Created job template {job_template_name} at {job_template['CreatedAt']} and last updated at {job_template['LastUpdated']}")

def update_job_template(mediaconvert_client, job_template_name, job_template_json_path):
    print(f"Updating template {job_template_name}")
    # Update a job template
    response = mediaconvert_client.update_job_template(
        Name=job_template_name,
        Settings=open(job_template_json_path).read()
    )
    #Query out the jobtemplate created at and last updated at
    job_template = response['JobTemplate']
    print(f"Updated job template {job_template_name} at {job_template['CreatedAt']} and last updated at {job_template['LastUpdated']}")
        