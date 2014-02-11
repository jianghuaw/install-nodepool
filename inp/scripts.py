import argparse
import StringIO

from inp import remote
from inp import data
from inp import bash_env
from inp import templating
from inp.validation import file_access_issues, remote_system_access_issues, get_args_or_die, die_if_issues_found


def parse_install_args():
    parser = argparse.ArgumentParser(description="Install Nodepool")
    parser.add_argument('private_key', help='Private key file')
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('rsparams', help='Rackspace settings file')
    parser.add_argument('rspass', help='Rackspace password')
    return parser.parse_args()


def issues_for_install_args(args):
    issues = (
        file_access_issues(args.private_key)
        + file_access_issues(args.rsparams)
        + file_access_issues(pubkey_for(args.private_key))
        + remote_system_access_issues(args.username, args.host)
    )

    return issues


def pubkey_for(privkey):
    return privkey + '.pub'


def get_params_or_die(cloud_parameters_file):
    with open(cloud_parameters_file, 'rb') as pfile:
        parameter_lines = pfile.read()
        pfile.close()

    die_if_issues_found(bash_env.bash_env_parsing_issues(parameter_lines))
    return bash_env.bash_to_dict(parameter_lines)


def install():
    args = get_args_or_die(parse_install_args, issues_for_install_args)
    cloud_env = get_params_or_die(args.rsparams)
    cloud_env['RACKSPACE_PASSWORD'] = args.rspass
    nodepool_config_file = data.nodepool_config(cloud_env)

    with remote.connect(args.username, args.host) as connection:
        connection.run('rm -f .bash_profile')
        connection.run('rm -f .ssh/nodepool')
        connection.run('rm -f .ssh/nodepool.pub')
        connection.run('rm -f install.sh')
        connection.run('rm -f nodepool.yaml')
        connection.put(nodepool_config_file, 'nodepool.yaml')
        connection.put(args.rsparams, '.bash_profile')
        connection.put(args.private_key, '.ssh/nodepool')
        connection.put(pubkey_for(args.private_key), '.ssh/nodepool.pub')
        connection.run('chmod 0400 .ssh/nodepool')
        connection.put(data.install_script(), 'install.sh')
        connection.run('bash install.sh "%s"' % (args.rspass, ))
