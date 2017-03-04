"""
Supported commands.

The number of available commands is kept as succinct as possible intentionally.
"""
from __future__ import absolute_import, print_function

import datetime
import boto3
import yaml
import sys
import os

from pprint import pprint

from .utils import *


# AWS service clients
_EC2 = boto3.client('ec2')
_IAM = boto3.client('iam')
_EFS = boto3.client('efs')


def _load_config(config_dir):
    config_path = os.path.join(config_dir, '.ec2.yaml')
    if not os.path.isdir(config_dir):
        print("{}ERROR{}: Directory '{}' does not exist."
              .format(ERROR_COLOR, RESET_COLOR, config_dir))
        sys.exit(1)
    if not os.path.isfile(config_path):
        print("{}ERROR{}: Cannot find ec2 configuration in '{}'. "
              "Please run `configure` command in your project directory "
              "to create a new '.ec2.yaml' config."
              .format(ERROR_COLOR, RESET_COLOR, config_path))
        sys.exit(1)
    with open(config_path) as fp:
        config = yaml.load(fp)
    return config


def _save_config(config, config_dir):
    if not os.path.isdir(config_dir):
        print("{}ERROR{}: Directory '{}' does not exist."
              .format(ERROR_COLOR, RESET_COLOR, config_dir))
        sys.exit(1)
    config_path = os.path.join(config_dir, '.ec2.yaml')
    with open(config_path, 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def show(args):
    """Show configuration of the current project."""
    config = _load_config(args.config_dir)
    print(yaml.dump(config, default_flow_style=False))


def configure(args):
    """Create a config file in the current working directory.
    """
    config_path = os.path.join(args.config_dir, '.ec2.yaml')
    if os.path.isfile(config_path):
        overwrite = yesno("Found an existing config in '{}'. "
                          "Would you like to overwrite?".format(config_path),
                          default=False)
        if not overwrite:
            return

    print("Initializing ec2 config in '{}'...".format(config_path))

    config = {
        'AWS': {},
        'EC2': {},
    }

    # Secret key name
    config['AWS']['key_name'] = args.key_name

    # IAM fleet role name
    response = _IAM.get_role(RoleName=args.iam_fleet_role_name)
    iam_fleet_role_arn = response['Role']['Arn']
    config['AWS']['iam_fleet_role_arn'] = iam_fleet_role_arn

    config['EC2'] = {
        'spot_fleet': None,
        'efs': None,
    }

    _save_config(config, args.config_dir)
    print("Done.")


def refresh(args):
    """Refresh config of the current project."""
    config_path = os.path.join(args.config_dir, '.ec2.yaml')
    if not os.path.isfile(config_path):
        print("ec2 has not been configured for the current project. "
              "Please run `configure` command in your project directory "
              "to create a new '.ec2.yaml' config.")
        return

    print("Refreshing config for '{}'...".format(args.config_dir))
    config = _load_config(args.config_dir)

    # Check on the spot fleet
    if config['EC2']['spot_fleet'] is not None:
        response = _EC2.describe_spot_fleet_instances(
            SpotFleetRequestId=config['EC2']['spot_fleet']['id'])
        if not response['ActiveInstances']:
            config['EC2']['spot_fleet'] = None
        else:
            config['EC2']['spot_fleet']['instances'] = \
                response['ActiveInstances']

    # Check on the EFS
    if config['EC2']['efs'] is not None:
        response = _EFS.describe_file_systems(
            FileSystemId=config['EC2']['efs'])
        if not response['FileSystems']:
            config['EC2']['efs'] = None

    _save_config(config, args.config_dir)
    print("Done.")


def list_amis(args):
    """List personal AMIs."""
    response = _EC2.describe_images(Owners=['self'])

    for ami in response['Images']:
        print('-' * 80)
        print('Name:', ami['Name'])
        print('Description', ami['Description'])
        print('ImageId:', ami['ImageId'])
        print('ImageType:', ami['ImageType'])
        print('CreationDate:', ami['CreationDate'])
        print('State:', ami['State'])
        sys.stdout.flush()
    print('-' * 80)


def list_instances(args):
    """List available instances."""
    filters = []
    if args.instance_state is not None:
        filters.append({
            'Name': 'instance-state-name',
            'Values': [args.instance_state]
        })
    if args.instance_type is not None:
        filters.append({
            'Name': 'instance-type',
            'Values': [args.instance_type]
        })
    if not args.all:
        print("Instances used in the current project:")
        config = _load_config(args.config_dir)
        if config['EC2']['spot_fleet'] is not None:
            response = _EC2.describe_spot_fleet_instances(
                SpotFleetRequestId=config['EC2']['spot_fleet']['id'])
            spot_instance_request_id = \
                response['ActiveInstances'][0]['SpotInstanceRequestId']
            filters.append({
                'Name': 'spot-instance-request-id',
                'Values': [spot_instance_request_id],
            })
        else:
            print("No instances are in use.")
            return
    else:
        print("Available instances:")

    response = _EC2.describe_instances(Filters=filters)
    if not response['Reservations']:
        print("No available instances.")
    else:
        for reservation in response['Reservations']:
            instance = reservation['Instances'][0]
            print('-' * 80)
            print('InstanceId:', instance['InstanceId'])
            print('InstanceType:', instance['InstanceType'])
            print('PublicDnsName:', instance['PublicDnsName'])
            print('PublicIpAddress:', instance['PublicIpAddress'])
            sys.stdout.flush()
        print('-' * 80)


def list_snapshots(args):
    """List available snapshots."""
    response = _EC2.describe_snapshots(OwnerIds=['self'])

    if not response['Snapshots']:
        print("No available snapshots.")
    else:
        for snapshot in response['Snapshots']:
            print('-' * 80)
            print('Description:', snapshot['Description'])
            print('SnapshotId:', snapshot['SnapshotId'])
            print('VolumeId:', snapshot['VolumeId'])
            print('State:', snapshot['State'])
            sys.stdout.flush()
        print('-' * 80)


def list_efs(args):
    """List available elastic file systems."""
    response = _EFS.describe_file_systems()

    if not response['FileSystems']:
        print("No available EFS.")
    else:
        for efs in response['FileSystems']:
            print('-' * 80)
            print('Name', efs['Name'])
            print('FileSystemId:', efs['FileSystemId'])
            print('CreationTime:', efs['CreationTime'])
            print('LifeCycleState:', efs['LifeCycleState'])
            print('NumberOfMountTargets:', efs['NumberOfMountTargets'])
            sys.stdout.flush()
        print('-' * 80)


def display_spot_price_history(args):
    """Display the spot price history."""
    current_datetime = datetime.datetime.utcnow()
    start_datetime = current_datetime - datetime.timedelta(days=args.days)

    response = _EC2.describe_spot_price_history(
        StartTime=start_datetime,
        InstanceTypes=[args.instance_type],
        AvailabilityZone=args.availability_zone,
        ProductDescriptions=['Linux/UNIX'])

    prices_per_zone = {}
    for price in response['SpotPriceHistory']:
        try:
            prices_per_zone[price['AvailabilityZone']].append(
                (price['Timestamp'], price['SpotPrice'])
            )
        except:
            prices_per_zone[price['AvailabilityZone']] = [
                (price['Timestamp'], price['SpotPrice'])
            ]

    print("\nLast %d prices for %s instances:" %
          (args.last_to_display, args.instance_type))
    for z, prices in sorted(prices_per_zone.items()):
        print("\n%s %s %s" % ('-' * 3, z, '-' * 35))
        for p in sorted(prices)[-args.last_to_display:]:
            print("%s UTC\t-\t%s" % (p[0], p[1]))
    print('-' * 50 + '\n')


def request_spot_fleet(args):
    """Request a new fleet of spot instances."""
    config = _load_config(args.config_dir)

    if config['EC2']['spot_fleet'] is not None:
        print("According to the current config, there already exists"
              "an active spot fleet request: {spot_fleet_id}. "
              "Before requesting a new spot fleet please cancel the existing "
              "one to avoid resource leaks."
              .format(spot_fleet_id=config['EC2']['spot_fleet']['id']))
        return

    # Resolve ValidUntil date
    valid_from = datetime.datetime.utcnow()
    valid_until = valid_from + datetime.timedelta(days=args.valid_days)
    year, month, day = valid_until.year, valid_until.month, valid_until.day
    valid_until = datetime.datetime(year, month, day)

    request_config = {
        'IamFleetRole': config['AWS']['iam_fleet_role_arn'],
        'SpotPrice': args.spot_price,
        'TargetCapacity': args.target_capacity,
        'ValidUntil': valid_until,
        'TerminateInstancesWithExpiration': True,
        'LaunchSpecifications': [
            {
                'ImageId': args.image_id,
                'InstanceType': args.instance_type,
                'KeyName': config['AWS']['key_name'],
                'Placement': {
                    'AvailabilityZone': args.availability_zone,
                },
            },
        ],
        'AllocationStrategy': 'lowestPrice',
        'Type': 'request',
    }

    response = _EC2.request_spot_fleet(SpotFleetRequestConfig=request_config)
    config['EC2']['spot_fleet'] = {
        'id': response['SpotFleetRequestId'],
        'instances': [],
    }
    print("Requested a spot fleet:", response['SpotFleetRequestId'])
    _save_config(config, args.config_dir)


def cancel_spot_fleet(args):
    """Cancel the fleet of spot instances."""
    config = _load_config(args.config_dir)

    if config['EC2']['spot_fleet'] is None:
        print("No active spot fleet requests. Nothing to cancel.")
        return

    print("Canceling spot fleet request {}..."
          .format(config['EC2']['spot_fleet']['id']))
    ec2.cancel_spot_fleet_requests(
        SpotFleetRequestIds=[config['EC2']['spot_fleet']['id']],
        TerminateInstances=True)
    print("Done.")

    config['EC2']['spot_fleet'] = None
    _save_config(config, args.config_dir)


def create_efs(args):
    """Create an EFS."""
    config = _load_config(args.config_dir)

    if config['EC2']['efs'] is not None:
        if not yesno(
            "Another EFS is already associated with this project: {}. "
            "Are you sure you want to create another one?"
            .format(config['EC2']['efs']['id']),
            default=False):
            return

    print("Creating an EFS with token '{}'...".format(args.creation_token))
    try:
        response = _EFS.create_file_system(
            CreationToken=args.creation_token,
            PerformanceMode=args.performance_mode)
    except:
        print("File system with token '{}' already exists."
              .format(args.creation_token))
        response = _EFS.describe_file_systems(
            CreationToken=args.creation_token)
        response = response['FileSystems'][0]
    config['EC2']['efs'] = {
            'id': response['FileSystemId'],
            'CreationTime': str(response['CreationTime']),
            'PerformanceMode': response['PerformanceMode'],
        }

    print("Creating mount targets...")
    response = _EC2.describe_subnets(
        Filters=[
            {
                'Name': 'availability-zone',
                'Values': args.mount_target_zones,
            },
        ])
    config['EC2']['efs']['mount_targets'] = []
    for subnet in response['Subnets']:
        print("...{}".format(subnet['AvailabilityZone']))
        _EFS.create_mount_target(
            FileSystemId=config['EC2']['efs']['id'],
            SubnetId=subnet['SubnetId'])
        config['EC2']['efs']['mount_targets'].append(
            subnet['AvailabilityZone'])
    _save_config(config, args.config_dir)
    print("Done.")


def delete_efs(args):
    """Delete EFS."""
    config = _load_config(args.config_dir)
    if config['EC2']['efs'] is None:
        print("No EFS is associated with this project. Nothing to delete.")
        return

    print("Deleting EFS {}...".format(config['EC2']['efs']['id']))
    if yesno("{}WARNING{}: This is a destructive action that cannot be undone. "
             "Are you sure you want to delete the EFS?"
             .format(WARNING_COLOR, RESET_COLOR),
             default=False):
        _EFS.delete_file_system(FileSystemId=config['EC2']['efs']['id'])
        print("Done.")
    else:
        print("Deletion canceled.")


def mount_efs(args):
    """Mount EFS to specified instances."""
    # TODO
