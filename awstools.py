#!/usr/bin/python3

from configparser import ConfigParser

import subprocess
import boto3
import click
import sys
import os

debug = False
set_profile = 'default'
set_region = None
ip_to_use = ip_to_use

def load_defaults(config_file):
    global debug, set_profile, set_region

    try:
        config = ConfigParser()
        config.read(config_file)

        try:
            debug = config.getboolean('awstools', 'debug')
        except:
            debug = False

        try:
            set_profile = config.get('aws', 'profile').strip('"').strip("'").strip()
        except:
            set_profile = 'default'

        try:
            set_region = config.get('aws', 'region').strip('"').strip("'").strip()
        except:
            set_region = None

        try:
            ip_to_use = config.get('aws', 'useIP').strip('"').strip("'").strip()
        except:
            ip_to_use = 'PrivateIpAddress'

    except:
        pass

def aws_search_instances(name):
    global debug, set_profile, set_region

    try:
        if set_region:
            ec2 = boto3.client(service_name='ec2', region_name=set_region)
        else:
            ec2 = boto3.client(service_name='ec2')
    except Exception as e:
        sys.exit('ERROR: '+str(e))

    if name:
        filter = {}
        filter['Name'] = 'tag:Name'
        filter['Values'] = [ name ]
        instance_filter = [ filter ]

        response = ec2.describe_instances(Filters=instance_filter)
    else:
        response = ec2.describe_instances()

    return response["Reservations"]


@click.group()
@click.option('--profile', default=None, help='AWS profile', type=str)
@click.option('--region', default=None, help='AWS region', type=str)
def awstools(profile, region):
    global debug, set_profile, set_region

    if profile:
        os.environ["AWS_PROFILE"] = profile
    else:
        os.environ["AWS_PROFILE"] = set_profile
    
    set_region = region

@awstools.command()
@click.argument('name', default='')
@click.option('--running', is_flag=True, default=False, help='show only running instances')
def search(name, running):
    global debug, ip_to_use

    reservations = aws_search_instances(name=None)

    for reservation in reservations:
        for instance in reservation["Instances"]:
            try:
                name_found = False
                for tag in instance['Tags']:
                    if tag['Key']=='Name':
                        name_found = True
                        if name in tag['Value'] or not name:
                            if running and instance['State']['Name']=='running':
                                print("{: <60} {: <20} {: <20}".format(tag['Value'], instance[ip_to_use], instance['InstanceId'] ))
                            else:
                                print("{: <60} {: <20} {: <20} {: <20}".format(tag['Value'], instance[ip_to_use], instance['InstanceId'], instance['State']['Name']))
                if not name_found:
                            if running and instance['State']['Name']=='running':
                                print("{: <60} {: <20} {: <20}".format('-', instance[ip_to_use], instance['InstanceId'] ))
                            else:
                                print("{: <60} {: <20} {: <20} {: <20}".format('-', instance[ip_to_use], instance['InstanceId'], instance['State']['Name']))
            except:
                pass
    

@awstools.command()
@click.argument('host')
def ssh(host):
    global debug, ip_to_use
    for reservation in aws_search_instances(host):
        for instance in reservation["Instances"]:
            if instance['State']['Name']=='running':
                try:
                    subprocess.check_call(['ssh', instance[ip_to_use]])
                    return
                except:
                    return
    sys.exit('Not found')

if __name__ == '__main__':
    load_defaults(os.path.join(os.getenv("HOME"), '.awstools/config'))
    awstools()
