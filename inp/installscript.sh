set -eux

RACKSPACE_PASSWORD="$1"

######
# Update apt
sudo sed -ie "s,mirror.anl.gov/pub/ubuntu,mirror.pnl.gov/ubuntu,g" /etc/apt/sources.list
sudo apt-get -qy update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy git mysql-server libmysqlclient-dev g++ python-dev libzmq-dev python-pip < /dev/null
sudo apt-get install -qy gearman-job-server < /dev/null
sudo apt-get install -qy python-novaclient < /dev/null

######
# Download nodepool + config
echo -e "Host github.com\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config

mkdir src
cd ~/src
#git clone git@github.com:citrix-openstack/config.git
git clone https://github.com/citrix-openstack/config.git
pushd config
popd

#git clone git@github.com:citrix-openstack/nodepool.git
git clone https://github.com/citrix-openstack/nodepool.git
pushd nodepool
popd

######
# Install requirements
pushd nodepool
sudo pip install -U distribute
sudo pip install -U -r requirements.txt
sudo pip install -e .
sudo pip install rackspace-auth-openstack
popd

######
# Create database
mysql -u root << DBINIT
create database nodepool;
GRANT ALL ON nodepool.* TO 'nodepool'@'localhost';
flush privileges;
DBINIT

source ~/.bash_profile
nova keypair-delete nodepool || true
nova keypair-add --pub-key ~/.ssh/nodepool.pub nodepool

######
# Config file for nodepool
sudo mkdir -p /etc/nodepool/
cat > _nodepool.yaml << NODEPOOL
script-dir: /home/ubuntu/src/config/modules/openstack_project/files/nodepool/scripts/
dburi: 'mysql://nodepool@localhost/nodepool'

cron:
  cleanup: '*/1 * * * *'
  update-image: '14 2 * * *'

zmq-publishers:
  - tcp://localhost:8888

gearman-servers:
  - host: localhost

providers:
  - name: rax-iad
    region-name: '$OS_REGION_NAME'
    service-type: 'compute'
    service-name: 'cloudServersOpenStack'
    username: '$OS_USERNAME'
    password: '$RACKSPACE_PASSWORD'
    project-id: '$OS_PROJECT_ID'
    auth-url: '$OS_AUTH_URL'
    boot-timeout: 120
    max-servers: 2
    keypair: nodepool
    images:
      - name: devstack-xenserver
        base-image: '62df001e-87ee-407c-b042-6f4e13f5d7e1'
        min-ram: 8192
        name-filter: 'Performance'
        install: install_xenserver.sh
        install_poll_interval: 10
        install_poll_count: 80
        install_status_file: /var/run/xenserver.ready
        launch_poll_interval: 10
        launch_poll_count: 40
        launch_done_stamp: /var/run/xenserver.ready
        username: 'root'
        private-key: /home/ubuntu/.ssh/nodepool

targets:
  - name: fake-jenkins
    jenkins:
      url: https://jenkins.example.org/
      user: fake
      apikey: fake
    images:
      - name: devstack-xenserver
        min-ready: 1
        providers:
          - name: rax-iad

NODEPOOL
sudo mv _nodepool.yaml /etc/nodepool/nodepool.yaml

#####
# Run as a daemon
sudo mkdir -p /var/run/nodepool/
sudo mkdir -p /var/log/nodepool/

cat > _rc.local << RCLOCAL
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.
/usr/bin/python /usr/local/bin/nodepoold -c /etc/nodepool/nodepool.yaml -l /home/ubuntu/src/config/modules/nodepool/files/logging.conf

exit 0
RCLOCAL
sudo mv -f _rc.local /etc/rc.local

#####
# Start now
sudo nohup /usr/bin/python /usr/local/bin/nodepoold -c /etc/nodepool/nodepool.yaml -l /home/ubuntu/src/config/modules/nodepool/files/logging.conf &
