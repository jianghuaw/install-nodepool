#!/bin/bash
set -eux

SOURCE_ENV=". /opt/osci/env/bin/activate"

sudo rm -rf /opt/osci/env /opt/osci/src


######
# Check out sources
sudo mkdir /opt/osci/src
sudo git clone \
    --quiet \
    $OSCI_REPO --branch $OSCI_BRANCH \
    /opt/osci/src


######
# Install binaries
sudo virtualenv /opt/osci/env
sudo bash << EOF
set -ex
. /opt/osci/env/bin/activate
set -u
cd /opt/nodepool/src
pip install -U -r requirements.txt
pip install .

cd /opt/osci/src
pip install -U -r requirements.txt
pip install .
EOF


######
# Set rights
sudo chmod -R g-w,o-w /etc/osci /opt/osci
sudo chown -R $OSCI_USER:nogroup /var/log/osci /var/run/osci
sudo chmod -R g-w,o-w /var/log/osci /var/run/osci
