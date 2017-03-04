A minimalistic CLI for managing AWS EC2 projects
================================================

This is an AWS EC2 CLI build upon [AWS Python SDK](https://boto3.readthedocs.io/en/latest/).
It was designed to support the standard workflow of a small compute-oriented (e.g., machine learning) projects.
The number of available commands is intentionally kept as succinct as possible.

## Features
- Commands for working with spot fleets (view pricing, request and release resources).
- Commands for working with the elastic file system (EFS) that can be shared across compute instances.
- Support for multiple projects (each project gets a separate config file).

## Why?
AWS EC2 has the [native CLI](https://aws.amazon.com/cli/), but it is extremely cumbersome to use for a number of reasons:

- The native AWS CLI supports the entire spectrum of AWS services and is enormous in the number of possible calls and arguments.
Most of the native API is useless for the workflow of a small project.
- The return format of the native CLI is not very human-friendly.
- You end up writing wrappers around the native CLI for each of your new projects or give up and use the web-interface (and sometimes forget to release the resources you requested and pay extra for no value).

## Installation
**Dependencies:**

- [boto3](https://boto3.readthedocs.io/en/latest/)
- [fabric](http://www.fabfile.org/)
- [six](https://pythonhosted.org/six/)
- [pyyaml](http://pyyaml.org/)

Clone the repository and install the `ec2` package as using pip as follows (use `sudo` if necessary):

```bash
$ git clone https://github.com/alshedivat/ec2.git && cd ec2
$ pip install -e .
```

The dependencies will be pulled and installed automatically.
After the installation, you will get access to the `ec2` command in your terminal.

## Usage
We assume that you have worked with AWS EC2 instances and have already set up a few necessary things, such as the SSH key.
If you have no previous experience with AWS, we recommend you go through to the [EC2 getting started guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html) and play with the [AWS web interface](https://aws.amazon.com/console/).
Also, make sure you have [installed](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) the AWS CLI.

### Initialization
Initialize a new ec2 project:

```bash
$ cd /path/to/your/project/directory
$ ec2 configure
```

This will create `.ec2.yaml` configuration file in your project directory of the following structure:

```
AWS:
  iam_fleet_role_arn: arn:aws:iam::XXXXXXXXXXXX:role/aws-ec2-spot-fleet-role
  key_name: default
  region: us-east-1
EC2:
  spot_fleet: null
EFS: null
```

### Working with spot fleets
Suppose, we would like to request a spot fleet of `p2.xlarge` instances.
You can decide in which zone to request the fleet by requesting the latest 3 prices for the spot instances in each zone:

```bash
$ ec2 fleet price -t p2.xlarge -n 3
```

which returns the output of the following form:

```
Last 3 prices for p2.xlarge instances:

--- us-east-1a -----------------------------------
2017-03-04 20:22:34+00:00 UTC   -   0.118700
2017-03-04 20:26:04+00:00 UTC   -   0.118500
2017-03-04 20:27:29+00:00 UTC   -   0.118600

--- us-east-1c -----------------------------------
2017-03-04 20:17:40+00:00 UTC   -   0.112600
2017-03-04 20:19:00+00:00 UTC   -   0.112200
2017-03-04 20:19:46+00:00 UTC   -   0.112300

--- us-east-1d -----------------------------------
2017-03-04 20:05:48+00:00 UTC   -   0.114000
2017-03-04 20:06:00+00:00 UTC   -   0.113500
2017-03-04 20:24:40+00:00 UTC   -   0.113600

--- us-east-1e -----------------------------------
2017-03-04 19:39:34+00:00 UTC   -   0.184200
2017-03-04 20:03:42+00:00 UTC   -   0.182800
2017-03-04 20:04:24+00:00 UTC   -   0.184200
```

Now, let's request a fleet of 2 instances in the `us-east-1c` zone for 3 days:

```bash
$ ec2 fleet request -ami IMAGE_ID -n 2 -d 3 -t p2.xlarge -z us-east-1c
```

If the request was successful, `ec2` will save the spot fleet id in the configuration file.
Moreover, to avoid resource leak, it will not allow you request a new spot fleet for this project while the requested one is still active.
You can always cancel your spot fleet request (and shut down the corresponding instances) using the following command:

```bash
$ ec2 fleet cancel
```

For other commands, please take a look at the `ec2` command help.

## Contribution

Bug reports (and PRs that fix them!) are very much welcome.

If you think a nice feature is missing, you can request it by opening an issue and providing a clear use-case.

## License

MIT
