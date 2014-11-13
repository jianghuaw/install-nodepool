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
            'osci_release.sh',
            'update.sh',
            'nodepool.yaml',
            'osci.config',
            'backup.sh',
            'restore.sh'],
    },
    entry_points = {
        'console_scripts': [
            'inp-install = inp.scripts:install',
            'inp-upload-keys = inp.scripts:nodepool_upload_keys',
            'inp-nodepool-configure = inp.scripts:nodepool_configure',
            'inp-nodepool-update = inp.scripts:nodepool_update',
            'inp-start = inp.scripts:start',
            'inp-osci-install = inp.scripts:osci_install',
            'inp-osci-release = inp.scripts:osci_release',
            'inp-osci-start = inp.scripts:osci_start',
            'inp-osci-backup = inp.scripts:backup',
            'inp-osci-restore = inp.scripts:restore',
        ]
    }
)
