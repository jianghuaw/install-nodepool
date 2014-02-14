set -eux

NODEPOOL_REPO="$1"
NODEPOOL_BRANCH="$2"

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
git clone "$NODEPOOL_REPO"
( cd nodepool && git checkout "$NODEPOOL_BRANCH" )
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
sudo mv ~/nodepool.yaml /etc/nodepool/nodepool.yaml

#####
# Run as a daemon
sudo mkdir -p /var/run/nodepool/
sudo mkdir -p /var/log/nodepool/

sudo tee /etc/init/nodepool.conf << NODEPOOLSTARTER
start on runlevel [2345]
stop on runlevel [016]

chdir /

script
    export NODEPOOL_SSH_KEY="\$(cat /home/ubuntu/.ssh/nodepool.pub)"
    /usr/bin/python /usr/local/bin/nodepoold -c /etc/nodepool/nodepool.yaml -l /home/ubuntu/src/config/modules/nodepool/files/logging.conf
end script
NODEPOOLSTARTER

# As nodepool will be executed as root, we need to give the ssh key to root
sudo mkdir /root/.ssh
sudo cp /home/ubuntu/.ssh/nodepool /root/.ssh/id_rsa
sudo chmod 0400 /root/.ssh/id_rsa
sudo chmod 0500 /root/.ssh

#####
# Start now
sudo service nodepool start
