smit.backuppsqls3
=================

backuppsqls3 is a set of tools for backing up a PostgreSQL database to Amazon S3. It is primarily meant for using a
"[Continuous Archiving and Point-In-Time Recovery](http://www.postgresql.org/docs/9.0/interactive/continuous-archiving.html)"
strategy, but also just pg_dumps can be used.

All tools are described below. A sample configuration file can be found in config/backuppsqls3.conf.sample, but also all
 options can be given on the command line.


pg_backup_s3
------------
This tool can create two backups. The first one is a pg_dump, the second a copy of the data directory as is needed for a
"[Continuous Archiving and Point-In-Time Recovery](http://www.postgresql.org/docs/9.0/interactive/continuous-archiving.html)"
backup. Command line switches indicate which of the two are done.

In case the data directory copy is done, a check in the PostgreSQL configuration is done to check that the wal archive tool
is configured correctly. If not, changes are suggested. Normally in this scenario the pg_backup_wal_s3 tool is used as
archiver. Also pg_start_backup and pg_stop_backup are done. A lockfile will be used to prevent two backups happening at
the same time.

pg_restore_s3
-------------
**Warning** This tool destroys the complete current database

A dump or data dir backup are fetched from Amazon S3 and the database is restored. For CA-PIT-R the WAL's are replayed.
The database is left in a state that it is only possible for the postgres user to connect. To restore access, the
pg_hba.conf.orig should be moved back to pg_hba.conf

pg_backup_wal_s3
----------------
This tool should be called by PostgreSQL to archive a WAL file to S3

pg_backup_wal_s3
----------------
This tool should be called by PostgreSQL to retrieve a WAL file from S3
