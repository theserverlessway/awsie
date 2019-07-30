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

    if arguments.no_stack:
        stack = ''
        remaining = [arguments.stack] + remaining
    else:
        stack = arguments.stack

    try:
        if stack and os.path.isfile(stack):
            with open(stack, 'r') as file:
                config = yaml.safe_load(file)
                stack = config.get('stack')

            if not stack:
                logger.info('Config file does not contain stack option.')
                sys.exit(1)

        session = create_session(region=arguments.region, profile=arguments.profile)
        ids = get_resource_ids(session, stack)
        if arguments.debug or arguments.verbose:
            logger.info('Replacements:')
            for key, value in ids.items():
                logger.info("  {}: {}".format(key, value))
            logger.info('')
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
    new_args = [re.sub('cf:([a-zA-Z0-9:]+):', replacement, argument) for argument in command]

    if arguments.debug or arguments.verbose:
        logger.info('Command:')
        logger.info('  ' + ' '.join(new_args))
        logger.info('')

    try:
        if arguments.debug:
            result = 0
        else:
            result = subprocess.call(new_args)
    except OSError:
        logger.info('Please make sure "{}" is installed and available in the PATH'.format(command[0]))
        sys.exit(1)

    sys.exit(result)


def get_resource_ids(session, stack):
    try:
        ids = {}
        client = session.client('cloudformation')
        if stack:
            paginator = client.get_paginator('list_stack_resources').paginate(StackName=stack)
            for page in paginator:
                for resource in page.get('StackResourceSummaries', []):
                    ids[resource['LogicalResourceId']] = resource['PhysicalResourceId']

            describe_stack = client.describe_stacks(StackName=stack)
            stack_outputs = describe_stack['Stacks'][0].get('Outputs', [])
            for output in stack_outputs:
                ids[output['OutputKey']] = output['OutputValue']

        paginator = client.get_paginator('list_exports').paginate()
        for page in paginator:
            for export in page.get('Exports', []):
                ids[export['Name']] = export['Value']
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
                    'stack or config file name, all other arguments are forwarded to the AWS CLI. --region and '
                    '--profile are used '
                    'to determine which stack to load the resources from and are passed on as well.\\nExample:\\n '
                    'awsie example-stack s3 ls s3://cf:DeploymentBucket:')

    parser.add_argument('--version', action='version', version='{}'.format(__version__))
    parser.add_argument('stack', help='Stack to load resources from')
    parser.add_argument('--region', help='The AWS Region to use')
    parser.add_argument('--profile', help='The AWS Profile to use')
    parser.add_argument('--command', action="store_true", help="If you run a non AWS CLI command")
    parser.add_argument('--no-stack', action="store_true", help="If you only use CFN Exports and no Stack data")
    parser.add_argument('--verbose', action="store_true", help="Print debug output before running the command")
    parser.add_argument('--debug', action="store_true", help="Print debug output and don't run the command")
    args = parser.parse_known_args(arguments)
    return args
