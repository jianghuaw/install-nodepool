set -eux

######
# Make sure nodepool is stopped
service nodepool status | grep -q "stop/waiting"


######
# Backup actual version
sudo tar -czf $NODEPOOL_HOME_DIR/nodepool-backup.tgz -C /opt/nodepool env src


######
# Remove
sudo rm -rf /opt/nodepool/{env,src}


######
# Check out sources
sudo mkdir /opt/nodepool/src
sudo git clone \
    --quiet \
    $NODEPOOL_REPO --branch $NODEPOOL_BRANCH \
    /opt/nodepool/src


######
# Install binaries
sudo virtualenv /opt/nodepool/env
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
# Adjust rights
sudo chmod -R g-w,o-w /opt/nodepool
