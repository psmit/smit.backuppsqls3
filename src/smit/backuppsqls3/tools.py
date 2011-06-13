from optparse import OptionParser
from ConfigParser import SafeConfigParser

from os.path import expanduser

from boto import connect_s3

def backup_wal():
    usage = "usage: %prog [options] source_file file_name"
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

    source_file,file_name = args

    config = {'bucket': '', 'prefix': '', 'access_key': '', 'secret_key': ''}

    #if options.has_key('config'):
    conf_parse = SafeConfigParser(config)
    conf_parse.read(['/etc/backuppsqls3.conf',expanduser('~/.backuppsqls3.conf'),options.config])
    
    if conf_parse.has_section('s3credentials'):
        for opt in config.keys():
            if conf_parse.has_option('s3credentials',opt):
                config[opt] = conf_parse.get('s3credentials',opt)

            if getattr(options, opt) is not None:
                config[opt] = getattr(options, opt)

    conn = connect_s3(config['access_key'], config['secret_key'])
    bucket = conn.get_bucket(config['bucket'])
    key = bucket.new_key(config['prefix']+file_name)
    key.set_contents_from_filename(source_file)


def run():
    pass
