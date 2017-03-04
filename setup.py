import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='ec2',
    version='0.2.0',
    packages=find_packages(),
    description='A minimalistic CLI for managing AWS EC2 projects.',
    long_description=read('README.md'),
    author='Maruan Al-Shedivat',
    author_email='maruan@alshedivat.com',
    url='https://github.com/alshedivat/ec2',
    license='MIT',
    install_requires=['argparse', 'boto3', 'configparser', 'fabric', 'six'],
    entry_points = {
        'console_scripts': [
            'ec2 = ec2:run',
        ],
    }
)
