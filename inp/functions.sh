function get_nodepool_sources() {
    sudo git clone \
        --quiet \
        $NODEPOOL_REPO /opt/nodepool/src
    pushd /opt/nodepool/src
    git checkout $NODEPOOL_BRANCH
    popd
}
