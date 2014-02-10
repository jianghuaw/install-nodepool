import os
import inp
import StringIO


def install_script():
    path = os.path.dirname(os.path.abspath(inp.__file__))
    install_script_path = os.path.join(path, 'installscript.sh')
    with open(install_script_path, 'rb') as f:
        filelike = StringIO.StringIO(f.read())
        filelike.name = 'install_script'
        return filelike
