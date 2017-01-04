#!/usr/bin/env python
"""
Cancel a spot instance fleet.
"""
import boto3
import yaml
import sys

client = boto3.client('ec2')


def cancel_spot_fleet_request():
    with open('config.yaml') as fp:
        config = yaml.load(fp)

    spot_fleet_id = config['spot-fleet-request']
    if spot_fleet_id is None:
        print "No active spot fleet requests. Nothing to cancel."
        return

    sys.stdout.write("Canceling spot fleet request %s..." % spot_fleet_id)
    client.cancel_spot_fleet_requests(
        SpotFleetRequestIds=[spot_fleet_id],
        TerminateInstances=True)
    sys.stdout.write("Done.\n")

    config['spot-fleet-request'] = None
    with open('config.yaml', 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def main():
    cancel_spot_fleet_request()


if __name__ == '__main__':
    main()
