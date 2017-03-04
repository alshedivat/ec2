from __future__ import absolute_import

from .cli import parse_args

__version__ = '0.2.0'


def run():
    args = parse_args()
    args.cmd(args)
