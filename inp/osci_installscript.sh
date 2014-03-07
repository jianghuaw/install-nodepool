set -eux

OSCI_REPO="$1"
OSCI_BRANCH="$2"

######
# Update apt
#sudo apt-get -qy update
#sudo DEBIAN_FRONTEND=noninteractive apt-get install -qy git mysql-server libmysqlclient-dev g++ python-dev libzmq-dev python-pip < /dev/null

######
# Download nodepool + config
echo -e "Host github.com\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config

[ -e ~/src ] || mkdir ~/src
cd ~/src

git clone "$OSCI_REPO"
(
  cd openstack-citrix-ci
  git checkout "$OSCI_BRANCH"
  # Install requirements
  sudo pip install -U -r requirements.txt
  # and osci itself
  sudo pip install -e .
)

######
# Create database
mysql -u root << DBINIT
create database if not exists openstack_ci;
GRANT ALL ON openstack_ci.* TO 'nodepool'@'localhost';
flush privileges;
DBINIT

osci-create-dbschema

sudo tee /etc/init/citrix-ci.conf << CITRIXCISTARTER
start on runlevel [2345]
stop on runlevel [016]

respawn
respawn limit 3 60

script
start-stop-daemon --start --make-pidfile --pidfile /var/run/citrix-ci.pid --exec /bin/bash -- -c "/root/src/openstack-citrix-ci/citrix-ci.sh >> /var/log/citrix-ci.log 2>&1"
end script
CITRIXCISTARTER

sudo tee /etc/init/citrix-ci-gerritwatch.conf << GERRITWATCH
start on runlevel [2345]
stop on runlevel [016]

respawn
respawn limit 3 60

script
start-stop-daemon --start --make-pidfile --pidfile /var/run/citrix-ci-gerritwatch.pid --exec /bin/bash -- -c "/root/src/openstack-citrix-ci/citrix-ci-gerritwatch.sh >> /var/log/citrix-ci-gerritwatch.log 2>&1"
end script
GERRITWATCH

if [ ! -e /root/.ssh/citrix_gerrit ]; then
    [ -e /root/.ssh ] || sudo mkdir /root/.ssh
    sudo cp /root/.ssh/citrix_gerrit /root/.ssh/
    sudo chmod 0400 /root/.ssh/citrix_gerrit
    sudo chmod 0500 /root/.ssh
fi

# Add gerrit to known hosts: Mate's proxy (first) and then the real gerrit
sudo tee -a /root/.ssh/known_hosts << KNOWN_HOST
|1|uvH7eZ2XTbkdHUUXZ3XBScp6SO0=|uYehq2EeLpZYm2+UJew0YUhzUSU= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDtdLzDzG6qmejiZq5BxDqxkN71W08xuQWVZ+6784SpsXTUujKT49lNCXmH+IHijsRaigU9cVFkWErVez0Q+NtUe077c5s50zCrL7EwH5/aiwaYklHF566TO7ctOJBLLsoVOUlJGpUAjM4veG9XMz0KhTP9qYK3zqNOcPV++551bQu1rc3kR8R8C/etmP60zMhVkUAdgyPWFZbmKlrBv1SxIpvjSo5STZzSRS7DK5/D9BaWS3zOcl5Pqtv0FVjm83dmQJxMPEjFo8e0T4Gq/noxYafQse4811/Ucmxj8J5rlJchakfxJz827w3MWYR4Ku+X3QAy/deBuvzUn3z35Zwr
|1|v64yXgSHd9wX62/OTnmu4O91rXo=|NkrM8t/1ZlyLl0NhSXWx8GkvjcU= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDtdLzDzG6qmejiZq5BxDqxkN71W08xuQWVZ+6784SpsXTUujKT49lNCXmH+IHijsRaigU9cVFkWErVez0Q+NtUe077c5s50zCrL7EwH5/aiwaYklHF566TO7ctOJBLLsoVOUlJGpUAjM4veG9XMz0KhTP9qYK3zqNOcPV++551bQu1rc3kR8R8C/etmP60zMhVkUAdgyPWFZbmKlrBv1SxIpvjSo5STZzSRS7DK5/D9BaWS3zOcl5Pqtv0FVjm83dmQJxMPEjFo8e0T4Gq/noxYafQse4811/Ucmxj8J5rlJchakfxJz827w3MWYR4Ku+X3QAy/deBuvzUn3z35Zwr
KNOWN_HOST
