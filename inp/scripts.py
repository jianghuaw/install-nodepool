import argparse
import StringIO
import logging
import yaml

from inp import remote
from inp import data
from inp import bash_env
from inp import templating
from inp.validation import file_access_issues, remote_system_access_issues, get_args_or_die, die_if_issues_found


DEFAULT_NODEPOOL_REPO = 'https://github.com/citrix-openstack/nodepool.git'
DEFAULT_NODEPOOL_BRANCH = '2014-11'
PROJECT_CONFIG_URL = 'https://github.com/citrix-openstack/project-config'
PROJECT_CONFIG_BRANCH = '2014-11'
DEFAULT_OSCI_REPO = 'https://github.com/citrix-openstack/openstack-citrix-ci.git'
DEFAULT_OSCI_BRANCH = '2014-11'
DEFAULT_PORT = 22
DEFAULT_MIN_READY = 8
DEFAULT_KEYPAIR_NAME = 'nodepool'
NODEPOOL_HOME_DIR = '/home/nodepool'


IAD_MAX_DEFAULT = 25
DFW_MAX_DEFAULT = 10
ORD_MAX_DEFAULT = 14


def bashline(some_dict):
    return ' '.join('{key}={value}'.format(key=key, value=value) for
        key, value in some_dict.iteritems())


class OSCIEnv(object):
    def __init__(self, osci_repo, osci_branch, swift_api_key, image_name):
        self.username = 'osci'
        self.home = '/home/osci'
        self.osci_repo = osci_repo
        self.osci_branch = osci_branch
        self.swift_api_key = swift_api_key
        self.image_name = image_name

    @property
    def _env_dict(self):
        return dict(
            OSCI_USER=self.username,
            OSCI_HOME_DIR=self.home,
            OSCI_REPO=self.osci_repo,
            OSCI_BRANCH=self.osci_branch,
            SWIFT_API_KEY=self.swift_api_key,
            NODEPOOL_HOME_DIR=NODEPOOL_HOME_DIR,
            IMAGE_NAME=self.image_name,
        )

    @property
    def bashline(self):
        return bashline(self._env_dict)

    def as_dict(self):
        return self._env_dict


class NodepoolEnv(object):
    def __init__(self):
        self.username = 'nodepool'
        self.home = NODEPOOL_HOME_DIR

    @property
    def _env_dict(self):
        return dict(
            NODEPOOL_USER=self.username,
            NODEPOOL_HOME_DIR=self.home,
        )

    @property
    def bashline(self):
        return bashline(self._env_dict)

    def as_dict(self):
        return self._env_dict


class NodepoolInstallEnv(NodepoolEnv):
    def __init__(self, repo, branch):
        super(NodepoolInstallEnv, self).__init__()
        self.repo = repo
        self.branch = branch

    @property
    def _env_dict(self):
        env = super(NodepoolInstallEnv, self)._env_dict
        return dict(
            env,
            NODEPOOL_REPO=self.repo,
            NODEPOOL_BRANCH=self.branch,
        )


class NodepoolConfigEnv(NodepoolEnv):

    def __init__(self, openrc, image_name, min_ready, rackspace_password, key_name, iad_max=0, ord_max=0, dfw_max=0):
        super(NodepoolConfigEnv, self).__init__()
        self.project_config_url = PROJECT_CONFIG_URL
        self.project_config_branch = PROJECT_CONFIG_BRANCH
        self.openrc = openrc
        self.image_name = image_name
        self.min_ready = str(min_ready)
        self.iad_max = str(iad_max)
        self.ord_max = str(ord_max)
        self.dfw_max = str(dfw_max)
        self.rackspace_password = rackspace_password
        self.key_name = key_name

    @property
    def _env_dict(self):
        env = super(NodepoolConfigEnv, self)._env_dict
        return dict(
            env,
            PROJECT_CONFIG_URL=self.project_config_url,
            PROJECT_CONFIG_BRANCH=self.project_config_branch,
            IMAGE_NAME=self.image_name,
            MIN_READY=self.min_ready,
            RACKSPACE_PASSWORD=self.rackspace_password,
            NODEPOOL_KEYPAIR_NAME=self.key_name,
            IAD_MAX=self.iad_max,
            ORD_MAX=self.ord_max,
            DFW_MAX=self.dfw_max,
            **self.openrc
        )


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
        default=DEFAULT_NODEPOOL_BRANCH,
        help='Nodepool branch (default: %s)' % DEFAULT_NODEPOOL_BRANCH,
    )
    return parser.parse_args()


def issues_for_install_args(args):
    return remote_system_access_issues(args.username, args.host, args.port)


def get_params_or_die(cloud_parameters_file):
    with open(cloud_parameters_file, 'rb') as pfile:
        parameter_lines = pfile.read()
        pfile.close()

    die_if_issues_found(bash_env.bash_env_parsing_issues(parameter_lines))
    return bash_env.bash_to_dict(parameter_lines)


def nodepool_install():
    args = get_args_or_die(parse_install_args, issues_for_install_args)

    env = NodepoolInstallEnv(args.nodepool_repo, args.nodepool_branch)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(data.install_script('installscript.sh'), 'install.sh')
        connection.run('%s bash install.sh' % env.bashline)
        connection.run('rm -f install.sh')


class NovaCommands(object):
    def __init__(self, config_env):
        self.config_env = config_env

    def _nova_cmd(self, region, cmd):
        env = self.config_env

        nova_env = dict(env.openrc, OS_REGION_NAME=region)
        return 'sudo -u {user} /bin/sh -c "HOME={home} {nova_env} /opt/nodepool/env/bin/nova {cmd}"'.format(
            user=env.username,
            nova_env=bashline(nova_env),
            home=env.home,
            cmd=cmd,
            region=region,
        )

    def keypair_show(self, region, name):
        return self._nova_cmd(region, 'keypair-show {name}'.format(name=name))

    def keypair_delete(self, region, name):
        return self._nova_cmd(region, 'keypair-delete {name}'.format(name=name))

    def keypair_add(self, region, name, path):
        return self._nova_cmd(
            region, 'keypair-add --pub-key {path} {name}'.format(
                name=name,
                path=path
            )
        )


def image_provider_regions():
    nodepool_config = yaml.load(data.nodepool_config(dict()))

    used_providers = []
    for label in nodepool_config['labels']:
        for provider in label['providers']:
            used_providers.append(provider['name'])

    regions = []
    for provider in nodepool_config['providers']:
        if provider['name'] in used_providers:
            regions.append(provider['region-name'])

    return regions


def _parse_nodepool_configure_args():
    parser = argparse.ArgumentParser(
        description="Configure Nodepool on a remote machine")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('openrc', help='OpenRc file to access the cloud')
    parser.add_argument('image_name', help='Image name to be used')
    parser.add_argument('nodepool_keyfile', help='SSH key to be used to prepare nodes')
    parser.add_argument('jenkins_keyfile', help='SSH key to be used by jenkins')
    parser.add_argument('rackspace_password', help='Rackspace password')
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    parser.add_argument(
        '--min_ready',
        type=int,
        default=DEFAULT_MIN_READY,
        help='Default number of min ready nodes (default: %s)' % DEFAULT_MIN_READY
    )
    parser.add_argument(
        '--iad_max',
        type=int,
        default=IAD_MAX_DEFAULT,
        help='Maximum number of nodes in IAD (default: %s)' % IAD_MAX_DEFAULT
    )
    parser.add_argument(
        '--dfw_max',
        type=int,
        default=DFW_MAX_DEFAULT,
        help='Maximum number of nodes in DFW (default: %s)' % DFW_MAX_DEFAULT
    )
    parser.add_argument(
        '--ord_max',
        type=int,
        default=ORD_MAX_DEFAULT,
        help='Maximum number of nodes in ORD (default: %s)' % ORD_MAX_DEFAULT
    )
    parser.add_argument(
        '--key_name',
        default=DEFAULT_KEYPAIR_NAME,
        help='Keypair name to use (default: %s)' % DEFAULT_KEYPAIR_NAME
    )
    return parser.parse_args()


def _issues_for_nodepool_configure_args(args):
    return (
        remote_system_access_issues(args.username, args.host, args.port)
        + file_access_issues(args.openrc)
        + file_access_issues(args.nodepool_keyfile)
        + file_access_issues(args.jenkins_keyfile)
    )


def nodepool_configure():
    args = get_args_or_die(
        _parse_nodepool_configure_args,
        _issues_for_nodepool_configure_args
    )

    env = NodepoolConfigEnv(
        get_params_or_die(args.openrc),
        args.image_name,
        args.min_ready,
        args.rackspace_password,
        args.key_name,
        iad_max=args.iad_max,
        ord_max=args.ord_max,
        dfw_max=args.dfw_max
    )
    nodepool_config_file = data.nodepool_config(env.as_dict())

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(
            data.install_script('nodepool_config.sh'),
            'nodepool_config.sh'
        )
        connection.put(
            nodepool_config_file,
            'nodepool.yaml'
        )

        connection.put(
            args.nodepool_keyfile,
            'nodepool.priv'
        )

        connection.put(
            args.jenkins_keyfile,
            'jenkins.priv'
        )

        connection.run('%s bash nodepool_config.sh' % env.bashline)

        connection.run('rm -f nodepool_config.sh')
        connection.run('rm -f nodepool.yaml')
        connection.run('rm -f nodepool.priv')
        connection.run('rm -f jenkins.priv')


def _parse_startstop_args(parser):
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    return parser.parse_args()


def parse_nodepool_start_args():
    parser = argparse.ArgumentParser(description="Start Nodepool")
    return _parse_startstop_args(parser)


def system_access_issues(args):
    issues = remote_system_access_issues(args.username, args.host, args.port)
    return issues


def nodepool_start():
    args = get_args_or_die(
        parse_nodepool_start_args,
        system_access_issues)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.sudo('service nodepool start')


def parse_nodepool_stop_args():
    parser = argparse.ArgumentParser(description="Stop Nodepool")
    return _parse_startstop_args(parser)


def nodepool_stop():
    args = get_args_or_die(
        parse_nodepool_stop_args,
        system_access_issues)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.sudo('service nodepool stop')


def parse_osci_install_args():
    parser = argparse.ArgumentParser(description="Install OSCI")
    parser.add_argument('gerrit_key', help='Private key file to be used'
                        ' with gerrit')
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('swift_api_key', help='Swift API key')
    parser.add_argument('image_name', help='Image to be used')
    parser.add_argument(
        '--osci_repo',
        default=DEFAULT_OSCI_REPO,
        help='OSCI repository (default: %s)' % DEFAULT_OSCI_REPO
    )
    parser.add_argument(
        '--osci_branch',
        default=DEFAULT_OSCI_BRANCH,
        help='OSCI branch (default: %s)' % DEFAULT_OSCI_BRANCH
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    return parser.parse_args()


def issues_for_osci_install_args(args):
    issues = (
        file_access_issues(args.gerrit_key)
        + remote_system_access_issues(args.username, args.host, args.port)
    )

    return issues


def osci_install():
    args = get_args_or_die(
        parse_osci_install_args,
        issues_for_osci_install_args)

    env = OSCIEnv(
        args.osci_repo, args.osci_branch, args.swift_api_key, args.image_name)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(args.gerrit_key, 'gerrit.key')
        connection.put(
            data.install_script('osci_installscript.sh'),
            'osci_installscript.sh'
        )
        connection.run(
            '%s bash osci_installscript.sh' % env.bashline
        )
        connection.run(
            'rm -f gerrit.key osci_installscript.sh')


def parse_osci_release_args():
    parser = argparse.ArgumentParser(description="Release OSCI")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument(
        '--osci_repo',
        default=DEFAULT_OSCI_REPO,
        help='OSCI repository (default: %s)' % DEFAULT_OSCI_REPO
    )
    parser.add_argument(
        '--osci_branch',
        default=DEFAULT_OSCI_BRANCH,
        help='OSCI branch (default: %s)' % DEFAULT_OSCI_BRANCH
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    return parser.parse_args()


def issues_for_osci_release_args(args):
    return remote_system_access_issues(args.username, args.host, args.port)


def osci_release():
    args = get_args_or_die(
        parse_osci_release_args,
        issues_for_osci_release_args)

    env = OSCIEnv(
        args.osci_repo, args.osci_branch, 'IRRELEVANT', 'IRRELEVANT')

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(
            data.install_script('osci_release.sh'),
            'osci_release.sh'
        )
        connection.run(
            '%s bash osci_release.sh' % env.bashline
        )
        connection.run(
            'rm -f gerrit.key osci_release.sh')


def parse_osci_start_args():
    parser = argparse.ArgumentParser(description="Start OSCI")
    return _parse_startstop_args(parser)


def osci_start():
    args = get_args_or_die(parse_osci_start_args, system_access_issues)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.sudo('service citrix-ci start')
        connection.sudo('service citrix-ci-gerritwatch start')


def parse_osci_stop_args():
    parser = argparse.ArgumentParser(description="Stop OSCI")
    return _parse_startstop_args(parser)


def osci_stop():
    args = get_args_or_die(parse_osci_stop_args, system_access_issues)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.sudo('service citrix-ci stop')
        connection.sudo('service citrix-ci-gerritwatch stop')


def _parse_nodepool_upload_keys_args():
    parser = argparse.ArgumentParser(
        description="Upload a key to the cloud")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('openrc', help='OpenRc file to access the cloud')
    parser.add_argument(
        '--remove',
        action="store_true",
        default=False,
        help='OpenRc file to access the cloud'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    parser.add_argument(
        '--key_name',
        default=DEFAULT_KEYPAIR_NAME,
        help='Keypair name to use (default: %s)' % DEFAULT_KEYPAIR_NAME
    )
    return parser.parse_args()


def _issues_for_nodepool_upload_keys_args(args):
    return (
        remote_system_access_issues(args.username, args.host, args.port)
        + file_access_issues(args.openrc)
    )


def nodepool_upload_keys():
    args = get_args_or_die(
        _parse_nodepool_upload_keys_args,
        _issues_for_nodepool_upload_keys_args
    )

    env = NodepoolConfigEnv(
        get_params_or_die(args.openrc),
        'ignored',
        'ignored',
        'ignored',
        args.key_name,
    )
    nodepool_config_file = data.nodepool_config(env.as_dict())
    nova_commands = NovaCommands(env)

    regions = image_provider_regions()

    with remote.connect(args.username, args.host, args.port) as connection:
        key_exists_in_regions = []
        for region in regions:
            result = connection.run(
                nova_commands.keypair_show(region, env.key_name),
                ignore_failures=True,
            )
            if result.succeeded:
                key_exists_in_regions.append(region)

        if key_exists_in_regions and not args.remove:
            raise SystemExit(
                'Keypair "{keypair}" already exists at regions: {regions}'
                ' Please remove them manually or use --remove'.format(
                    keypair=env.key_name,
                    regions=','.join(key_exists_in_regions)
                )
            )

        if args.remove:
            for region in key_exists_in_regions:
                connection.run(
                    nova_commands.keypair_delete(region, env.key_name)
                )

        for region in regions:
            result = connection.run(
                nova_commands.keypair_add(
                    region,
                    env.key_name,
                    '{home}/.ssh/id_rsa.pub'.format(home=env.home))
            )


def parse_update_args():
    parser = argparse.ArgumentParser(description="Update Nodepool")
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
        default=DEFAULT_NODEPOOL_BRANCH,
        help='Nodepool branch (default: %s)' % DEFAULT_NODEPOOL_BRANCH,
    )
    return parser.parse_args()


def issues_for_update_args(args):
    return remote_system_access_issues(args.username, args.host, args.port)


def nodepool_update():
    args = get_args_or_die(parse_update_args, issues_for_update_args)

    env = NodepoolInstallEnv(args.nodepool_repo, args.nodepool_branch)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(data.install_script('update.sh'), 'update.sh')
        connection.run('%s bash update.sh' % env.bashline)
        connection.run('rm -f update.sh')


def parse_backup_args():
    parser = argparse.ArgumentParser(description="Backup osci and nodepool")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('output', help='Output file on local system')
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    return parser.parse_args()


def issues_for_backup_args(args):
    return remote_system_access_issues(args.username, args.host, args.port)


def backup():
    args = get_args_or_die(parse_backup_args, issues_for_backup_args)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(data.install_script('backup.sh'), 'backup.sh')
        connection.run('bash backup.sh')
        connection.get('osci-backup.tgz', args.output)
        connection.run('rm -f backup.sh osci-backup.tgz')


def parse_restore_args():
    parser = argparse.ArgumentParser(description="Restore osci and nodepool")
    parser.add_argument('username', help='Username to target host')
    parser.add_argument('host', help='Target host')
    parser.add_argument('dump_file', help='Dump file on local system')
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help='SSH port to use (default: %s)' % DEFAULT_PORT
    )
    return parser.parse_args()


def issues_for_restore_args(args):
    return (
        remote_system_access_issues(args.username, args.host, args.port)
        + file_access_issues(args.dump_file)
    )


def restore():
    args = get_args_or_die(parse_restore_args, issues_for_restore_args)

    with remote.connect(args.username, args.host, args.port) as connection:
        connection.put(data.install_script('restore.sh'), 'restore.sh')
        connection.put(args.dump_file, 'osci-backup.tgz')
        connection.run('bash restore.sh')
        connection.run('rm -f restore.sh osci-backup.tgz')
