from setuptools import setup


setup(
    name='inp',
    version='0.1dev',
    description='Install Nodepool',
    packages=['inp'],
    install_requires=['fabric'],
    package_data = {
        'inp': ['installscript.sh', 'nodepool.yaml'],
    },
    entry_points = {
        'console_scripts': [
            'inp-install = inp.scripts:install',
        ]
    }
)
