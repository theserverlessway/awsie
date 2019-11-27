import sys

import boto3
import pytest
from awsie import cli
from path import Path


@pytest.fixture()
def region():
    return 'us-west-1'


@pytest.fixture()
def profile():
    return 'testprofile'


@pytest.fixture()
def stack():
    return 'teststack'


@pytest.fixture()
def sysexit(mocker):
    return mocker.patch.object(sys, 'exit')


@pytest.fixture()
def arguments(mocker):
    arguments = []
    mocker.patch.object(sys, 'argv', arguments)
    return arguments


describe_stack = {
    'Stacks': [
        {'Outputs': [
            {'OutputKey': 'Output_Key_1',
             'OutputValue': 'Output_Value_1'},
            {'OutputKey': 'Output_Key_2',
             'OutputValue': 'Output_Value_2'}
        ],
        }
    ]
}


@pytest.fixture
def botocore_session(mocker):
    return mocker.patch('botocore.session.Session')


@pytest.fixture
def session(mocker, botocore_session):
    return mocker.patch('awsie.cli.Session')


@pytest.fixture
def client(session, mocker):
    client_mock = mocker.Mock()
    session.return_value.client.return_value = client_mock
    return client_mock


def test_profile_argument_parsing(stack, region):
    arguments = cli.parse_arguments([stack, '--region', region])[0]
    assert arguments.region == region


def test_region_argument_parsing(stack, profile):
    arguments = cli.parse_arguments([stack, '--profile', profile])[0]
    assert arguments.profile == profile


def test_stack_argument_parsing(stack):
    arguments = cli.parse_arguments(['--profile', 'something', stack, 'something', 'else'])[0]
    assert arguments.stack == stack


def test_fails_without_stack():
    with pytest.raises(SystemExit):
        cli.parse_arguments([])


def test_session_creation(region, profile, session, botocore_session):
    new_session = cli.create_session(region, profile)
    botocore_session.assert_called_with(profile=profile)
    session.assert_called_with(botocore_session=botocore_session(), region_name=region)
    assert new_session == session()


def test_loads_resources_and_outputs_and_exports(mocker, stack):
    session = mocker.Mock(spec=boto3.Session)
    client = session.client.return_value

    resources_mocks = mocker.Mock()
    resources_mocks.paginate.return_value = [{'StackResourceSummaries': [{
        'LogicalResourceId': 'LogicalResourceId' + str(i),
        'PhysicalResourceId': 'PhysicalResourceId' + str(i)
    }]} for i in range(2)]

    exports_mocks = mocker.Mock()
    exports_mocks.paginate.return_value = [{'Exports': [{
        'Name': 'ExportName' + str(i),
        'Value': 'ExportValue' + str(i)
    }]} for i in range(2)]

    client.get_paginator.side_effect = [resources_mocks, exports_mocks]
    print([resources_mocks, exports_mocks])

    client.describe_stacks.return_value = describe_stack

    ids = cli.get_resource_ids(session=session, stack=stack)
    assert len(ids) == 6
    assert ids['LogicalResourceId0'] == 'PhysicalResourceId0'
    assert ids['LogicalResourceId1'] == 'PhysicalResourceId1'
    assert ids['Output_Key_1'] == 'Output_Value_1'
    assert ids['Output_Key_2'] == 'Output_Value_2'
    assert ids['ExportName0'] == 'ExportValue0'
    assert ids['ExportName1'] == 'ExportValue1'

    session.client.assert_called_with('cloudformation')
    client.get_paginator.assert_has_calls([mocker.call('list_stack_resources'), mocker.call('list_exports')])
    resources_mocks.paginate.assert_called_with(StackName=stack)
    exports_mocks.paginate.assert_called_with()
    client.describe_stacks.assert_called_with(StackName=stack)


def test_loads_resources_and_ignores_empty_outputs(mocker, stack):
    session = mocker.Mock(spec=boto3.Session)
    client = session.client.return_value

    resources_summaries = []
    for i in range(2):
        resources = {'StackResourceSummaries': [{
            'LogicalResourceId': 'LogicalResourceId' + str(i),
            'PhysicalResourceId': 'PhysicalResourceId' + str(i)

        }]}
        resources_summaries.append(resources)

    client.get_paginator.return_value.paginate.return_value = resources_summaries

    describe_stack = {
        'Stacks': [{}]
    }

    client.describe_stacks.return_value = describe_stack

    ids = cli.get_resource_ids(session=session, stack=stack)
    assert len(ids) == 2
    assert ids['LogicalResourceId0'] == 'PhysicalResourceId0'
    assert ids['LogicalResourceId1'] == 'PhysicalResourceId1'

    client.describe_stacks.assert_called_with(StackName=stack)


def test_main_replaces_and_calls_aws(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, 'testcf:DeploymentBucket:', 'test2', 'test3'])
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'DeploymentBucket': '1'}

    cli.main()

    subprocess.call.assert_called_with(['aws', 'test1', 'test2', 'test3'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_main_replaces_and_calls_aws_with_profile_and_region(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, 'testcf:DeploymentBucket:', '--profile', 'profile', '--region', 'region'])
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'DeploymentBucket': '1'}

    cli.main()

    subprocess.call.assert_called_with(['aws', 'test1', '--region', 'region', '--profile', 'profile'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_captures_colon_non_greedy(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, 'testcf:A:B:C::12345_12345:'])
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'A:B:C': 'Replace'}

    cli.main()

    subprocess.call.assert_called_with(['aws', 'testReplace:12345_12345:'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_captures_special_characters(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, 'testcf:A-B:C-D:F::12345'])
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'A-B:C-D:F': 'Replace'}

    cli.main()

    subprocess.call.assert_called_with(['aws', 'testReplace:12345'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_main_fails_for_missing_replacement(mocker, stack):
    arguments = ['awsie', stack, 'testcf:DeploymentBucket:']
    mocker.patch.object(sys, 'argv', arguments)
    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')

    get_resource_ids.return_value = {}

    with pytest.raises(SystemExit):
        cli.main()


def test_main_fails_for_missing_awscli(mocker, stack, arguments):
    arguments.extend(['awsie', stack])
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')
    subprocess.call.side_effect = OSError()

    with pytest.raises(SystemExit):
        cli.main()


def test_main_replaces_and_calls_arbitrary_command(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, '--command', 'testcommand', 'testcf:DeploymentBucket:', '--region', 'test'])

    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'DeploymentBucket': '1'}

    cli.main()

    subprocess.call.assert_called_with(['testcommand', 'test1'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_no_subprocess_on_debug(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, '--debug'])

    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {'DeploymentBucket': '1'}

    cli.main()

    subprocess.call.assert_not_called()
    sysexit.assert_called_with(0)


def test_called_with_verbose(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', stack, '--verbose'])
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    cli.main()

    subprocess.call.assert_called_with(['aws'])


def test_no_stack_argument(mocker, stack, sysexit, arguments):
    arguments.extend(['awsie', '--no-stack', 'ec2', 'something'])

    get_resource_ids = mocker.patch.object(cli, 'get_resource_ids')
    mocker.patch.object(cli, 'create_session')
    subprocess = mocker.patch.object(cli, 'subprocess')

    get_resource_ids.return_value = {}

    cli.main()

    subprocess.call.assert_called_with(['aws', 'ec2', 'something'])
    sysexit.assert_called_with(subprocess.call.return_value)


def test_config_file_for_stack_loading(mocker, client, stack, arguments, tmpdir, sysexit):
    arguments.extend(['awsie', stack, '--command', 'testcommand'])

    subprocess = mocker.patch.object(cli, 'subprocess')

    client.get_paginator.return_value.paginate.return_value = []
    client.describe_stacks.return_value = describe_stack

    with Path(tmpdir):
        with open('stack.config.yaml', 'w') as f:
            f.write('stack: {}'.format(stack))

        cli.main()

    client.describe_stacks.assert_called_with(StackName=stack)

    subprocess.call.assert_called_with(['testcommand'])
    sysexit.assert_called_with(subprocess.call.return_value)
