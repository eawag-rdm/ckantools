#!/bin/bash

# #############################################################################
# HvW @ Eawag - 2017-05-24
#
# Dumps CKAN database from $sourcehost and initializes
# CKAN database at $targethost.
#
# Updates the database-schema
# (Useful if moving from one Postgres version to another).
#
# Rebuilds SOLR-index.
#
# Useful to sync the DB on development-server with production, or
# for moving production to a different machine.
#
# ### DROPS EXISTING DATABASE FROM TARGET ###
#
# If $target is a development server ($DEVSERVER="true"), the user has to
# manually kill it before the operation and re-start it after the operation.
#
# Assumptions:
#   1. The database-cluster at target is installed according to
#      Debian defaults (name="main")
#   2. The database-cluster at target is installed with --locale en_US.UTF-8
#   3. The database-cluster at target is properly configured
#     + /etc/postgresql/${postgres_version}/main/postgresql.conf:
#           `listen_addresses = '*'`
#     + /etc/postgresql/9.5/main/pg_hba.conf:
#         # Allow ckan-instance
#         host    all             all             152.88.xxx.xxx/32        md5
#         # Allow developer's workstation
#         host    all             all             152.88.xxx.xxx/32        md5
#   4. Executing user can passwordless ssh into $sourcehost, $targethost
#      and $target_ckanhost
#   5. Executng user has passwordless sudo on $sourcehost, $targethost
#      and $target_ckanhost
#
# Parameters:
#   All variables between "PARAMETERS" and "END PARAMETERS"
#
# #############################################################################

## PARAMETERS #################################################################

sourcehost="eaw-ckan-dev1.eawag.wroot.emp-eaw.ch"
sourceport="5432"

# targethost="eaw-ckan-db1.eawag.wroot.emp-eaw.ch"
targethost="localhost"
targetport="5432"

# The host running CKAN with database on $targethost
#target_ckanhost="eaw-ckan-prod1.eawag.wroot.emp-eaw.ch"
target_ckanhost="localhost"
DEVSERVER="true"

## My passwords are managed by "pass"
pgsourcepw=`pass eawag/postgres:ckan_default@eaw-ckan-dev1`
#pgtargetpw=`pass eawag/postgres:ckan_default@eaw-ckan-db1`
pgtargetpw=`pass eawag/postgres:ckan_default@localhost`

## Postgres-versions (target)
# postgres_version="9.6"
# postgis_version="2.3"
postgres_version="9.5"
postgis_version="2.2"

# location of contrib script to update PostGIS objects
target_postgis_restore="/usr/share/postgresql/${postgres_version}/contrib/postgis-${postgis_version}/postgis_restore.pl"

## END PARAMETERS##############################################################

sourceconn="postgresql://ckan_default:$pgsourcepw@$sourcehost:$sourceport"
sourceconnlocal="postgresql://ckan_default:$pgsourcepw@localhost:$sourceport"
targetconn="postgresql://ckan_default:$pgtargetpw@$targethost:$targetport"
targetconnlocal="postgresql://ckan_default:$pgtargetpw@localhost:$targetport"

# directory for temporary storing db-dump
dumpdir="./dumps"

# directory for storing DB-backups
db_backups="./db_backup"

[[ -d $dumpdir ]] || mkdir $dumpdir
[[ -d $db_backups ]] || mkdir $db_backups

timestamp=`date -I'seconds'`

set -u # exit if un-initialized variable is used

shutdown_target_ckan() {
    echo "Shutting dow apache2 on $target_ckanhost"
    ssh $target_ckanhost "sudo systemctl stop apache2"
}

start_target_ckan() {
    echo  "Starting apache2 on $target_ckanhost"
    ssh $target_ckanhost "sudo systemctl start apache2"
}

db_schema_upgrade_target() {
    echo "Upgrading db-schema at $targethost (from $target_ckanhost)"
    if [[ $DEVSERVER == "true" ]]; then
	user=`whoami`
	inifile="/etc/ckan/default/development.ini"
    else
	user="ckan"
	inifile="/etc/ckan/default/production.ini"
    fi
    ssh $target_ckanhost "sudo -u $user /usr/lib/ckan/default/bin/paster --plugin=ckan db upgrade -c $inifile"
}

solr_reindex() {
    echo "reindexing SOLR"
    if [[ $DEVSERVER == "true" ]]; then
	user=`whoami`
	inifile="/etc/ckan/default/development.ini"
    else
	user="ckan"
	inifile="/etc/ckan/default/production.ini"
    fi
    ssh $target_ckanhost "sudo -u $user /usr/lib/ckan/default/bin/paster --plugin=ckan search-index rebuild_fast -c $inifile"
}
    
backup_target() {
    echo "Backing up DB $1 from $targethost to $db_backups/$1_$timestamp"
    if [[ `check_exist_db $1 $targethost` == 0 ]]; then
	ssh $targethost pg_dump -Fc -b ${targetconn}/$1 >$db_backups/target_$1_$timestamp
    else
	echo "WARNING: DB $1 doesn't exist on $targethost -- skipping"
    fi
}

check_exist_db () { # arguments: dbname hostname
    ssh $2 sudo -u postgres psql -lqt |cut -d \| -f1 |grep -w $1 >/dev/null
    echo $?
}

drop_target_db () {
    echo "Dropping DB $1 from $targethost"
    if [[ `check_exist_db $1 $targethost` == 0 ]]; then
	ssh $targethost sudo -u postgres dropdb $1
    else
	echo "WARNING: DB $1 doesn't exist on $targethost -- skipping"
    fi
}

dump_source_db () {
    echo "Dumping $1 from $sourcehost"
    
    if [[ `check_exist_db $1 $sourcehost` == 0 ]]; then
	ssh $sourcehost "pg_dump -Fc -b ${sourceconnlocal}/$1" >$dumpdir/source_$1_$timestamp
    else
	echo "WARNING: DB $1 doesn't exist on $targethost -- skipping"
    fi
}

cp_sourcedump_to_target() {
    echo "copying $dumpdir to $targethost"
    ssh $targethost "mkdir dbdumps_tmp"
    scp -r ${dumpdir}/* $targethost:dbdumps_tmp
}


create_target_tables() {
    echo "Creating table ckan_default on $targethost"
    ssh $targethost "sudo -u postgres createdb -O ckan_default ckan_default -E utf-8"
    echo "Creating table datastore_default on $targethost"
    ssh $targethost "sudo -u postgres createdb -O ckan_default datastore_default -E utf-8"
}

init_target_postgis() {
    echo "running postgis.sql on $targethost"
    ssh $targethost "sudo -u postgres psql -d ckan_default -f /usr/share/postgresql/${postgres_version}/contrib/postgis-${postgis_version}/postgis.sql"
    echo "running spatial_ref_sys.sql on $targethost"
    ssh $targethost "sudo -u postgres psql -d ckan_default -f /usr/share/postgresql/${postgres_version}/contrib/postgis-${postgis_version}/spatial_ref_sys.sql"
    echo "setting ownership spatial tables on $targethost"
    ssh $targethost "sudo -u postgres psql -d ckan_default -c 'ALTER VIEW geometry_columns OWNER TO ckan_default;'"
    ssh $targethost "sudo -u postgres psql -d ckan_default -c 'ALTER TABLE spatial_ref_sys OWNER TO ckan_default;'"
}

prepare_postgis_dump() {
    echo "Preprocessing source-dump of ckan_default for PostGIS - restore"
    ssh $targethost "perl $target_postgis_restore dbdumps_tmp/source_ckan_default_$timestamp >dbdumps_tmp/ckan_default_postgis.sql"
}

restore_db() {
    echo "Restoring ckan_default_postgis into ckan_default at $targethost"
    ssh $targethost "sudo -u postgres psql -d ckan_default -f dbdumps_tmp/ckan_default_postgis.sql"
    echo "Restoring datastore_default"
    ssh $targethost "sudo -u postgres pg_restore -d datastore_default dbdumps_tmp/source_datastore_default_$timestamp" 
}

cleanup() {
    echo "Removing $targethost:dbdumps_tmp"
    ssh $targethost "rm -rf dbdumps_tmp"
}

if [[ ! $DEVSERVER == "true" ]]; then
    shutdown_target_ckan
fi
backup_target ckan_default
backup_target datastore_default
drop_target_db ckan_default
drop_target_db datastore_default
dump_source_db ckan_default
dump_source_db datastore_default
cp_sourcedump_to_target
create_target_tables
init_target_postgis
prepare_postgis_dump
restore_db
cleanup
db_schema_upgrade_target
if [[ ! $DEVSERVER == "true" ]]; then
    start_target_ckan
fi
solr_reindex


