# AWSIE

 [![Build Status](https://travis-ci.org/theserverlessway/awsie.svg?branch=master)](https://travis-ci.org/theserverlessway/awsie)
[![PyPI version](https://badge.fury.io/py/awsie.svg)](https://pypi.python.org/pypi/awsie)
[![license](https://img.shields.io/github/license/theserverlessway/awsie.svg)](LICENSE)
[![Coverage Status](https://coveralls.io/repos/github/theserverlessway/awsie/badge.svg?branch=master)](https://coveralls.io/github/theserverlessway/awsie?branch=master)

pronounced /ˈɒzi/ oz-ee like our great friends from down under.

AWSIE is a CloudFormation aware wrapper on top of the AWS CLI. It help you to call an awscli command (or any command), but instead of the actual physical ID of the resource you use the LogicalId, OutputId or ExportName which will be replaced when executing the actual command.

For many different resources AWS can automatically set a random name when creating the resource through Cloudformation. While this has a big upside with resources not clashing when the same stack gets deployed multipe times, a downside is that running a command against a specific resource means you have to write lookup code or use the resource name by hand.

Awsie helps you to do that lookup and call the awscli without any potential for clashes. By supporting both LogicalIds, Output and Export variables you have a lot of flexibility for your automation scripts.

## Installation

Before installing make sure you have the `awscli` installed as awsie depends on it. We don't install it ourselves so you're able to install the exact version you want to use.

Awsie can be installed through pip:

```shell
pip3 install -U awscli awsie 
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

## Documentation

Check out the full [Documentation and Quickstart on TheServerlessWay.com](https://theserverlessway.com/tools/awsie/)
