set -eux

THIS_FILE=$(readlink -f $0)
THIS_DIR=$(dirname $THIS_FILE)


######
# Create an osci user
sudo adduser \
    --home $OSCI_HOME_DIR \
    --disabled-password \
    --quiet \
    --gecos $OSCI_USER \
    $OSCI_USER


######
# Create install directory
sudo mkdir /opt/osci


######
# Create config directory
sudo mkdir /etc/osci


######
# Create pid directory
sudo mkdir /var/run/osci


######
# Create log directory
sudo mkdir /var/log/osci


######
# Check out sources
sudo mkdir /opt/osci/src
sudo git clone \
    --quiet \
    $OSCI_REPO --branch $OSCI_BRANCH \
    /opt/osci/src


######
# Create database
mysql -u root << DBINIT
create database if not exists openstack_ci;
GRANT ALL ON openstack_ci.* TO 'nodepool'@'localhost';
flush privileges;
DBINIT


SOURCE_ENV=". /opt/osci/env/bin/activate"

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

######
# Create Database Schema
sudo -u $OSCI_USER -i bash -c "$SOURCE_ENV ; osci-create-dbschema"


sudo tee /etc/init/citrix-ci.conf << CITRIXCISTARTER
start on runlevel [2345]
stop on runlevel [016]

respawn
respawn limit 3 60

setuid $OSCI_USER
chdir $OSCI_HOME_DIR

script
start-stop-daemon --start --make-pidfile \\
    --pidfile /var/run/osci/citrix-ci.pid \\
    --exec /bin/bash -- -c "$SOURCE_ENV; /opt/osci/src/citrix-ci.sh \\
    >> /var/log/osci/citrix-ci.log 2>&1"
end script
CITRIXCISTARTER

sudo tee /etc/init/citrix-ci-gerritwatch.conf << GERRITWATCH
start on runlevel [2345]
stop on runlevel [016]

respawn
respawn limit 3 60

setuid $OSCI_USER
chdir $OSCI_HOME_DIR

script
start-stop-daemon --start --make-pidfile \\
    --pidfile /var/run/osci/citrix-ci-gerritwatch.pid \\
    --exec /bin/bash -- -c "$SOURCE_ENV; /opt/osci/src/citrix-ci-gerritwatch.sh \\
    >> /var/log/osci/citrix-ci-gerritwatch.log 2>&1"
end script
GERRITWATCH


######
# Copy ssh settings
sudo rm -rf $OSCI_HOME_DIR/.ssh
sudo mkdir $OSCI_HOME_DIR/.ssh

sudo cp $THIS_DIR/gerrit.key $OSCI_HOME_DIR/.ssh/gerrit
sudo chown -R $OSCI_USER:$OSCI_USER $OSCI_HOME_DIR/.ssh
sudo chmod -R g-w,g-r,o-w,o-r $OSCI_HOME_DIR/.ssh

echo "JJJ -- TODO -- "
exit 1

# Add gerrit to known hosts: Mate's proxy (first) and then the real gerrit
sudo tee -a /root/.ssh/known_hosts << KNOWN_HOST
|1|uvH7eZ2XTbkdHUUXZ3XBScp6SO0=|uYehq2EeLpZYm2+UJew0YUhzUSU= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDtdLzDzG6qmejiZq5BxDqxkN71W08xuQWVZ+6784SpsXTUujKT49lNCXmH+IHijsRaigU9cVFkWErVez0Q+NtUe077c5s50zCrL7EwH5/aiwaYklHF566TO7ctOJBLLsoVOUlJGpUAjM4veG9XMz0KhTP9qYK3zqNOcPV++551bQu1rc3kR8R8C/etmP60zMhVkUAdgyPWFZbmKlrBv1SxIpvjSo5STZzSRS7DK5/D9BaWS3zOcl5Pqtv0FVjm83dmQJxMPEjFo8e0T4Gq/noxYafQse4811/Ucmxj8J5rlJchakfxJz827w3MWYR4Ku+X3QAy/deBuvzUn3z35Zwr
|1|v64yXgSHd9wX62/OTnmu4O91rXo=|NkrM8t/1ZlyLl0NhSXWx8GkvjcU= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDtdLzDzG6qmejiZq5BxDqxkN71W08xuQWVZ+6784SpsXTUujKT49lNCXmH+IHijsRaigU9cVFkWErVez0Q+NtUe077c5s50zCrL7EwH5/aiwaYklHF566TO7ctOJBLLsoVOUlJGpUAjM4veG9XMz0KhTP9qYK3zqNOcPV++551bQu1rc3kR8R8C/etmP60zMhVkUAdgyPWFZbmKlrBv1SxIpvjSo5STZzSRS7DK5/D9BaWS3zOcl5Pqtv0FVjm83dmQJxMPEjFo8e0T4Gq/noxYafQse4811/Ucmxj8J5rlJchakfxJz827w3MWYR4Ku+X3QAy/deBuvzUn3z35Zwr
KNOWN_HOST

# Add uploading of status to crontab
crontab - <<EOF
*/10 * * * * /root/src/openstack-citrix-ci/upload_ci_status.sh
EOF
