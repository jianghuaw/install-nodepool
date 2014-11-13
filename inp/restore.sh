######
# Create database
mysql -u root << DBINIT
drop database if exists nodepool;
create database nodepool;
GRANT ALL ON nodepool.* TO 'nodepool'@'localhost';
flush privileges;

drop database if exists openstack_ci;
create database openstack_ci;
GRANT ALL ON openstack_ci.* TO 'nodepool'@'localhost';
flush privileges;
DBINIT


TEMPDIR=$(mktemp -d)
tar -xzf osci-backup.tgz -C $TEMPDIR

mysql -u root nodepool < $TEMPDIR/nodepool.sql
mysql -u root openstack_ci < $TEMPDIR/openstack_ci.sql

rm -rf $TEMPDIR
