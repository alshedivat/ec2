"""
Supported commands.

The number of available commands is kept as succinct as possible intentionally.
"""
from __future__ import absolute_import, print_function

import os
import sys
import yaml
import datetime

import boto3

from pprint import pprint

from . import utils


# AWS service clients
_EC2 = boto3.client('ec2')
_IAM = boto3.client('iam')
_EFS = boto3.client('efs')


def show(args):
    """Show configuration of the current project."""
    config = utils.load_config(args.config_dir)
    print(yaml.dump(config, default_flow_style=False))


def configure(args):
    """Create a config file in the current working directory.
    """
    config_path = os.path.join(args.config_dir, '.ec2.yaml')
    if os.path.isfile(config_path):
        overwrite = utils.yesno(
            "Found an existing config in '{}'. "
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

    utils.save_config(config, args.config_dir)
    print("Done.")


def refresh(args):
    """Refresh config of the current project."""
    print("Refreshing config for '{}'...".format(args.config_dir))
    config = utils.load_config(args.config_dir)

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

    utils.save_config(config, args.config_dir)
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
        utils.STDOUT.flush()
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
        config = utils.load_config(args.config_dir)
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
            utils.STDOUT.flush()
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
            utils.STDOUT.flush()
        print('-' * 80)


def list_efs(args):
    """List available elastic file systems."""
    response = _EFS.describe_file_systems()

    if not response['FileSystems']:
        print("No available EFS.")
    else:
        for efs in response['FileSystems']:
            print('-' * 80)
            print('FileSystemId:', efs['FileSystemId'])
            print('CreationTime:', efs['CreationTime'])
            print('LifeCycleState:', efs['LifeCycleState'])
            print('NumberOfMountTargets:', efs['NumberOfMountTargets'])
            utils.STDOUT.flush()
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
        except AttributeError:
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
    config = utils.load_config(args.config_dir)

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
    utils.save_config(config, args.config_dir)


def cancel_spot_fleet(args):
    """Cancel the fleet of spot instances."""
    config = utils.load_config(args.config_dir)

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
    utils.save_config(config, args.config_dir)


def create_efs(args):
    """Create an EFS."""
    config = utils.load_config(args.config_dir)

    if config['EC2']['efs'] is not None:
        create_another_efs = utils.yesno(
            "Another EFS is already associated with this project: {}. "
            "Are you sure you want to create another one?"
            .format(config['EC2']['efs']['id']),
            default=False)
        if not create_another_efs:
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

    # It seems like EFS doesn't have waiters (yet?)
    # We need to have EFS available before creating mount targets...
    request_callback = lambda : \
        _EFS.describe_file_systems(
            FileSystemId=config['EC2']['efs']['id'])['FileSystems'][0]
    condition_callback = lambda response: \
        response['LifeCycleState'] != 'available'
    utils.wait(request_callback, condition_callback, sleep_time=3.0)

    print("Creating mount targets...")
    config['EC2']['efs']['mount_targets'] = {}
    response = _EC2.describe_subnets(
        Filters=[
            {
                'Name': 'availability-zone',
                'Values': args.mount_target_zones,
            },
        ])
    subnets = {
        subnet['SubnetId']: subnet['AvailabilityZone']
        for subnet in response['Subnets']
    }

    # Read the existing mount targets
    response = _EFS.describe_mount_targets(
        FileSystemId=config['EC2']['efs']['id'])
    for mount_target in response['MountTargets']:
        if mount_target['SubnetId'] in subnets:
            availability_zone = subnets[mount_target['SubnetId']]
            config['EC2']['efs']['mount_targets'][availability_zone] = \
                mount_target['MountTargetId']
            print("...in {} - already exists.".format(availability_zone))
            utils.STDOUT.flush()

    # Create mount targets (if necessary)
    for subnet_id, availability_zone in subnets.iteritems():
        if availability_zone in config['EC2']['efs']['mount_targets']:
            continue
        print("...in {} - ".format(availability_zone), end="")
        utils.STDOUT.flush()
        response = _EFS.create_mount_target(
            FileSystemId=config['EC2']['efs']['id'],
            SubnetId=subnet['SubnetId'])
        config['EC2']['efs']['mount_targets'][availability_zone] = \
            response['MountTargetId']
        # Wait on mount target being created...
        request_callback = lambda : \
            _EFS.describe_mount_targets(
                MountTargetId=response['MountTargetId'])['MountTargets'][0]
        condition_callback = lambda response: \
            response['LifeCycleState'] != 'available'
        utils.wait(request_callback, condition_callback, sleep_time=3.0)
        print("done.")

    utils.save_config(config, args.config_dir)
    print("Done.")


def delete_efs(args):
    """Delete EFS."""
    config = utils.load_config(args.config_dir)
    if config['EC2']['efs'] is None:
        print("No EFS is associated with this project. Nothing to delete.")
        return
    efs_id = config['EC2']['efs']['id']
    efs_mount_targets = config['EC2']['efs']['mount_targets']

    # Delete the EFS
    delete_efs = utils.yesno(
        "{}WARNING{}: This is a destructive action that cannot be undone. "
        "Are you sure you want to delete the EFS?"
        .format(utils.WARNING_COLOR, utils.RESET_COLOR),
        default=False)
    if delete_efs:
        print("Deleting EFS {} mount targets...".format(efs_id))
        for availability_zone, mount_target_id in efs_mount_targets.iteritems():
            print("...in {} - ".format(availability_zone), end="")
            utils.STDOUT.flush()
            _EFS.delete_mount_target(MountTargetId=mount_target_id)
            # Wait on mount target being deleted...
            request_callback = lambda : \
                _EFS.describe_mount_targets(
                    MountTargetId=mount_target_id)['MountTargets'][0]
            condition_callback = lambda response: \
                response['LifeCycleState'] != 'deleted'
            utils.wait(request_callback, condition_callback, sleep_time=3.0)
            print("done.")

        print("Deleting EFS {}...".format(efs_id))
        _EFS.delete_file_system(FileSystemId=efs_id)
        # Wait on file system being deleted...
        request_callback = lambda : \
            _EFS.describe_file_systems(FileSystemId=efs_id)['FileSystems'][0]
        condition_callback = lambda response: \
            response['LifeCycleState'] != 'deleted'
        utils.wait(request_callback, condition_callback, sleep_time=3.0)
        config['EC2']['efs'] = None
        print("Done.")
    else:
        print("Deletion canceled.")

    utils.save_config(config, args.config_dir)


def mount_efs(args):
    """Mount EFS to specified instances."""
    # TODO
