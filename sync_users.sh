#!/bin/bash

#############################################
# Copy users from one CKAN instance to another.
#
# HvW @ Eawag - 2017-05-17
#
#############################################
set -e
set -u

## Supply connection parameters to databases ################
sourcehost="eaw-ckan-dev1.eawag.wroot.emp-eaw.ch:5432"
targethost="eaw-ckan-db1.eawag.wroot.emp-eaw.ch:5432"
# targethost="localhost:5432"

## My passwords are managed by "pass"
pgsourcepw=`pass eawag/postgres:ckan_default@eaw-ckan-dev1`
pgtargetpw=`pass eawag/postgres:ckan_default@eaw-ckan-db1`
# pgtargetpw=`pass eawag/postgres:ckan_default@localhost`


sourceconn="postgresql://ckan_default:$pgsourcepw@$sourcehost/ckan_default"
targetconn="postgresql://ckan_default:$pgtargetpw@$targethost/ckan_default"


RUN_TARGETDB="psql -X $targetconn --set ON_ERROR_STOP=on --set AUTOCOMMIT=off ckan_default"
RUN_SOURCEDB="psql -X $sourceconn --set ON_ERROR_STOP=on --set AUTOCOMMIT=off ckan_default"

mktmptable() {
    $RUN_TARGETDB <<EOF
CREATE TABLE IF NOT EXISTS public.$1_tmp (LIKE public.$1 INCLUDING ALL);
COMMIT;
EOF
}

readsource() {
    $RUN_SOURCEDB <<EOF
COPY public.$1 TO STDOUT;
EOF
}

writetable() {
    $RUN_TARGETDB -c "\copy public.$1_tmp from stdin; commit;"
}

clear_tmp() {
    $RUN_TARGETDB<<EOF
delete from public.$1_tmp *;
commit;
EOF
}

list_copyrows() {
    if [[ "$table" = "user" ]]; then
	$RUN_TARGETDB<<EOF
SELECT name, state, id FROM public.$1_tmp ut
    WHERE ut.state != 'deleted'
    AND NOT EXISTS
    (SELECT name from public.$1 u
        WHERE u.name = ut.name)
    AND NOT EXISTS
    (SELECT id from public.$1 u
        WHERE u.id = ut.id);
EOF
    elif [[ "$table" = "ldap_user" ]]; then
	$RUN_TARGETDB<<EOF
SELECT ldap_id, id FROM public.$1_tmp ut
    WHERE NOT EXISTS
    (SELECT ldap_id from public.$1 u
        WHERE u.ldap_id = ut.ldap_id)
    AND NOT EXISTS
    (SELECT id from public.$1 u
        WHERE u.id = ut.id);
EOF
    fi
}

list_omitrows() {
    echo -e "\n Will not be copied:"
    echo -e "username or id already exists:"
    if [[ "$table" = "user" ]]; then
	$RUN_TARGETDB<<EOF
SELECT DISTINCT ut.name AS name_tmp, u.name AS name_target,
ut.id AS id_temp, u.id AS id_target, ut.state AS state_tmp
  FROM public.$1_tmp ut RIGHT OUTER JOIN public.$1 u
    ON (ut.name = u.name OR ut.id = u.id);
EOF
	echo -e "state='deleted' in source:"
	$RUN_TARGETDB<<EOF
SELECT ut.name AS name_tmp, ut.id AS id_temp, ut.state AS state_tmp
  FROM public.$1_tmp ut
  WHERE ut.state = 'deleted';
EOF
    elif [[ "$table" = "ldap_user" ]]; then
	$RUN_TARGETDB<<EOF
SELECT DISTINCT ut.ldap_id AS ldap_id_tmp, u.ldap_id AS ldap_id_target,
ut.id AS id_tmp, u.id AS id_target
  FROM public.$1_tmp ut RIGHT OUTER JOIN public.$1 u
    ON (ut.ldap_id = u.ldap_id OR ut.id = u.id);
EOF
    fi
}

insert() {
    if [[ "$table" = "user" ]]; then
	$RUN_TARGETDB<<EOF
INSERT INTO public.$1
  (SELECT * FROM public.$1_tmp ut
    WHERE ut.state != 'deleted'
    AND NOT EXISTS
    (SELECT name from public.$1 u
      WHERE u.name = ut.name)
    AND NOT EXISTS
      (SELECT id from public.$1 u
       WHERE u.id = ut.id)
  );
COMMIT;
EOF
    elif [[ "$table" = "ldap_user" ]]; then
		$RUN_TARGETDB<<EOF
INSERT INTO public.$1
  (SELECT * FROM public.$1_tmp ut
    WHERE NOT EXISTS
      (SELECT ldap_id from public.$1 u
        WHERE u.ldap_id = ut.ldap_id)
    AND NOT EXISTS
      (SELECT id from public.$1 u
       WHERE u.id = ut.id)
  );
COMMIT;
EOF
    fi
}

drop_tmp() {
    $RUN_TARGETDB<<EOF
DROP TABLE IF EXISTS public.$1_tmp;
COMMIT;
EOF
}


for table in "user" "ldap_user"; do
    echo -e "\n ###### Copying table \"$table\" ######"
    echo -e "\nsourcehost: $sourcehost"
    echo -e "targethost: $targethost\n"
    echo -e "making public.${table}_tmp at targethost"
    drop_tmp $table
    mktmptable $table
    echo -e "\ncopying user at sourcehost to public.${table}_tmp at targethost"
    readsource $table |writetable $table
    list_omitrows $table
    echo -e "\nrows to be inserted:"
    list_copyrows $table
    insert $table
    drop_tmp $table
done

