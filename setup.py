#!/usr/bin/python

from setuptools import setup, find_packages
from version import get_version

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='panopto-python-soap',
    version=get_version('short'),
    author='Chris Phillips',
    author_email='Chris.M.Phillips@Sprint.com',
    description=('Panopto to Watershed data migration and sFTP transfer adapted from Mark Brewsters soap API from Panopto'),
    long_description=readme(),
    keywords=['python', 'panopto', 'lambda', 'api', 'soap', 'watershed', 'cron', 'sftp'],
    install_requires=[
        'regex',
        'urllib3',
        'zeep',
        'python-dotenv',
        'pytz',
        'paramiko',
        'pycron'
    ],
    package_dir={'': 'src'},
    packages=find_packages('src')
)