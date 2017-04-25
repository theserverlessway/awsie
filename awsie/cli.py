import argparse
import re
import subprocess
import sys

import botocore
from boto3.session import Session


def main():
    parsed_arguments = parse_arguments(sys.argv[1:])
    arguments = parsed_arguments[0]
    remaining = parsed_arguments[1]

    stack = arguments.stack

    try:
        session = create_session(region=arguments.region, profile=arguments.profile)
        ids = get_resource_ids(session, stack)
    except Exception as e:
        print(e)
        sys.exit(1)

    def replacement(matchobject):
        match_name = matchobject.group(1)
        if not ids.get(match_name):
            print('Resource with logical ID "' + match_name + '" does not exist')
            sys.exit(1)
        return ids[match_name]

    command = ['aws'] + remaining
    if arguments.command:
        command = arguments.command.split()
    else:
        if arguments.region:
            command.extend(['--region', arguments.region])
        if arguments.profile:
            command.extend(['--profile', arguments.profile])
    new_args = [re.sub('cf:([a-zA-Z0-9]+):', replacement, argument) for argument in command]

    try:
        result = subprocess.call(new_args)
    except OSError:
        print('Please make sure "{}" is installed and available in the PATH'.format(command[0]))
        sys.exit(1)

    sys.exit(result)


def get_resource_ids(session, stack):
    try:
        client = session.client('cloudformation')
        paginator = client.get_paginator('list_stack_resources').paginate(StackName=stack)
        ids = {}
        for page in paginator:
            for resource in page['StackResourceSummaries']:
                ids[resource['LogicalResourceId']] = resource['PhysicalResourceId']

        describe_stack = client.describe_stacks(StackName=stack)
        stack_outputs = describe_stack['Stacks'][0].get('Outputs', [])
        for output in stack_outputs:
            ids[output['OutputKey']] = output['OutputValue']
    except botocore.exceptions.ClientError as e:
        print(e)
        sys.exit(1)
    return ids


def create_session(region, profile):
    params = {}
    if region:
        params['region_name'] = region
    if profile:
        params['profile_name'] = profile
    session = Session(**params)
    return session


def parse_arguments(arguments):
    parser = argparse.ArgumentParser(
        description='Call AWS with substituted CloudFormation values. The first positional argument is used as the '
                    'stack name, all other arguments are forwarded to the AWS CLI. --region and --profile are used '
                    'to determine which stack to load the resources from and are passed on as well.\\nExample:\\n '
                    'awsie example-stack s3 ls s3://cf:DeploymentBucket:')

    parser.add_argument('stack', help='Stack to load resources from')
    parser.add_argument('--region')
    parser.add_argument('--profile')
    parser.add_argument('--command')
    args = parser.parse_known_args(arguments)
    return args
