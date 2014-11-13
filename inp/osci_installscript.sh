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
    $SOURCE_ENV && osci-manage -v \\
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
    $SOURCE_ENV && osci-watch-gerrit \\
    >> /var/log/osci/citrix-ci-gerritwatch.log 2>&1
end script
GERRITWATCH


######
# Copy ssh settings
sudo rm -rf $OSCI_HOME_DIR/.ssh
sudo mkdir $OSCI_HOME_DIR/.ssh

sudo cp $NODEPOOL_HOME_DIR/.ssh/jenkins $OSCI_HOME_DIR/.ssh/jenkins
sudo cp $THIS_DIR/gerrit.key $OSCI_HOME_DIR/.ssh/id_rsa
sudo chown -R $OSCI_USER:$OSCI_USER $OSCI_HOME_DIR/.ssh
sudo chmod -R g-w,g-r,o-w,o-r $OSCI_HOME_DIR/.ssh

GERRIT_HOST=23.253.232.87
GERRIT_PORT=29418


sudo tee /etc/osci/osci.config << OSCI_CONF_END
RUN_TESTS=True
VOTE=False
VOTE_PASSED_ONLY=True
VOTE_SERVICE_ACCOUNT=False
MYSQL_USERNAME=nodepool
GERRIT_HOST=$GERRIT_HOST
GERRIT_PORT=$GERRIT_PORT
RECHECK_REGEXP=.*(citrix recheck|xenserver:? recheck|recheck xenserver).*
KEEP_FAILED=2
PROJECT_CONFIG=openstack/nova,openstack/tempest,openstack-dev/devstack,stackforge/xenapi-os-testing
NODE_KEY=$OSCI_HOME_DIR/.ssh/jenkins
SWIFT_API_KEY=$SWIFT_API_KEY
NODEPOOL_IMAGE=$IMAGE_NAME
OSCI_CONF_END

######
# Add gerrit to known hosts:
sudo -u osci -i /bin/bash -c "ssh-keyscan -H -t rsa -p $GERRIT_PORT '$GERRIT_HOST [$GERRIT_HOST]:$GERRIT_PORT'> ~/.ssh/known_hosts"

echo "JJJ -- TODO -- "
exit 1

# Add uploading of status to crontab
crontab - <<EOF
*/10 * * * * /root/src/openstack-citrix-ci/upload_ci_status.sh
EOF
