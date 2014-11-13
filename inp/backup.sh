#!/bin/bash

set -eux

TMPDIR=$(mktemp -d)

mysqldump -u root openstack_ci > $TMPDIR/openstack_ci.sql
mysqldump -u root nodepool > $TMPDIR/nodepool.sql

tar -czf osci-backup.tgz -C $TMPDIR ./

rm -rf $TMPDIR
