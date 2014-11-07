set -eux

NODEPOOL_REPO="$1"
NODEPOOL_BRANCH="$2"

NODEPOOL_USER="nodepool"
NODEPOOL_HOME="/home/$NODEPOOL_USER"
NODEPOOL_VENV="$NODEPOOL_HOME/env"
NODEPOOL_SRC="$NODEPOOL_HOME/src/nodepool"
NODEPOOL_CFG_DIR="$NODEPOOL_HOME/conf"
NODEPOOL_LOGS="$NODEPOOL_HOME/logs"


######
# Install system level dependencies
sudo apt-get -qy update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy \
    git mysql-server libmysqlclient-dev g++ python-dev libzmq-dev \
    python-pip python-virtualenv \
    gearman-job-server < /dev/null


######
# Create a nodepool user
sudo adduser --system \
    --home $NODEPOOL_HOME \
    --disabled-password \
    --quiet \
    --gecos $NODEPOOL_USER \
    $NODEPOOL_USER

function as_nodepool() {
    sudo -u $NODEPOOL_USER bash -c "$1"
}


######
# Get nodepool sources
as_nodepool "git clone \
    $NODEPOOL_REPO --branch $NODEPOOL_BRANCH \
    $NODEPOOL_SRC"


######
# Create virtual environment
as_nodepool "virtualenv $NODEPOOL_VENV"

function in_venv() {
    as_nodepool "set +u && . $NODEPOOL_VENV/bin/activate && set -u && $1"
}


######
# Install python requirements
in_venv "pip install -U distribute"
in_venv "cd $NODEPOOL_SRC && pip install -U -r requirements.txt"
in_venv "cd $NODEPOOL_SRC && pip install ."
in_venv "pip install python-novaclient rackspace-auth-openstack"


######
# Create config and logging dir
as_nodepool "mkdir $NODEPOOL_CFG_DIR"
as_nodepool "mkdir $NODEPOOL_LOGS"


######
# Create database
mysql -u root << DBINIT
create database nodepool;
GRANT ALL ON nodepool.* TO 'nodepool'@'localhost';
flush privileges;
DBINIT


sudo -u $NODEPOOL_USER tee $NODEPOOL_CFG_DIR/logging.conf << EOF
[loggers]
keys=root,nodepool,requests,image

[handlers]
keys=console,debug,normal,image

[formatters]
keys=simple

[logger_root]
level=WARNING
handlers=console

[logger_requests]
level=WARNING
handlers=debug,normal
qualname=requests

[logger_nodepool]
level=DEBUG
handlers=debug,normal
qualname=nodepool

[logger_image]
level=INFO
handlers=image
qualname=nodepool.image.build
propagate=0

[handler_console]
level=WARNING
class=StreamHandler
formatter=simple
args=(sys.stdout,)

[handler_debug]
level=DEBUG
class=logging.handlers.TimedRotatingFileHandler
formatter=simple
args=('$NODEPOOL_LOGS/debug.log', 'midnight', 1, 30,)

[handler_normal]
level=INFO
class=logging.handlers.TimedRotatingFileHandler
formatter=simple
args=('$NODEPOOL_LOGS/nodepool.log', 'midnight', 1, 30,)

[handler_image]
level=INFO
class=logging.handlers.TimedRotatingFileHandler
formatter=simple
args=('$NODEPOOL_LOGS/image.log', 'midnight', 1, 30,)

[formatter_simple]
format=%(asctime)s %(levelname)s %(name)s: %(message)s
datefmt=
EOF

sudo tee /etc/init/nodepool.conf << NODEPOOLSTARTER
start on runlevel [2345]
stop on runlevel [016]

setuid $NODEPOOL_USER

chdir /

script
    export NODEPOOL_SSH_KEY="\$(cat $HOME/.ssh/nodepool.pub)"
    $NODEPOOL_VENV/bin/python \\
        $NODEPOOL_VENV/bin/nodepoold \\
        -c $NODEPOOL_CFG_DIR/nodepool.yaml \\
        -l $NODEPOOL_CFG_DIR/logging.conf \\
        -p $NODEPOOL_HOME/nodepool.pid \\
        -d
end script
NODEPOOLSTARTER
