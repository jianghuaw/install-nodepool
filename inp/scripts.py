import argparse
import os
import sys
from inp import remote
from inp import data


def parse_install_args():
    parser = argparse.ArgumentParser(description="Install Nodepool")
    parser.add_argument('private_key', help='Private key file')
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('rsparams', help='Rackspace settings file')
    parser.add_argument('rspass', help='Rackspace password')
    return parser.parse_args()


def message_for_first_issue(checks):
    for check, msg in checks:
        if check() is False:
            return [msg]
    return []


def file_access_issues(fpath):
    checks = [
        (lambda: os.path.exists(fpath), 'File %s does not exist' % fpath),
        (lambda: os.path.isfile(fpath), 'File %s is not a file' % fpath),
    ]
    return message_for_first_issue(checks)


def remote_system_access_issues(username, host):
    checks = [
        (lambda: remote.check_connection(username, host),
            'Cannot connect to %s using %s' % (username, host)),
        (lambda: remote.check_sudo(username, host),
            'Cannot sudo on %s as %s' % (username, host))
    ]
    return message_for_first_issue(checks)


def issues_for_install_args(args):
    issues = (
        file_access_issues(args.private_key)
        + file_access_issues(args.rsparams)
        + file_access_issues(pubkey_for(args.private_key))
        + remote_system_access_issues(args.username, args.host)
    )

    return issues


def get_args_or_die(arg_parser, arg_validator):
    args = arg_parser()
    issues = arg_validator(args)
    if issues:
        for issue in issues:
            sys.stderr.write('ERROR: ' + issue + '\n')
        sys.exit(1)
    return args


def pubkey_for(privkey):
    return privkey + '.pub'


def install():
    args = get_args_or_die(parse_install_args, issues_for_install_args)
    with remote.connect(args.username, args.host) as connection:
        connection.run('rm -f .bash_profile')
        connection.run('rm -f .ssh/nodepool')
        connection.run('rm -f .ssh/nodepool.pub')
        connection.run('rm -f install.sh')
        connection.put(args.rsparams, '.bash_profile')
        connection.put(args.private_key, '.ssh/nodepool')
        connection.put(pubkey_for(args.private_key), '.ssh/nodepool.pub')
        connection.run('chmod 0400 .ssh/nodepool')
        connection.put(data.install_script(), 'install.sh')
        connection.run('bash install.sh "%s"' % (args.rspass, ))
