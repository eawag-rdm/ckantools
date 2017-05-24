## sync_users.sh

**deprecated: Why not copy the whole fricking DB? -> Use `copydb.sh`**

Copies  users from one CKAN instance to another.

HvW @ Eawag - 2017-05-17

When username or id already exists in target,
the record is skipped. The script iterates
through tables "user" and "ldap_user".
Both have to exist on target (activate ckanext-ldap).

Set parameters by modifying variables at the beginning of the script.

## copydb.sh

HvW @ Eawag - 2017-05-24

Dumps CKAN database from `$sourcehost` and initializes
CKAN database at `$targethost`.

Updates the database-schema
(Useful if moving from one Postgres version to another).

Rebuilds SOLR-index.

Useful to sync the DB on development-server with production, or
for moving production to a different machine.

**DROPS EXISTING DATABASE FROM TARGET**

If `$target` is a development server (`$DEVSERVER="true"`), the user has to
manually kill it before the operation and re-start it after the operation.

The user has to manually set the permissions for datastor, something liek that:
`paster --plugin=ckan datastore set-permissions -c /etc/ckan/default/development.ini |\`
`ssh ${targethost} "sudo -u postgres psql"

Assumptions:
  1. The database-cluster at target is installed according to
     Debian defaults (name="main")
  2. The database-cluster at target is installed with `--locale en_US.UTF-8`
  3. The database-cluster at target is properly configured
    + in `/etc/postgresql/${postgres_version}/main/postgresql.conf`:
          `listen_addresses = '*'`
    + in `/etc/postgresql/9.5/main/pg_hba.conf`:
        > # Allow ckan-instance
        > host    all             all             152.88.xxx.xxx/32        md5
        > # Allow developer's workstation
        > host    all             all             152.88.xxx.xxx/32        md5
  4. Users `ckan_default` and `datastore_default` exist in DB on `targethost`.
    + `sudo -u postgres createuser -S -D -R -P ckan_default`
    + `sudo -u postgres createuser -S -D -R -P -l datastore_default`

  4. Executing user can passwordless ssh into $sourcehost, $targethost
     and $target_ckanhost
  5. Executng user has passwordless sudo on $sourcehost, $targethost
     and $target_ckanhost

Parameters:
  All variables between "PARAMETERS" and "END PARAMETERS"

#############################################################################
