from setuptools import setup


setup(
    name='inp',
    version='0.2dev',
    description='Install Nodepool',
    packages=['inp'],
    install_requires=['fabric', 'PyYaml'],
    package_data = {
        'inp': [
            'installscript.sh',
            'nodepool_config.sh',
            'osci_installscript.sh',
            'nodepool.yaml'],
    },
    entry_points = {
        'console_scripts': [
            'inp-install = inp.scripts:install',
            'inp-upload-keys = inp.scripts:nodepool_upload_keys',
            'inp-nodepool-configure = inp.scripts:nodepool_configure',
            'inp-start = inp.scripts:start',
            'inp-osci-install = inp.scripts:osci_install',
            'inp-osci-start = inp.scripts:osci_start',
        ]
    }
)
