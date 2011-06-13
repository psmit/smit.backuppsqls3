from boto import connect_s3
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from os.path import expanduser
from sys import stderr

def get_wal_config(tool,usage):

    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config", default="", help="Configuration file")
    parser.add_option("-b", "--bucket", dest="bucket", help="S3 Bucket")
    parser.add_option("-p", "--prefix", dest="prefix", help="Backup prefix (e.g. backup/dbname/)")
    parser.add_option("-a", "--access-key", dest='access_key', help="AWS access key")
    parser.add_option("-s", "--secret-key", dest='secret_key', help="NOT RECOMMENDED, use config files to set credentials. AWS secret key")

    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.print_usage()
        exit(1)

    config = {'bucket': '', 'prefix': '', 'access_key': '', 'secret_key': ''}

    conf_parse = SafeConfigParser(config)
    conf_parse.read(['/etc/backuppsqls3.conf',expanduser('~/.backuppsqls3.conf'),options.config])

    for section in ["general", tool]:
        if conf_parse.has_section(section):
            for opt in config.keys():
                if conf_parse.has_option(section,opt):
                    config[opt] = conf_parse.get(section,opt)

                if getattr(options, opt) is not None:
                    config[opt] = getattr(options, opt)

    return config, args


def backup_wal():
    config, args = get_wal_config("backup_wal", "usage: %prog [options] source_file file_name")
    source_file,file_name = args

    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])
    key = bucket.new_key(config['prefix']+file_name)
    key.set_contents_from_filename(source_file)

def restore_wal():
    config, args = get_wal_config("restore_wal", "usage: %prog [options] source_file target_path")
    source_file,target_path = args

    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])

    key = bucket.get_key(config['prefix']+source_file)
    if key is not None:
        key.get_contents_to_filename(target_path)
    else:
        print >> stderr, "File not found"
        exit(1)

def run():
    pass
