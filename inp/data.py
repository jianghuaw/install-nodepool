import os
import inp
import StringIO

from inp import templating

def get_path_for(fname):
    path = os.path.dirname(os.path.abspath(inp.__file__))
    return os.path.join(path, fname)


def get_filelike(fname):
    with open(get_path_for(fname), 'rb') as f:
        filelike = StringIO.StringIO(f.read())
        filelike.name = 'install_script'
        return filelike


def install_script():
    return get_filelike('installscript.sh')


def nodepool_config(cloud_env):
    nodepool_config_template = get_filelike('nodepool.yaml').read()
    nodepool_config = templating.bash_style_replace(cloud_env, nodepool_config_template)
    nodepool_config_file = StringIO.StringIO(nodepool_config)
    nodepool_config_file.name = 'nodepool.yaml'
    return nodepool_config_file
