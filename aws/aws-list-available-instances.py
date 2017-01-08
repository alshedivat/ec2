#!/usr/bin/env python
"""
List available instances.
"""
import argparse
import boto3
import yaml
import sys

client = boto3.client('ec2')


def list_available_instances(instance_state='running',
                             instance_type=None):
    filters = []
    if instance_state is not None:
        filters.append({
            'Name': 'instance-state-name',
            'Values': [instance_state]
        })
    if instance_type is not None:
        filters.append({
            'Name': 'instance-type',
            'Values': [instance_type]
        })
    response = client.describe_instances(Filters=filters)

    for reservation in response['Reservations']:
        instance = reservation['Instances'][0]
        print '-' * 80
        print 'InstanceId:', instance['InstanceId']
        print 'InstanceType:', instance['InstanceType']
        print 'PublicDnsName:', instance['PublicDnsName']
    print '-' * 80


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--instance_type", metavar="TYPE",
                        help="type of the requested instances",
                        default=None)
    parser.add_argument("-s", "--instance_state", metavar="STATE",
                        help="name of a secret key for accessing the instance",
                        default="running")
    return parser.parse_args()


def main():
    args = parse_args()
    list_available_instances(instance_state=args.instance_state,
                             instance_type=args.instance_type)


if __name__ == '__main__':
    main()
