import os
import sys
import time
import yaml
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


def load_config(config_dir):
    config_path = os.path.join(config_dir, '.ec2.yaml')
    if not os.path.isdir(config_dir):
        print("{}ERROR{}: Directory '{}' does not exist."
              .format(ERROR_COLOR, RESET_COLOR, config_dir))
        sys.exit(1)
    if not os.path.isfile(config_path):
        print("{}ERROR{}: Cannot find ec2 configuration in '{}'. "
              "Please run `configure` command in your project directory "
              "to create a new '.ec2.yaml' config."
              .format(ERROR_COLOR, RESET_COLOR, config_path))
        sys.exit(1)
    with open(config_path) as fp:
        config = yaml.load(fp)
    return config


def save_config(config, config_dir):
    if not os.path.isdir(config_dir):
        print("{}ERROR{}: Directory '{}' does not exist."
              .format(ERROR_COLOR, RESET_COLOR, config_dir))
        sys.exit(1)
    config_path = os.path.join(config_dir, '.ec2.yaml')
    with open(config_path, 'w') as fp:
        yaml.dump(config, fp, default_flow_style=False)


def wait(request_callback, condition_callback, sleep_time=5.0):
    response = None
    while response is None or condition_callback(response):
        time.sleep(sleep_time)
        try:
            response = request_callback()
        except:
            break
