"""Packaging settings."""

from os.path import abspath, dirname, join, isfile

from setuptools import setup

from awsie import __version__

this_dir = abspath(dirname(__file__))
path = join(this_dir, 'README.rst')
long_description = ''
if isfile(path):
    with open(path) as file:
        long_description = file.read()

setup(
    name='awsie',
    version=__version__,
    description='CloudFormation aware aws cli wrapper.',
    long_description=long_description,
    url='https://github.com/flomotlik/awsie',
    author='Florian Motlik',
    author_email='flo@flomotlik.me',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='aws, cloud, awscli',
    packages=['awsie'],
    install_requires=['boto3'],
    entry_points={
        'console_scripts': [
            'awsie=awsie.cli:main',
        ],
    }
)
