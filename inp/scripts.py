import argparse
import StringIO
import logging

from inp import remote
from inp import data
from inp import bash_env
from inp import templating
from inp.validation import file_access_issues, remote_system_access_issues, get_args_or_die, die_if_issues_found


DEFAULT_NODEPOOL_REPO = 'https://github.com/citrix-openstack/nodepool.git'
DEFAULT_NODEPOOL_BRANCH = 'master'
DEFAULT_PORT = 22


def parse_install_args():
    parser = argparse.ArgumentParser(description="Install Nodepool")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    parser.add_argument(
        '--nodepool_repo',
        default=DEFAULT_NODEPOOL_REPO,
        help='Nodepool repository (default: %s)' % DEFAULT_NODEPOOL_REPO,
    )
    parser.add_argument(
        '--nodepool_branch',
        default='master',
        help='Nodepool branch (default: %s)' % DEFAULT_NODEPOOL_BRANCH,
    )
    return parser.parse_args()


def issues_for_install_args(args):
    return remote_system_access_issues(args.username, args.host, args.port)


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

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.run('rm -f install.sh')
        connection.put(data.install_script('installscript.sh'), 'install.sh')
        connection.run('bash install.sh "%s" "%s"' %
                       (args.nodepool_repo, args.nodepool_branch))


def parse_start_args():
    parser = argparse.ArgumentParser(description="Start Nodepool")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    return parser.parse_args()


def issues_for_start_args(args):
    issues = remote_system_access_issues(args.username, args.host, args.port)
    return issues


def start():
    args = get_args_or_die(parse_start_args, issues_for_start_args)

    with remote.connect(args.username, args.host) as connection:
        connection.sudo('service nodepool start')


def parse_osci_install_args():
    parser = argparse.ArgumentParser(description="Install OSCI")
    parser.add_argument('private_key', help='Private key file')
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('params', help='OSCI settings file')
    parser.add_argument('--image_name', default='xsdsvm', help='Image name to use')
    parser.add_argument('--osci_repo',
                        default='https://github.com/citrix-openstack/openstack-citrix-ci.git',
                        help='OSCI repository')
    parser.add_argument('--osci_branch',
                        default='master',
                        help='Nodepool branch')
    return parser.parse_args()


def issues_for_osci_install_args(args):
    issues = (
        file_access_issues(args.private_key)
        + file_access_issues(pubkey_for(args.private_key))
        + remote_system_access_issues(args.username, args.host, args.port)
    )

    return issues


def osci_install():
    args = get_args_or_die(parse_osci_install_args, issues_for_osci_install_args)

    with remote.connect(args.username, args.host) as connection:
        connection.put(args.private_key, '.ssh/citrix_gerrit')
        connection.put(pubkey_for(args.private_key), '.ssh/citrix_gerrit.pub')
        connection.run('chmod 0400 .ssh/citrix_gerrit')
        connection.put(args.params, 'osci.config')
        connection.put(data.install_script('osci_installscript.sh'), 'osci_installscript.sh')
        connection.run('bash osci_installscript.sh "%s" "%s"' %
                       (args.osci_repo, args.osci_branch))


def parse_osci_start_args():
    parser = argparse.ArgumentParser(description="Start OSCI")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    return parser.parse_args()


def issues_for_osci_start_args(args):
    issues = remote_system_access_issues(args.username, args.host, args.port)
    return issues


def osci_start():
    args = get_args_or_die(parse_osci_start_args, issues_for_osci_start_args)

    with remote.connect(args.username, args.host) as connection:
        connection.sudo('service citrix-ci start')
        connection.sudo('service citrix-ci-gerritwatch start')

