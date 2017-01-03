"""
List available instances.
"""
import boto3
import yaml
import sys

client = boto3.client('ec2')


def list_available_instances():
    response = client.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': [
                    'running',
                ]
            },
        ]
    )

    for instance in response['Reservations'][0]['Instances']:
        print '-' * 80
        print 'InstanceId:', instance['InstanceId']
        print 'InstanceType:', instance['InstanceType']
        print 'PublicDnsName:', instance['PublicDnsName']
    print '-' * 80


def main():
    list_available_instances()


if __name__ == '__main__':
    main()
