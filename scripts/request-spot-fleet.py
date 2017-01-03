"""
Request a new spot instance fleet.
"""
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
                       valid_days=30):
    with open('config.yaml') as fp:
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
    config['spot-fleet-request'] = spot_fleet_response['SpotFleetRequestId']

    with open('config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def main():
    request_spot_fleet()


if __name__ == '__main__':
    main()
