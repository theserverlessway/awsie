import argparse
import logging
import os
import re
import subprocess
import sys

import botocore
import botocore.session
import yaml
from boto3.session import Session
from botocore import credentials

from . import __version__

cli_cache = os.path.join(os.path.expanduser('~'), '.aws/cli/cache')

logger = logging.getLogger(__name__)


def main():
    parsed_arguments = parse_arguments(sys.argv[1:])
    arguments = parsed_arguments[0]
    remaining = parsed_arguments[1]

    stack = arguments.stack
    try:
        if os.path.isfile(stack):
            with open(stack, 'r') as file:
                config = yaml.safe_load(file)
                stack = config.get('stack')

            if not stack:
                logger.info('Config file does not contain stack option.')
                sys.exit(1)

        session = create_session(region=arguments.region, profile=arguments.profile)
        ids = get_resource_ids(session, stack)
    except Exception as e:
        logger.info(e)
        sys.exit(1)

    def replacement(matchobject):
        match_name = matchobject.group(1)
        if not ids.get(match_name):
            logger.info('Resource with logical ID "' + match_name + '" does not exist')
            sys.exit(1)
        return ids[match_name]

    if arguments.command:
        command = remaining
    else:
        command = ['aws'] + remaining
        if arguments.region:
            command.extend(['--region', arguments.region])
        if arguments.profile:
            command.extend(['--profile', arguments.profile])
    new_args = [re.sub('cf:([a-zA-Z0-9]+):', replacement, argument) for argument in command]

    try:
        result = subprocess.call(new_args)
    except OSError:
        logger.info('Please make sure "{}" is installed and available in the PATH'.format(command[0]))
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
        logger.info(e)
        sys.exit(1)
    return ids


def create_session(region, profile):
    cached_session = botocore.session.Session(profile=profile)
    cached_session.get_component('credential_provider').get_provider('assume-role').cache = credentials.JSONFileCache(
        cli_cache)
    return Session(botocore_session=cached_session, region_name=region)


def parse_arguments(arguments):
    parser = argparse.ArgumentParser(
        description='Call AWS with substituted CloudFormation values. The first positional argument is used as the '
                    'stack name, all other arguments are forwarded to the AWS CLI. --region and --profile are used '
                    'to determine which stack to load the resources from and are passed on as well.\\nExample:\\n '
                    'awsie example-stack s3 ls s3://cf:DeploymentBucket:')

    parser.add_argument('--version', action='version', version='{}'.format(__version__))
    parser.add_argument('stack', help='Stack to load resources from')
    parser.add_argument('--region')
    parser.add_argument('--profile')
    parser.add_argument('--command', action="store_true")
    args = parser.parse_known_args(arguments)
    return args
