import contextlib

from fabric import api as fabric_api
from fabric import operations
from fabric import network as fabric_network


def fabric_settings(username, host, port, ignore_failures=False):
    warn_only = ignore_failures
    return fabric_api.settings(
        host_string=host,
        abort_on_prompts=True,
        port=port,
        user=username,
        warn_only=warn_only)

def check_connection(username, host, port):
    with fabric_settings(username, host, port):
        result = fabric_api.run('true')
        return result.return_code == 0


def check_sudo(username, host, port):
    with fabric_settings(username, host, port):
        result = fabric_api.sudo('true')
        return result.return_code == 0


class Connection(object):
    def __init__(self, username, host, port):
        self.username = username
        self.host = host
        self.port = port

    def put(self, local_fname, remote_fname):
        with self.settings(False):
            operations.put(local_path=local_fname, remote_path=remote_fname)

    def disconnect(self):
        fabric_network.disconnect_all()

    def settings(self, ignore_failures):
        return fabric_settings(
            self.username, self.host, self.port, ignore_failures)

    def run(self, command, ignore_failures=False):
        with self.settings(ignore_failures):
            return fabric_api.run(command)

    def sudo(self, command):
        with self.settings(False):
            return fabric_api.sudo(command)


@contextlib.contextmanager
def connect(username, host, port):
    connection = Connection(username, host, port)
    yield connection
    connection.disconnect()
