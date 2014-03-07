from setuptools import setup


setup(
    name='inp',
    version='0.2dev',
    description='Install Nodepool',
    packages=['inp'],
    install_requires=['fabric'],
    package_data = {
        'inp': ['installscript.sh', 'nodepool.yaml'],
    },
    entry_points = {
        'console_scripts': [
            'inp-install = inp.scripts:install',
            'inp-start = inp.scripts:start',
            'inp-osci-install = inp.scripts:osci_install',
            'inp-osci-start = inp.scripts:osci_start',
        ]
    }
)
