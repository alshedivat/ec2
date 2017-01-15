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
        description="A minimalistic CLI to handle AWS EC2 projects.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config_dir", default=".",
                        help="path to a folder that contains ec2 config")
    commands = parser.add_subparsers(title="ec2 commands")

    # Configuration
    config = commands.add_parser(
        "config",
        description="Create, refresh, or display a config.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    config.set_defaults(cmd=cmd.configure)
    change_config = config.add_mutually_exclusive_group()
    change_config.add_argument("--create", action="store_true",
                               help="create a new config file")
    change_config.add_argument("--refresh", action="store_true",
                               help="refresh the state of config")
    config.add_argument("-k", "--key_name", default="default",
                        help="the name of the secrete key to use with ec2")
    config.add_argument("-iam", "--iam_fleet_role_name", metavar="IAM",
                        default="aws-ec2-spot-fleet-role",
                        help="IAM fleet role name")

    # Listing instances
    list_instances = commands.add_parser(
        "list",
        description="List available instances.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_instances.set_defaults(cmd=cmd.list_available_instances)
    list_instances.add_argument("-t", "--instance_type", metavar="TYPE",
                                help="type of the instances to be listed",
                                default=None)
    list_instances.add_argument("-s", "--instance_state", metavar="STATE",
                                help="state of the instances to be listed",
                                default="running")

    # Operations with spot fleets
    fleet = commands.add_parser(
        "fleet",
        description="Operations with spot fleets.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    fleet_subparsers = fleet.add_subparsers(title="spot fleet commands")

    spot_price_history = fleet_subparsers.add_parser(
        "price", description="display spot price history",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    spot_price_history.set_defaults(cmd=cmd.display_spot_price_history)
    spot_price_history.add_argument(
        "-n", "--last_to_display", type=int, default=10,
        help="number of last prices to display")
    spot_price_history.add_argument(
        "-d", "--days", type=int, default=1,
        help="how many days in the past to consider")
    spot_price_history.add_argument(
        "-t", "--instance_type", metavar="TYPE", default="p2.xlarge",
        help="type of the requested instances")
    spot_price_history.add_argument(
        "-z", "--availability_zone", metavar="ZONE", default="",
        help="availability zone of the requested instances")

    spot_fleet_request = fleet_subparsers.add_parser(
        "request",
        description="Request a spot fleet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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
        "-z", "--availability_zone", metavar="ZONE", default="us-east-1a",
        help="availability zone of the requested instances")

    spot_fleet_cancel = fleet_subparsers.add_parser(
        "cancel",
        description="Cancel a spot fleet request.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    spot_fleet_cancel.set_defaults(cmd=cmd.cancel_spot_fleet)

    # Operations with volumes
    volume = commands.add_parser(
        "volume",
        description="Operations with volumes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volume_subparsers = volume.add_subparsers(title="volume commands")

    volume_restore = volume_subparsers.add_parser(
        "restore",
        description="Restore volume from the snapshot.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volume_restore.set_defaults(cmd=cmd.restore_data_volume)
    volume_restore.add_argument(
        "-t", "--volume_type", metavar="TYPE", default="gp2",
        help="type of the requested volume")
    volume_restore.add_argument(
        "-z", "--availability_zone", metavar="ZONE", default="us-east-1a",
        help="availability zone of the requested instances")

    volume_archive = volume_subparsers.add_parser(
        "archive",
        description="Archive volume to a snapshot.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volume_archive.set_defaults(cmd=cmd.archive_data_volume)

    volume_attach = volume_subparsers.add_parser(
        "attach",
        description="Attach volume to an instance.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volume_attach.set_defaults(cmd=cmd.attach_data_volume)
    volume_attach.add_argument(
        "-i", "--instance_id", required=True,
        help="instance id to which the volume is attached")
    volume_attach.add_argument(
        "-d", "--device", default="/dev/xvdf",
        help="attached volume will be attached as the specified device")

    volume_detach = volume_subparsers.add_parser(
        "detach",
        description="Detach the volume.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    volume_detach.set_defaults(cmd=cmd.detach_data_volume)
    volume_detach.add_argument(
        "-f", "--force", action="store_true",
        help="whether to force-detach the volume (data loss may occur)")

    return parser.parse_args()


def run():
    args = parse_args()
    args.config_dir = os.path.abspath(args.config_dir)
    args.cmd(args)


if __name__ == '__main__':
    run()
