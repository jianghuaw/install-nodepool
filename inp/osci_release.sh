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

pip install -U requests==2.2.0
EOF



######
# Create a link for osci-view
rm -f /usr/local/bin/osci-view
sudo ln -s -t /usr/local/bin /opt/osci/env/bin/osci-view


######
# Create osci-manage
rm -f /usr/local/bin/osci-manage
sudo tee /usr/local/bin/osci-manage << EOF
#!/bin/bash
sudo -u $OSCI_USER -i /opt/osci/env/bin/osci-manage "\$@"
EOF
sudo chmod 0755 /usr/local/bin/osci-manage


######
# Set rights
sudo chmod -R g-w,o-w /etc/osci /opt/osci
sudo chown -R $OSCI_USER:nogroup /var/log/osci /var/run/osci
sudo chmod -R g-w,o-w /var/log/osci /var/run/osci
