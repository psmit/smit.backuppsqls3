#!/usr/bin/env python

from setuptools import setup
import sys

sys.path = ['./src'] + sys.path

from smit.backuppsqls3 import __version__

setup(name='smit.backuppsqls3',
      version=__version__,
      description='Tool backupping and restoring psql to s3',
      author='Peter Smit',
      author_email='peter@smitmail.eu',
      packages=['smit','smit.backuppsqls3'],
      package_dir={'': 'src'},
      install_requires=['boto'],
      data_files=[('config', ['config/backuppsqls3.conf.sample'])],
      entry_points = dict(console_scripts=[
        'pg_backup_s3 = smit.backuppsqls3.tools:run',
        'pg_backup_wal_s3 = smit.backuppsqls3.tools:backup_wal',
        'pg_restore_s3 = smit.backuppsqls3.tools:run',
        'pg_restore_wal_s3 = smit.backuppsqls3.tools:run'
        ])
      )
