import os
import sys
import getpass as gp
import logging

log = logging.getLogger(__name__)

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
STDIN = sys.stdin
STDERR = sys.stderr
STDOUT = sys.stdout

WARNING_COLOR = "\033[33m"
ERROR_COLOR = "\033[31m"
RESET_COLOR = "\033[0m"


def u(s):
    """Mock unicode function for python 2 and 3 compatibility."""
    return s if PY3 or type(s) is unicode else s.decode("utf-8")


def prompt(msg, end="\n"):
    """Prints a message to the stderr stream."""
    if not msg.endswith("\n"):
        msg += end
    STDERR.write(u(msg))


def py23_input(msg=""):
    prompt(msg, end=" ")
    return STDIN.readline().strip()


def yesno(prompt, default=True):
    prompt = prompt.strip() + (" [Y/n]" if default else " [y/N]")
    raw = py23_input(prompt)
    return {'y': True, 'n': False}.get(raw.lower(), default)
