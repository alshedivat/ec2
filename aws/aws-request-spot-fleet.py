#!/usr/bin/env python
"""
Request a new spot instance fleet.
"""
import argparse
import boto3
import datetime
import yaml

from pprint import pprint

client = boto3.client('ec2')

def request_spot_fleet(availability_zone='us-east-1a',
                       iam_fleet_role_name='aws-ec2-spot-fleet-role',
                       image_id='ami-6828317f',
                       instance_type='p2.xlarge',
                       key_name='IDL',
                       spot_price='0.9',
                       valid_days=30,
                       verbose=1):
    with open('.config.yaml') as fp:
        config = yaml.load(fp)

    if config['spot-fleet-request'] is not None:
        print "There already exists an active spot fleet request: %s." % \
              config['spot-fleet-request']
        print "Before requesting a new spot fleet, cancel the existing one."
        return

    iam = boto3.client('iam')
    response = iam.get_role(RoleName=iam_fleet_role_name)
    iam_fleet_role_arn = response['Role']['Arn']

    valid_from = datetime.datetime.utcnow()
    valid_until = valid_from + datetime.timedelta(days=valid_days)
    year, month, day = valid_until.year, valid_until.month, valid_until.day
    valid_until = datetime.datetime(year, month, day)

    request_config = {
        'IamFleetRole': iam_fleet_role_arn,
        'SpotPrice': spot_price,
        'TargetCapacity': 1,
        'ValidUntil': valid_until,
        'TerminateInstancesWithExpiration': True,
        'LaunchSpecifications': [
            {
                'ImageId': image_id,
                'InstanceType': instance_type,
                'KeyName': key_name,
                'Placement': {
                    'AvailabilityZone': availability_zone,
                },
            },
        ],
        'AllocationStrategy': 'lowestPrice',
        'Type': 'request',
    }

    response = client.request_spot_fleet(SpotFleetRequestConfig=request_config)
    config['spot-fleet-request'] = response['SpotFleetRequestId']
    print "Requested a spot fleet:", config['spot-fleet-request']

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("image", help="AMI image id")
    parser.add_argument("-az", "--availability_zone", metavar="zone",
                        help="availability zone of the requested instances",
                        default="us-east-1a")
    parser.add_argument("-iam", "--iam_fleet_role_name", metavar="IAM",
                        help="IAM fleet role name",
                        default="aws-ec2-spot-fleet-role")
    parser.add_argument("-t", "--instance_type", metavar="TYPE",
                        help="type of the requested instances",
                        default="p2.xlarge")
    parser.add_argument("-k", "--key_name", metavar="KEY",
                        help="name of a secret key for accessing the instance",
                        default="IDL")
    parser.add_argument("-p", "--spot_price", metavar="PRICE",
                        help="the max hourly price",
                        default="0.9")
    parser.add_argument("-d", "--valid_days", type=int,
                        help="the number of days the request is valid; "
                             "the request gets canceled afterwards",
                        default=30)
    return parser.parse_args()


def main():
    args = parse_args()
    request_spot_fleet(availability_zone=args.availability_zone,
                       iam_fleet_role_name=args.iam_fleet_role_name,
                       image_id=args.image,
                       instance_type=args.instance_type,
                       key_name=args.key_name,
                       spot_price=args.spot_price,
                       valid_days=args.valid_days)


if __name__ == '__main__':
    main()
