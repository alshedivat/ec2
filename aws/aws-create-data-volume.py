#!/usr/bin/env python
"""
Create a new EBS data volume from a snapshot.
The snapshot is deleted.
"""
import argparse
import boto3
import yaml
import sys

from pprint import pprint

client = boto3.client('ec2')


def create_data_volume(availability_zone='us-east-1a',
                       volume_type='gp2'):
    with open('.config.yaml') as fp:
        config = yaml.load(fp)
    snapshot_id = config['data-snapshot']

    if snapshot_id is None:
        print "Cannot create a data volume. No data snapshots available."
        return

    sys.stdout.write("Creating a volume from snapshot %s..." % snapshot_id)
    sys.stdout.flush()
    response = client.create_volume(SnapshotId=snapshot_id,
                                    AvailabilityZone=availability_zone,
                                    VolumeType=volume_type)
    volume_id = response['VolumeId']
    config['data-volume'] = volume_id
    client.get_waiter('volume_available').wait(VolumeIds=[volume_id])
    sys.stdout.write("Done.\n")

    sys.stdout.write("Deleting the snapshot..."); sys.stdout.flush()
    response = client.delete_snapshot(SnapshotId=snapshot_id)
    config['data-snapshot'] = None
    sys.stdout.write("Done.\n")

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-az", "--availability_zone", metavar="zone",
                        help="availability zone of the requested instances",
                        default="us-east-1a")
    parser.add_argument("-t", "--volume_type", metavar="TYPE",
                        help="type of the requested volume",
                        default="gp2")
    return parser.parse_args()


def main():
    args = parse_args()
    create_data_volume(availability_zone=args.availability_zone,
                       volume_type=args.volume_type)


if __name__ == '__main__':
    main()
