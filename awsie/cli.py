import argparse
import re
import subprocess
import sys

import botocore
from boto3.session import Session


def main():
    arguments = parse_arguments(sys.argv[1:])

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

    new_args = ['aws'] + [re.sub('cf:([a-zA-Z0-9]+):', replacement, argument) for argument in sys.argv[1:]]
    new_args.remove(stack)

    try:
        result = subprocess.call(new_args)
    except OSError:
        print('Please make sure to install the AWSCLI with "pip install awscli"')
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


def parse_arguments(args):
    parser = argparse.ArgumentParser(
        description='Call AWS with substituted CloudFormation values. The first positional argument is used as the '
                    'stack name, all other arguments are forwarded to the AWS CLI. --region and --profile are used '
                    'to determine which stack to load the resources from and are passed on as well.\\nExample:\\n '
                    'awsie example-stack s3 ls s3://cf:DeploymentBucket:')

    parser.add_argument('stack', help='Stack to load resources from')
    parser.add_argument('--region')
    parser.add_argument('--profile')
    args = parser.parse_known_args(args)
    return args[0]
