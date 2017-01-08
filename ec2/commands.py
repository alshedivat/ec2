"""
Supported commands.

The number of available commands is kept as succinct as possible intentionally.
"""
from __future__ import print_function

import argparse
import datetime
import boto3
import yaml
import sys
import os


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
        sys.stdout.flush()
    print('-' * 80)


def request_spot_fleet(args):
    """Request a new fleet of spot instances.
    """
    with open('.config.yaml') as fp:
        config = yaml.load(fp)

    if config['spot_fleet_id'] is not None:
        print("There already exists an active spot fleet request according to "
              "the current config: %s." % config['spot-fleet-request'])
        print("Before requesting a new spot fleet, "
              "please cancel the existing one to avoid a budget leak.")
        return

    iam = boto3.client('iam')
    response = iam.get_role(RoleName=args.iam_fleet_role_name)
    iam_fleet_role_arn = response['Role']['Arn']

    valid_from = datetime.datetime.utcnow()
    valid_until = valid_from + datetime.timedelta(days=args.valid_days)
    year, month, day = valid_until.year, valid_until.month, valid_until.day
    valid_until = datetime.datetime(year, month, day)

    request_config = {
        'IamFleetRole': iam_fleet_role_arn,
        'SpotPrice': args.spot_price,
        'TargetCapacity': args.target_capacity,
        'ValidUntil': args.valid_until,
        'TerminateInstancesWithExpiration': True,
        'LaunchSpecifications': [
            {
                'ImageId': args.image_id,
                'InstanceType': args.instance_type,
                'KeyName': args.key_name,
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
    config['spot_fleet_id'] = response['SpotFleetRequestId']
    print("Requested a spot fleet:", config['spot_fleet_id'])

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def cancel_spot_fleet(args):
    """Cancel the fleet of spot instances.
    """
    with open('.config.yaml') as fp:
        config = yaml.load(fp)

    spot_fleet_id = config['spot_fleet_id']
    if spot_fleet_id is None:
        print("No active spot fleet requests. Nothing to cancel.")
        return

    print("Canceling spot fleet request %s..." % spot_fleet_id, end="")
    client.cancel_spot_fleet_requests(
        SpotFleetRequestIds=[spot_fleet_id],
        TerminateInstances=True)
    print("Done.")

    config['spot_fleet_id'] = None
    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def restore_data_volume(args):
    """Restore an EBS data volume from a snapshot. Deletes the snapshot.
    """
    with open('.config.yaml') as fp:
        config = yaml.load(fp)
    snapshot_id = config['snapshot_id']

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
    config['volume_id'] = volume_id
    ec2.get_waiter('volume_available').wait(VolumeIds=[volume_id])
    print("Done.")

    print("Deleting the snapshot...", end="")
    sys.stdout.flush()
    response = ec2.delete_snapshot(SnapshotId=snapshot_id)
    config['snapshot_id'] = None
    print("Done.")

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def archive_data_volume(args):
    """Create a snapshot from the data volume. Deletes the volume.
    """
    with open('.config.yaml') as fp:
        config = yaml.load(fp)
    volume_id = config['volume_id']

    if volume_id is None:
        print("Cannot create a snapshot. No data volumes available.")
        return

    ec2 = boto3.client('ec2')

    print("Creating a snapshot from volume %s..." % volume_id, end="")
    sys.stdout.flush()
    response = ec2.create_snapshot(VolumeId=volume_id,
                                   Description="The volume with data.")
    snapshot_id = response['SnapshotId']
    config['snapshot_id'] = snapshot_id
    ec2.get_waiter('snapshot_completed').wait(SnapshotIds=[snapshot_id])
    print("Done.")

    print("Deleting the volume...", end="")
    sys.stdout.flush()
    ec2.delete_volume(VolumeId=volume_id)
    config['volume_id'] = None
    print("Done.")

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def attach_data_volume(args):
    """Attach the data volume to an instance.
    """
    with open('.config.yaml') as fp:
        config = yaml.load(fp)
    volume_id = config['volume_id']
    attached_to = config['volume_attached_to']

    if volume_id is None:
        sys.stdout.write(
            "No data volumes available. First create a data volume. "
            "I you have a snapshot of a data volume, you can create it "
            "from snapshot using `aws-create-data-volume` utility.")
        return

    if attached_to is not None:
        sys.stdout.write(
            "The data volume %s is already attached to instance %s. "
            "The volume cannot be attached to multiple instances." %
            (volume_id, attached_to))
        return

    sys.stdout.write("Attaching the volume..."); sys.stdout.flush()
    response = client.attach_volume(VolumeId=volume_id,
                                    InstanceId=args.instance_id,
                                    Device='xvdh')
    config['volume_attached_to'] = args.instance_id
    sys.stdout.write("Done.\n")

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)