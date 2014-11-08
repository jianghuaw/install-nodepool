set -eux

######
# Install system level dependencies
sudo apt-get -qy update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy \
    git mysql-server libmysqlclient-dev g++ python-dev libzmq-dev \
    python-pip python-virtualenv \
    gearman-job-server < /dev/null


######
# Create a nodepool user
sudo adduser \
    --home $NODEPOOL_HOME_DIR \
    --disabled-password \
    --quiet \
    --gecos $NODEPOOL_USER \
    $NODEPOOL_USER


######
# Create install directory
sudo mkdir /opt/nodepool
sudo virtualenv /opt/nodepool/env


######
# Create config directory
sudo mkdir /etc/nodepool


######
# Create pid directory
sudo mkdir /var/run/nodepool


######
# Create log directory
sudo mkdir /var/log/nodepool


######
# Check out sources
sudo mkdir /opt/nodepool/src
sudo git clone \
    --quiet \
    $NODEPOOL_REPO --branch $NODEPOOL_BRANCH \
    /opt/nodepool/src


######
# Install binaries
sudo bash << EOF
set -ex
. /opt/nodepool/env/bin/activate
set -u
cd /opt/nodepool/src
pip install -U distribute
pip install -U -r requirements.txt
pip install .
pip install python-novaclient rackspace-auth-openstack
EOF


######
# Create database
mysql -u root << DBINIT
create database nodepool;
GRANT ALL ON nodepool.* TO 'nodepool'@'localhost';
flush privileges;
DBINIT

sudo chmod -R g-w,o-w /etc/nodepool /opt/nodepool
sudo chown -R $NODEPOOL_USER:nogroup /var/log/nodepool /var/run/nodepool
sudo chmod -R g-w,o-w /var/log/nodepool /var/run/nodepool
