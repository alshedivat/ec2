"""
Supported commands.

The number of available commands is kept as succinct as possible intentionally.
"""
from __future__ import print_function

import argparse
import configparser
import datetime
import boto3
import yaml
import sys
import os

from pprint import pprint


def configure(args):
    """Create a config file in the current working directory.
    """
    if args.create:
        print("Creating new config in %s..." % args.config_dir, end="")
        config = configparser.ConfigParser(allow_no_value=True)

        config['AWS'] = {}

        # Secret key name
        config['AWS']['key_name'] = args.key_name

        # IAM fleet role name
        iam = boto3.client('iam')
        response = iam.get_role(RoleName=args.iam_fleet_role_name)
        iam_fleet_role_arn = response['Role']['Arn']
        config['AWS']['iam_fleet_role_arn'] = iam_fleet_role_arn

        config['EC2'] = {
            'snapshot_id': None,
            'volume_id': None,
            'volume_zone': None,
            'volume_attached_to': None,
            'spot_fleet_id': None,
            'spot_fleet_zone': None,
        }

        save_config(config, args.config_dir)
        print("Done.")

    elif args.refresh:
        print("Refreshing config in %s..." % args.config_dir, end="")
        config = load_config(args.config_dir)
        ec2 = boto3.client('ec2')

        # Check on the spot fleet
        if config['EC2']['spot_fleet_id'] is not None:
            response = ec2.describe_spot_fleet_instances(
                SpotFleetRequestId=config['EC2']['spot_fleet_id'])
            if not response['ActiveInstances']:
                config['EC2']['spot_fleet_id'] = None
                config['EC2']['spot_fleet_zone'] = None

        # Check on the volume
        if config['EC2']['volume_id'] is not None:
            response = ec2.describe_volumes(
                VolumeIds=[config['EC2']['volume_id']])
            if (not response['Volumes'] or
                (response['Volumes'][0]['State'] != 'available' and
                 response['Volumes'][0]['State'] != 'in-use')):
                config['EC2']['volume_id'] = None
                config['EC2']['volume_zone'] = None

        # Check  on the instance the volume is attached to
        if config['EC2']['volume_attached_to'] is not None:
            response = ec2.describe_instance_status(
                InstanceIds=[config['EC2']['volume_attached_to']])
            if not response['InstanceStatuses']:
                config['EC2']['volume_attached_to'] = None
            else:
                instance_status = response['InstanceStatuses'][0]
                if instance_status['InstanceState']['Name'] != 'running':
                    config['EC2']['volume_attached_to'] = None

        save_config(config, args.config_dir)
        print("Done.")

    else:
        filepath = os.path.join(args.config_dir, '.ec2.ini')
        with open(filepath) as fp:
            for line in fp.readlines():
                print(line.strip())


def load_config(config_dir):
    """Load and parse config from a file.
    """
    filepath = os.path.join(config_dir, '.ec2.ini')
    if not os.path.isdir(config_dir):
        raise ValueError("%s is not an existing directory!" % config_dir)
    if not os.path.isfile(filepath):
        raise ValueError("No config file found in %s." % config_dir)
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(filepath)
    return config


def save_config(config, config_dir):
    """Save config to a file.
    """
    if not os.path.isdir(config_dir):
        raise ValueError("%s is not an existing directory!" % config_dir)
    filepath = os.path.join(config_dir, '.ec2.ini')
    with open(filepath, 'w') as fp:
        config.write(fp)


def list_available_instances(args):
    """List available instances.
    """
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

    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(Filters=filters)

    for reservation in response['Reservations']:
        instance = reservation['Instances'][0]
        print('-' * 80)
        print('InstanceId:', instance['InstanceId'])
        print('InstanceType:', instance['InstanceType'])
        print('PublicDnsName:', instance['PublicDnsName'])
        print('PublicIpAddress:', instance['PublicIpAddress'])
        sys.stdout.flush()
    print('-' * 80)


def display_spot_price_history(args):
    """Display the spot price history.
    """
    current_datetime = datetime.datetime.utcnow()
    start_datetime = current_datetime - datetime.timedelta(days=args.days)

    ec2 = boto3.client('ec2')
    response = ec2.describe_spot_price_history(
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
    """Request a new fleet of spot instances.
    """
    config = load_config(args.config_dir)

    if config['EC2']['spot_fleet_id'] is not None:
        print("There already exists an active spot fleet request according to "
              "the current config: %s." % config['EC2']['spot-fleet-request'])
        print("Before requesting a new spot fleet, "
              "please cancel the existing one to avoid a budget leak.")
        return

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

    ec2 = boto3.client('ec2')
    response = ec2.request_spot_fleet(SpotFleetRequestConfig=request_config)
    config['EC2']['spot_fleet_id'] = response['SpotFleetRequestId']
    config['EC2']['spot_fleet_zone'] = args.availability_zone
    print("Requested a spot fleet:", response['SpotFleetRequestId'])

    save_config(config, args.config_dir)


def cancel_spot_fleet(args):
    """Cancel the fleet of spot instances.
    """
    config = load_config(args.config_dir)

    spot_fleet_id = config['EC2']['spot_fleet_id']
    if spot_fleet_id is None:
        print("No active spot fleet requests. Nothing to cancel.")
        return

    ec2 = boto3.client('ec2')

    # Make sure the volume is marked detached if necessary
    response = ec2.describe_spot_fleet_instances(
        SpotFleetRequestId=spot_fleet_id)
    instances_to_be_terminated = set(
        [instance['InstanceId'] for instance in response['ActiveInstances']])
    if config['EC2']['volume_attached_to'] in instances_to_be_terminated:
        config['EC2']['volume_attached_to'] = None

    print("Canceling spot fleet request %s..." % spot_fleet_id, end="")
    ec2.cancel_spot_fleet_requests(
        SpotFleetRequestIds=[spot_fleet_id],
        TerminateInstances=True)
    print("Done.")

    config['EC2']['spot_fleet_id'] = None
    config['EC2']['spot_fleet_zone'] = None
    save_config(config, args.config_dir)


def restore_data_volume(args):
    """Restore an EBS data volume from a snapshot. Deletes the snapshot.
    """
    config = load_config(args.config_dir)
    snapshot_id = config['EC2']['snapshot_id']

    if snapshot_id is None:
        print("Cannot restore a volume. No data snapshots available.")
        return

    ec2 = boto3.client('ec2')

    print("Restoring a volume from snapshot %s..." % snapshot_id, end="")
    sys.stdout.flush()
    response = ec2.create_volume(SnapshotId=snapshot_id,
                                 AvailabilityZone=args.availability_zone,
                                 VolumeType=args.volume_type)
    volume_id = response['VolumeId']
    ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
    config['EC2']['volume_id'] = volume_id
    config['EC2']['volume_zone'] = args.availability_zone
    print("Done.")

    print("Deleting the snapshot...", end="")
    sys.stdout.flush()
    response = ec2.delete_snapshot(SnapshotId=snapshot_id)
    config['EC2']['snapshot_id'] = None
    print("Done.")

    save_config(config, args.config_dir)


def archive_data_volume(args):
    """Create a snapshot from the data volume. Deletes the volume.
    """
    config = load_config(args.config_dir)
    volume_id = config['EC2']['volume_id']

    if volume_id is None:
        print("Cannot create a snapshot. No data volumes available.")
        return

    ec2 = boto3.client('ec2')

    print("Creating a snapshot from volume %s..." % volume_id, end="")
    sys.stdout.flush()
    response = ec2.create_snapshot(VolumeId=volume_id,
                                   Description="The volume with data.")
    snapshot_id = response['SnapshotId']
    ec2.get_waiter('snapshot_completed').wait(SnapshotIds=[snapshot_id])
    config['EC2']['snapshot_id'] = snapshot_id
    print("Done.")

    print("Deleting the volume...", end="")
    sys.stdout.flush()
    ec2.delete_volume(VolumeId=volume_id)
    ec2.get_waiter('volume_deleted').wait(VolumeIds=[volume_id])
    config['EC2']['volume_id'] = None
    config['EC2']['volume_zone'] = None
    print("Done.")

    save_config(config, args.config_dir)


def attach_data_volume(args):
    """Attach the data volume to an instance.
    """
    config = load_config(args.config_dir)
    volume_id = config['EC2']['volume_id']
    attached_to = config['EC2']['volume_attached_to']

    if volume_id is None:
        print("No data volumes available. First create a data volume. "
              "I you have a snapshot of a data volume, you can restore the "
              "volume using `ec2 volume restore` command. "
              "Type `ec2 volume restore -h` for help.")
        return

    if attached_to is not None:
        print("The data volume %s is already attached to instance %s. "
              "The volume cannot be attached to multiple instances." %
              (volume_id, attached_to))
        return

    ec2 = boto3.client('ec2')

    print("Attaching volume %s to instance %s..." %
          (volume_id, args.instance_id), end="")
    sys.stdout.flush()
    response = ec2.attach_volume(VolumeId=volume_id,
                                 InstanceId=args.instance_id,
                                 Device=args.device)
    ec2.get_waiter('volume_in_use').wait(VolumeIds=[volume_id])
    config['EC2']['volume_attached_to'] = args.instance_id
    print("Done.")

    save_config(config, args.config_dir)


def detach_data_volume(args):
    """Detach the data volume from an instance.
    """
    config = load_config(args.config_dir)
    volume_id = config['EC2']['volume_id']
    attached_to = config['EC2']['volume_attached_to']

    if volume_id is None:
        print("No data volumes available. Nothing to do.")
        return

    if attached_to is None:
        print("The volume %s is not attached. Nothing to do." % volume_id)
        return

    ec2 = boto3.client('ec2')

    print("Detaching volume %s from instance %s..." %
          (volume_id, attached_to), end="")
    sys.stdout.flush()
    response = ec2.detach_volume(VolumeId=volume_id, Force=args.force)
    ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
    config['EC2']['volume_attached_to'] = None
    print("Done.")

    save_config(config, args.config_dir)
