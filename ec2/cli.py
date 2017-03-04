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
    show = commands.add_parser(
        "show",
        description="Show configuration of the current project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    show.set_defaults(cmd=cmd.show)

    configure = commands.add_parser(
        "configure",
        description="Configure ec2 for the current project.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    configure.set_defaults(cmd=cmd.configure)
    configure.add_argument("-k", "--key_name", default="default",
                           help="the name of the secrete key to use with ec2")
    configure.add_argument("-iam", "--iam_fleet_role_name", metavar="IAM",
                           default="aws-ec2-spot-fleet-role",
                           help="IAM fleet role name")

    refresh = commands.add_parser(
        "refresh",
        description="Refresh ec2 configuration.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    refresh.set_defaults(cmd=cmd.refresh)

    # Listing resources (AMIs, instances, snapshots, EFSs)
    list_resources = commands.add_parser(
        "list",
        description="List available resources.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_subparsers = list_resources.add_subparsers(title="list commands")

    list_amis = list_subparsers.add_parser(
        "amis",
        description="List personal AMIs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_amis.set_defaults(cmd=cmd.list_amis)

    list_instances = list_subparsers.add_parser(
        "instances",
        description="List available instances.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_instances.set_defaults(cmd=cmd.list_instances)
    list_instances.add_argument("-a", "--all",
                                help="whether to list all available instances",
                                action="store_true")
    list_instances.add_argument("-t", "--instance_type", metavar="TYPE",
                                help="type of the instances to be listed",
                                default=None)
    list_instances.add_argument("-s", "--instance_state", metavar="STATE",
                                help="state of the instances to be listed",
                                default="running")

    list_efs = list_subparsers.add_parser(
        "efs",
        description="List available elastic file systems (EFS).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_efs.set_defaults(cmd=cmd.list_efs)

    list_snapshots = list_subparsers.add_parser(
        "snapshots",
        description="List available snapshots.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    list_snapshots.set_defaults(cmd=cmd.list_snapshots)

    # Spot fleets
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
        "-n", "--last_to_display", type=int, default=5,
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

    # EFS
    efs = commands.add_parser(
        "efs",
        description="Operations with elastic file systems.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    efs_subparsers = efs.add_subparsers(title="efs commands")

    efs_create = efs_subparsers.add_parser(
        "create",
        description="Create an EFS.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    efs_create.set_defaults(cmd=cmd.create_efs)
    efs_create.add_argument(
        "--creation_token", default="data",
        help="Creation token: string of up to 64 ASCII characters.")
    efs_create.add_argument(
        "--performance_mode", default="generalPurpose",
        help="Performance mode of the file system.")
    efs_create.add_argument(
        "--mount_target_zones", nargs="+",
        default=["us-east-1a", "us-east-1b", "us-east-1c", "us-east-1d"],
        help="Availability zones where to create mount targets.")

    efs_delete = efs_subparsers.add_parser(
        "delete",
        description="Delete an EFS.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    efs_delete.set_defaults(cmd=cmd.delete_efs)

    efs_mount = efs_subparsers.add_parser(
        "mount",
        description="Create an EFS.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    efs_mount.add_argument(
        "-i", "--instances", nargs="+", default=[],
        help="list of instances to mount the EFS to.")

    # Parse and post-process args
    args = parser.parse_args()
    args.config_dir = os.path.abspath(args.config_dir)

    return args
