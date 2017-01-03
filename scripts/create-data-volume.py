"""
Create a new EBS data volume from a snapshot.
The snapshot is deleted.
"""
import boto3
import yaml
import sys

from pprint import pprint

client = boto3.client('ec2')


def create_data_volume(availability_zone='us-east-1a',
                       volume_type='gp2'):
    with open('config.yaml') as fp:
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

    with open('config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def main():
    create_data_volume()


if __name__ == '__main__':
    main()
