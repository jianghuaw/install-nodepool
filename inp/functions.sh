function get_nodepool_sources() {
    sudo git clone \
        --quiet \
        $NODEPOOL_REPO --branch $NODEPOOL_BRANCH \
        /opt/nodepool/src
}
