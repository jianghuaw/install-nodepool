import contextlib

from fabric import api as fabric_api
from fabric import operations
from fabric import network as fabric_network


def fabric_settings(username, host):
    return fabric_api.settings(
        host_string=host,
        abort_on_prompts=True,
        user=username)

def check_connection(username, host):
    with fabric_settings(username, host):
        result = fabric_api.run('true')
        return result.return_code == 0


def check_sudo(username, host):
    with fabric_settings(username, host):
        result = fabric_api.sudo('true')
        return result.return_code == 0


class Connection(object):
    def __init__(self, username, host):
        self.username = username
        self.host = host

    def put(self, local_fname, remote_fname):
        with self.settings():
            operations.put(local_path=local_fname, remote_path=remote_fname)

    def disconnect(self):
        fabric_network.disconnect_all()

    def settings(self):
        return fabric_settings(self.username, self.host)

    def run(self, command):
        with self.settings():
            fabric_api.run(command)


@contextlib.contextmanager
def connect(username, host):
    connection = Connection(username, host)
    yield connection
    connection.disconnect()
