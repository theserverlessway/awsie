import sys

import boto3
import pytest

from awsie import cli


@pytest.fixture()
def region():
    return 'us-west-1'


@pytest.fixture()
def profile():
    return 'testprofile'


@pytest.fixture()
def stack():
    return 'teststack'


def test_profile_argument_parsing(stack, region):
    arguments = cli.parse_arguments([stack, '--region', region])
    assert arguments.region == region


def test_region_argument_parsing(stack, profile):
    arguments = cli.parse_arguments([stack, '--profile', profile])
    assert arguments.profile == profile


def test_stack_argument_parsing(stack):
    arguments = cli.parse_arguments(['--profile', 'something', stack, 'something', 'else'])
    assert arguments.stack == stack


def test_fails_without_stack(mocker):
    with pytest.raises(SystemExit):
        cli.parse_arguments([])


def test_session_creation(mocker, region, profile):
    mocker.patch.object(cli, 'Session')
    session = cli.create_session(region, profile)
    cli.Session.assert_called_with(region_name=region, profile_name=profile)
    assert session == cli.Session.return_value


def test_loads_resources(mocker, stack):
    session = mocker.Mock(spec=boto3.Session)
    client = session.client.return_value

    resources_summaries = []
    for i in range(2):
        resources = {'StackResourceSummaries': [{
            'LogicalResourceId': 'LogicalResourceId' + str(i),
            'PhysicalResourceId': 'PhysicalResourceId' + str(i)

        }]}
        resources_summaries.append(resources)

    client.get_paginator().paginate.return_value = resources_summaries

    ids = cli.get_resource_ids(session=session, stack=stack)
    assert len(ids) == 2
    assert ids['LogicalResourceId0'] == 'PhysicalResourceId0'
    assert ids['LogicalResourceId1'] == 'PhysicalResourceId1'
    session.client.assert_called_with('cloudformation')
    client.get_paginator.assert_called_with('list_stack_resources')
    client.get_paginator.return_value.paginate.assert_called_with(StackName=stack)


def test_main_replaces_and_calls_aws(mocker, stack):
    arguments = ['awsie', stack, 'testcf:DeploymentBucket:', 'test2', 'test3']
    mocker.patch.object(sys, 'argv', arguments)
    sysexit = mocker.patch.object(sys, 'exit')
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'DeploymentBucket': '1'}

    cli.main()

    subprocess.call.assert_called_with(['aws', 'test1', 'test2', 'test3'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_main_fails_for_missing_replacement(mocker, stack):
    arguments = ['awsie', stack, 'testcf:DeploymentBucket:']
    mocker.patch.object(sys, 'argv', arguments)
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')

    get_resource_ids.return_value = {}

    with pytest.raises(SystemExit):
        cli.main()


def test_main_fails_for_missing_awscli(mocker, stack):
    arguments = ['awsie', stack]
    mocker.patch.object(sys, 'argv', arguments)
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')
    subprocess.call.side_effect = OSError()

    with pytest.raises(SystemExit):
        cli.main()
