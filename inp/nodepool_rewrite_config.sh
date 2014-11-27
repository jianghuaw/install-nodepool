set -eux

THIS_FILE=$(readlink -f $0)
THIS_DIR=$(dirname $THIS_FILE)

sudo cp $THIS_DIR/nodepool.yaml /etc/nodepool/nodepool.yaml

sudo chmod g-w,o-w /etc/nodepool/nodepool.yaml
