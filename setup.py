#!/usr/bin/env python

from setuptools import setup

setup(name='smit.backuppsqls3',
      version='0.0.1dev',
      description='Tool backupping and restoring psql to s3',
      author='Peter Smit',
      author_email='peter@smitmail.eu',
      packages=['smit'],
      package_dir={'': 'src'},
      install_requires=[],
      entry_points = dict(console_scripts=[
        'bckp = smit.backuppsqls3.bckp:run',
        ])
      )
