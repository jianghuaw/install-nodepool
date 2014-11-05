# install-nodepool

Scripts to install nodepool and OSCI, the XenServer OpenStack CI.

## Installation

Use pip to install this software package. As an example, if you have this
directory cloned to `~/src/install-nodepool` then:

    pip install ~/somedir

## Usage

To demonstrate an example installation, a VM will be used. This VM is
accessible on port `2424` on the host `localhost`. It's actually a VM having
its ssh port forwarded there. The user/password combo is `ubuntu/ubuntu`. The
VM is running **Ubuntu 14.04.1 LTS**.

Now you need to create a key to be used to communicate with the box:

    ssh-keygen -f ubuntu.key -N ""

And another one to be used by nodepool

    ssh-keygen -f osci.key -N ""

To enable passwordless authentication to the new system, load an agent and add
the key:

    eval $(ssh-agent)
    ssh-add ubuntu.key

And enable authentication to the system:

    cat ubuntu.key.pub |
        ssh -p 2424 ubuntu@localhost "mkdir .ssh && dd of=.ssh/authorized_keys"

The following command should not ask for a password:

    ssh -p 2424 ubuntu@localhost "ls -la"

### Install nodepool

To install nodepool (but not to start it yet!), you should do the following:

    inp-install --port 2424 ubuntu 127.0.0.1

After this operation, you should be have startup files in place for nodepool.

