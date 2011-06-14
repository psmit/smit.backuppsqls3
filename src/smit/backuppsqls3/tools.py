import tarfile
from gzip import GzipFile
from subprocess import  call
from boto import connect_s3
from ConfigParser import SafeConfigParser, RawConfigParser
from datetime import datetime
from optparse import OptionParser
import os
from os.path import expanduser
from os import unlink, fdopen
from psycopg2 import connect
from sys import stderr
from tempfile import mkstemp
from zc.lockfile import LockFile


def add_s3_options_to_parser(parser):
    parser.add_option("-b", "--bucket", dest="bucket", help="S3 Bucket")
    parser.add_option("-p", "--prefix", dest="prefix", help="Backup prefix (e.g. backup/dbname/)")
    parser.add_option("-a", "--access-key", dest='access_key', help="AWS access key")
    parser.add_option("-s", "--secret-key", dest='secret_key', help="NOT RECOMMENDED, use config files to set credentials. AWS secret key")


def update_config_for_s3(config,options,tool):
    keys = ['bucket', 'prefix', 'access_key', 'secret_key']
    for k in keys:
        if k not in config:
            config[k] = ''

    conf_parse = SafeConfigParser(config)
    conf_parse.read(['/etc/backuppsqls3.conf',expanduser('~/.backuppsqls3.conf'),options.config])

    for section in ["general", tool]:
        if conf_parse.has_section(section):
            for opt in config.keys():
                if conf_parse.has_option(section,opt):
                    config[opt] = conf_parse.get(section,opt)

                if getattr(options, opt) is not None:
                    config[opt] = getattr(options, opt)


def get_wal_config(tool,usage):

    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config", default="", help="Configuration file")
    add_s3_options_to_parser(parser)
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.print_usage()
        exit(1)

    config = {}
    update_config_for_s3(config,options,tool)
    return config, args


def backup_wal():
    config, args = get_wal_config("backup_wal", "usage: %prog [options] source_file file_name")
    source_file,file_name = args

    fi,t_file_name = mkstemp()
    fp = fdopen(fi,'w')
    gzf = GzipFile(fileobj=fp)
    gzf.writelines(open(source_file))
    gzf.close()
    fp.close()


    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])
    key = bucket.new_key(config['prefix']+file_name+".gz")
    key.set_contents_from_filename(t_file_name)

    unlink(t_file_name)

def restore_wal():
    config, args = get_wal_config("restore_wal", "usage: %prog [options] source_file target_path")
    source_file,target_path = args

    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])

    key = bucket.get_key(config['prefix']+source_file+".gz")
    if key is not None:
        fi,t_file_name = mkstemp()
        os.close(fi)
        key.get_contents_to_filename(t_file_name)
        gzf = GzipFile(t_file_name,'r')
        a = open(target_path,'w')
        a.write(gzf.read())
        a.close()
        gzf.close()
        unlink(t_file_name)
    else:
        print >> stderr, "File not found"
        exit(1)

def backup():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config", default="", help="Configuration file")
    add_s3_options_to_parser(parser)
    parser.add_option("-l", "--lock-file", dest='lock_file', default='/tmp/backuppsqls3.lock')
    parser.add_option("--dump", dest="do_dump", default=False, action="store_true", help="Perform dump")
#    parser.add_option("--dump-databases", dest="databases", default="ALL", help="Which databases to backup when a dump is done")
    parser.add_option("--base-backup", dest="do_base_backup", default=False, action="store_true", help="Perform base backup for PITR and check configuration")
    parser.add_option("--postgresql-conf", dest="postgresql_conf", help="PostgreSQL configuration file (used for base backup)")
    parser.add_option("--postgresql-user", dest="postgresql_user", help="PostgreSQL super user (default: current system user)")
    parser.add_option("--postgresql-password", dest="postgresql_password", help="Password for PostgreSQL user (default, use system ident)")

    (options, args) = parser.parse_args()
    config = {}

    update_config_for_s3(config,options,"backup")

    sec, postgres_conf = _read_postgres_config(options.postgresql_conf)
    test_archive_config(sec,postgres_conf,postgres_conf)


    config['lock_file'] = options.lock_file
    config['data_dir'] = postgres_conf.get(sec,'data_directory').replace('\'','').split('#')[0].strip()

    if options.do_base_backup:
        _do_base_backup(config)
    if options.do_dump:
        _do_dump_backup(config)


def _read_postgres_config(config_file):
    fi, file_name = mkstemp()
    fp = fdopen(fi, 'w')
    sec = "sectionhead"
    print >> fp, "["+sec+"]"
    for line in open(config_file):
        print >> fp, line.strip()
    fp.close()
    s = RawConfigParser()
    s.read(file_name)
    unlink(file_name)
    return sec, s

def test_archive_config(sec,s,config_file):
    if not (s.has_option(sec,"archive_mode") and s.get(sec,"archive_mode").startswith('on') and s.has_option(sec, 'archive_command') and 'pg_backup_wal_s3' in s.get(sec, 'archive_command')):
        print "Please enable archiving in %s" % config_file
        print "Suggested entries:"
        print "  wal_level = archive"
        print "  archive_mode = on"
        print "  archive_command = 'pg_backup_wal_s3 %p %f'"
        exit(1)
    return True


def _do_base_backup(config):
    lock = LockFile(config['lock_file'])
    conn = connect("")
    cur = conn.cursor()
    label = datetime.now().strftime("%Y%m%d%H%M%S")
    cur.execute("SELECT pg_start_backup('%s');" % label)

    fi,file_name = mkstemp()
    fp = fdopen(fi,'w')
    tar_f = tarfile.open(fileobj=fp,mode='w:gz')
    tar_f.add(config['data_dir'],arcname="",exclude=lambda x: '/pg_xlog' in x)
    tar_f.close()
    fp.close()


    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])
    key = bucket.new_key(config['prefix']+"base_"+label+".tar.gz")
    key.set_contents_from_filename(file_name)

    unlink(file_name)
    cur.execute("SELECT pg_stop_backup();")
    lock.close()

def _do_dump_backup(config):
    label = datetime.now().strftime("%Y%m%d%H%M%S")

    fi,file_name = mkstemp()
    fp = fdopen(fi,'w')

    if call(["pg_dumpall"], stdout=fp) is not 0:
        print >> stderr, "Dump failed"
        exit(1)
    fp.close()


    fi2,file_name2 = mkstemp()

    f_in = open(file_name, 'rb')
    f_out = GzipFile(file_name2, 'wb')
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()

    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])
    key = bucket.new_key(config['prefix']+"dump_"+label+".gz")
    key.set_contents_from_filename(file_name2)

    unlink(file_name)
    unlink(file_name2)

def run():
    pass
