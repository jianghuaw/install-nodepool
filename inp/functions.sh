function get_nodepool_sources() {
    sudo git clone \
        --quiet \
        $NODEPOOL_REPO /opt/nodepool/src
    pushd /opt/nodepool/src
    git checkout $NODEPOOL_BRANCH
    popd
}


function get_osci_sources() {
    sudo git clone \
        --quiet \
        $OSCI_REPO /opt/osci/src
    pushd /opt/osci/src
    git checkout $OSCI_BRANCH
    popd
}
