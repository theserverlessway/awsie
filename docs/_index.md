---
title: AWSie
subtitle: CloudFormation aware AWS CLI wrapper
weight: 400
disable_pagination: true
---

 [![Build Status](https://travis-ci.org/flomotlik/awsie.svg?branch=master)](https://travis-ci.org/flomotlik/awsie)
[![PyPI version](https://badge.fury.io/py/awsie.svg)](https://pypi.python.org/pypi/awsie)
[![license](https://img.shields.io/github/license/flomotlik/awsie.svg)](https://github.com/flomotlik/awsie/blob/master/LICENSE)
[![Coverage Status](https://coveralls.io/repos/github/flomotlik/awsie/badge.svg?branch=master)](https://coveralls.io/github/flomotlik/awsie?branch=master)

pronounced /ˈɒzi/ oz-ee like our great friends from down under.

AWSIE is a CloudFormation aware wrapper on top of the AWS CLI. It help you to call an awscli command (or any command), but instead of the actual physical ID of the resource you use the LogicalId, OutputId or ExportName which will be replaced when executing the actual command.

For many different resources AWS can automatically set a random name when creating the resource through Cloudformation. While this has a big upside with resources not clashing when the same stack gets deployed multipe times, a downside is that running a command against a specific resource means you have to write lookup code or use the resource name by hand.

Awsie helps you to do that lookup and call the awscli without any potential for clashes. By supporting both LogicalIds, Output and Export variables you have a lot of flexibility for your automation scripts.

## Installation

Before installing make sure you have the awscli installed as awsie depends on it. We don't install it ourselves so you're able to install the exact version you want to use.

```shell
pip install awscli
```

awsie can be installed through pip:

```shell
pip install awsie
```

Alternatively you can clone this repository and run

```shell
python setup.py install
```

## Quick example

For example when you deploy a CloudFormation stack:

```json
{
    "Resources": {
        "DeploymentBucket": {
            "Type": "AWS::S3::Bucket"
        }
    }
}
```

and then want to list the content of the bucket you can use `awsie`:

```shell
awsie example-stack s3 ls s3://cf:DeploymentBucket: --region us-west-1
```

or if you want to remove `somefile` from the `DeploymentBucket`:

```shell
awsie example-stack s3 rm s3://cf:DeploymentBucket:/somefile --region us-west-1
```

which will replace `cf:DeploymentBucket:` with the actual name of the resource and run the awscli with all arguments you passed to awsie, except for the stack-name (which has to be the first argument):

```shell
aws s3 ls s3://formica-example-stack-deploymentbucket-1jjzisylxreh9 --region us-west-1
aws s3 rm s3://formica-example-stack-deploymentbucket-1jjzisylxreh9/somefile --region us-west-1
```

## Replacement syntax

The replacement syntax is `cf:LOGICAL_ID:` and will insert the PhysicalId of the resource with LOGICAL_ID through the data returned from the list-stack-resources API call. Make sure you don't forget the second colon at the end, its important to be able to separate the syntax when its embedded in another string.

The Regex used is greedy, so `cf:vpc:VPC:` will look for `vpc:VPC` in the variables. That can lead to issues if you want to combine two values directly, e.g. `cf:vpc:VPC1:cf:vpc:VPC2:` which will get `vpc:VPC1:cf:vpc:VPC2` as the replacement key. You need to put a chracter other than `a-zA-Z0-9:` between the values to separate them, e.g. `cf:vpc:VPC1:-cf:vpc:VPC2:`. This is almost never going to be a problem, just in case.

## Arbitrary commands

You can also use `awsie` to run arbitrary commands with replaced values. Simply use the `--command` option to set the specific command and the options you want to use. Make sure the command is in quotes so its handled as one argument to awsie.

```shell
awsie STACK_NAME --command "awslogs get cf:LogGroup: ALL"
```

## Config File

Having to use a specific stack name in the command itself can be an issue as you might change that name in a config file and have to remember to update it in the command as well (e.g. in your Makefile). To solve this awsie supports loading the stack name from a config file.

If the first argument you're giving to awsie is an existing file it will parse the file with a yaml parser and look for the `stack` option. This makes it easy to combine awsie with tools like [`formica`](https://theserverlessway.com/tools/formica/).

So if we have a file named `stack.config.yaml` with the following content:

```yaml
stack: example-stack
```

then we can run the following command which will successfully load data from `example-stack`  just like in the example above.

```bash
awsie stack.config.yaml s3 ls s3://cf:DeploymentBucket: --region us-west-1 
```

## No Stack when just using Exports

In case you want to run a command that just uses CloudFormation Exports as data and therefore don't want to configure a stack you can use the `--no-stack` option.

## Verbose Output

With `--verbose` you'll get a list of all the Keys and Values awsie finds and uses for replacement and the command that will be run before executing it. This makes it easy to debug any potential issues.

## Usage

```bash
usage: awsie [-h] [--version] [--region REGION] [--profile PROFILE]
             [--command] [--no-stack] [--verbose] [--debug]
             stack

Call AWS with substituted CloudFormation values. The first positional argument
is used as the stack or config file name, all other arguments are forwarded to
the AWS CLI. --region and --profile are used to determine which stack to load
the resources from and are passed on as well.\nExample:\n awsie example-stack
s3 ls s3://cf:DeploymentBucket:

positional arguments:
  stack              Stack to load resources from

optional arguments:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  --region REGION    The AWS Region to use
  --profile PROFILE  The AWS Profile to use
  --command          If you run a non AWS CLI command
  --no-stack         If you only use CFN Exports and no Stack data
  --verbose          Print debug output before running the command
  --debug            Print debug output and don't run the command
 ```