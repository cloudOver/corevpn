from distutils.core import setup
from setuptools import find_packages
from distutils.command.install import install as _install

setup(
  name = 'corevpn',
  packages = find_packages(exclude=['config']),
  version = '16.09.01',
  description = 'CloudOver VPN service',
  author = 'Marta Nabozny',
  author_email = 'marta.nabozny@cloudover.io',
  url = 'http://cloudover.org/corecluster/',
  download_url = 'https://github.com/cloudOver/CoreVpn/archive/master.zip',
  keywords = ['corecluster', 'cloudover', 'cloud', 'vpn'],
  classifiers = [],
  install_requires = ['corevpn'],
)
