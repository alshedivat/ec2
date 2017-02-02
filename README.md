A minimalistic CLI for managing AWS EC2 projects
================================================

This is an AWS EC2 CLI build upon [AWS Python SDK](https://boto3.readthedocs.io/en/latest/).
It was designed to support the standard workflow of small computational projects.
The number of available commands is intentionally kept as succinct as possible.

## Features
- Commands for working with spot fleets (view pricing, request and release resources)
- Commands for working with data volumes (archiving to / restoring data volumes from snapshots)
- Support for multiple projects (each project gets a separate config file)

## Why?
AWS EC2 has the [native CLI](https://aws.amazon.com/cli/), but it is extremely cumbersome to use for a number of reasons:

- The native AWS CLI supports the entire spectrum of AWS services and is enormous in the number of possible calls and arguments.
Most of the native API is useless for the workflow of a small project.
- The return format is pure JSON, which not very human-friendly.
- You end up writing wrappers around the native CLI for each of your new projects or give up and use the web-interface (and sometimes forget to release the resources you requested and pay extra for no value).

## Installation
Clone the repository and install the `ec2` package as using pip as follows (use `sudo` if necessary):

```bash
$ git clone https://github.com/alshedivat/ec2.git && cd ec2
$ pip install -e .
```

After the installation, you will get access to the `ec2` command in your terminal.

## Usage
We assume that you have worked with AWS EC2 instances and have already set up a few necessary things, such as the SSH key.
If you have no previous experience with AWS, we recommend you go through to the [EC2 getting started guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html) and play with the [AWS web interface](https://aws.amazon.com/console/).

### Initialization
Initialize a new ec2 project:

```bash
$ cd /path/to/your/project/directory
$ ec2 config --create
```

This will create `.ec2.ini` configuration file in your project directory of the following structure:

```
[AWS]
key_name = default
iam_fleet_role_arn = arn:aws:iam::XXXXXXXXXXXX:role/aws-ec2-spot-fleet-role

[EC2]
snapshot_id
volume_zone
spot_fleet_zone
volume_attached_to
spot_fleet_id
volume_id
```

### Working with spot fleets
Suppose, we would like to request a spot fleet of `p2.xlarge` instances.
You can decide in which zone to request the fleet by requesting the latest prices for the spot instances in each zone:

```bash
$ ec2 fleet price -t p2.xlarge
```

Now, let's request a fleet of 2 instances in the `us-east-1b` zone for 3 days:

```bash
$ ec2 fleet request -ami IMAGE_ID -n 2 -d 3 -t p2.xlarge -z us-east-1b
```

If the request was successful, `ec2` will save the spot fleet id in the configuration file.
Moreover, it will not allow you request a new spot fleet while the requested one is active to avoid resource leak.
You can always cancel your spot fleet request (and shut down the corresponding instances) using the following command:

```bash
$ ec2 fleet cancel
```

For other commands, please take a look at the `ec2` command help.

## Contribution

Bug reports (and PRs that fix them!) are very much welcome.

If you think a nice feature is missing, you can request it by opening an issue and providing a clear use case.
This CLI is intentionally kept clean and minimalistic, so we are reluctant to integrate features that will never be used.

## License

MIT
