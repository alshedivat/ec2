import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='ec2',
    version='0.1',
    packages=find_packages(),
    description='A minimalistic CLI for AWS EC2 on a budget.',
    long_description=read('README.md'),
    author='Maruan Al-Shedivat',
    author_email='maruan@alshedivat.com',
    url='https://github.com/alshedivat/aws-ec2-on-a-budget',
    license='MIT',
    install_requires=['argparse','boto3','configparser','six'],
    entry_points = {
        'console_scripts': [
            'ec2 = ec2.cli:run',
        ],
    }
)
