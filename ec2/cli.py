"""
A minimalistic command line interface for EC2.
"""
from __future__ import absolute_import

import argparse
import os

from . import commands as cmd


def parse_args():
    parser = argparse.ArgumentParser(
        prog="ec2",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config_dir", default=".",
                        help="path to a folder that contains ec2 config")
    commands = parser.add_subparsers(title="ec2 commands")

    # Configuration
    config = commands.add_parser(
        "config", help="operations for configuration")
    config.set_defaults(cmd=cmd.configure)
    config.add_argument("--create", action="store_true",
                        help="whether to create a new config file")
    config.add_argument("-k", "--key_name", default="default",
                        help="the name of the secrete key to use with ec2")
    config.add_argument("-iam", "--iam_fleet_role_name", metavar="IAM",
                        default="aws-ec2-spot-fleet-role",
                        help="IAM fleet role name")

    # Listing instances
    list_instances = commands.add_parser(
        "list", help="list available instances")
    list_instances.set_defaults(cmd=cmd.list_available_instances)
    list_instances.add_argument("-t", "--instance_type", metavar="TYPE",
                                help="type of the instances to be listed",
                                default=None)
    list_instances.add_argument("-s", "--instance_state", metavar="STATE",
                                help="state of the instances to be listed",
                                default="running")

    # Operations with spot fleets
    fleet = commands.add_parser(
        "fleet", help="operations with spot fleets")
    fleet_subparsers = fleet.add_subparsers(title="spot fleet commands")

    spot_fleet_request = fleet_subparsers.add_parser(
        "request", help="request a spot fleet")
    spot_fleet_request.set_defaults(cmd=cmd.request_spot_fleet)
    spot_fleet_request.add_argument(
        "-ami", "--image_id", required=True, help="AMI image id")
    spot_fleet_request.add_argument(
        "-t", "--instance_type", metavar="TYPE", default="p2.xlarge",
        help="type of the requested instances")
    spot_fleet_request.add_argument(
        "-n", "--target_capacity", metavar="NUMBER", default=1,
        help="number of instances to request")
    spot_fleet_request.add_argument(
        "-p", "--spot_price", metavar="PRICE", default="0.9",
        help="the max hourly price")
    spot_fleet_request.add_argument(
        "-d", "--valid_days", type=int, default=30,
        help="the number of days the request is valid (canceled afterwards)")
    spot_fleet_request.add_argument(
        "-iam", "--iam_fleet_role_name", metavar="IAM",
        default="aws-ec2-spot-fleet-role", help="IAM fleet role name")
    spot_fleet_request.add_argument(
        "-k", "--key_name", metavar="KEY", default="IDL",
        help="name of a secret key for accessing the instance")
    spot_fleet_request.add_argument(
        "-z", "--availability_zone", metavar="ZONE", default="us-east-1a",
        help="availability zone of the requested instances")

    spot_fleet_cancel = fleet_subparsers.add_parser(
        "cancel", help="cancel a spot fleet request")
    spot_fleet_cancel.set_defaults(cmd=cmd.cancel_spot_fleet)

    # Operations with volumes
    volume = commands.add_parser(
        "volume", help="operations with volumes")
    volume_subparsers = volume.add_subparsers(title="volume commands")

    volume_restore = volume_subparsers.add_parser(
        "restore", help="restore volume from a snapshot")
    volume_restore.set_defaults(cmd=cmd.restore_data_volume)
    volume_restore.add_argument(
        "-t", "--volume_type", metavar="TYPE", default="gp2",
        help="type of the requested volume")
    volume_restore.add_argument(
        "-z", "--availability_zone", metavar="ZONE", default="us-east-1a",
        help="availability zone of the requested instances")

    volume_archive = volume_subparsers.add_parser(
        "archive", help="archive volume to a snapshot")
    volume_archive.set_defaults(cmd=cmd.archive_data_volume)

    volume_attach = volume_subparsers.add_parser(
        "attach", help="attach volume to an instance")
    volume_attach.set_defaults(cmd=cmd.attach_data_volume)
    volume_attach.add_argument(
        "-i", "--instance_id", required=True,
        help="instance id to which the volume is attached")

    return parser.parse_args()


def run():
    args = parse_args()
    args.config_dir = os.path.abspath(args.config_dir)
    args.cmd(args)


if __name__ == '__main__':
    run()
