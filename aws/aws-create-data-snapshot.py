#!/usr/bin/env python
"""
Create a snapshot from the data volume.
The volume is being deleted.
"""
import argparse
import boto3
import yaml
import sys

from pprint import pprint

client = boto3.client('ec2')


def create_data_snapshot():
    with open('.config.yaml') as fp:
        config = yaml.load(fp)
    volume_id = config['data-volume']

    if volume_id is None:
        print "Cannot create a snapshot. No data volumes available."
        return

    sys.stdout.write("Creating a snapshot from data volume %s..." % volume_id)
    sys.stdout.flush()
    response = client.create_snapshot(VolumeId=volume_id,
                                      Description="The volume with data.")
    snapshot_id = response['SnapshotId']
    config['data-snapshot'] = snapshot_id
    client.get_waiter('snapshot_completed').wait(SnapshotIds=[snapshot_id])
    sys.stdout.write("Done.\n")

    sys.stdout.write("Deleting the volume..."); sys.stdout.flush()
    client.delete_volume(VolumeId=volume_id)
    config['data-volume'] = None
    sys.stdout.write("Done.\n")

    with open('.config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def parse_args():
    parser = argparse.ArgumentParser()
    return parser.parse_args()


def main():
    args = parse_args()
    create_data_snapshot()


if __name__ == '__main__':
    main()
