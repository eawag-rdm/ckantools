#!/bin/bash

set -e
set -u

sourcehost="eaw-ckan-dev1.eawag.wroot.emp-eaw.ch:5432"
pgsourcepw=`pass eawag/postgres:ckan_default@eaw-ckan-dev1`
targethost="eaw-ckan-db1.eawag.wroot.emp-eaw.ch:5432"
pgtargetpw=`pass eawag/postgres:ckan_default@eaw-ckan-db1`
# targethost="localhost:5432"
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
    $RUN_TARGETDB<<EOF
SELECT name, state, id FROM public.$1_tmp ut
WHERE ut.state != 'deleted' AND NOT EXISTS
(SELECT name from public.$1 u
 WHERE u.name = ut.name) AND NOT EXISTS
(SELECT id from public.$1 u
 WHERE u.id = ut.id);
EOF
}

insert() {
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
}

drop_tmp() {
    $RUN_TARGETDB<<EOF
DROP TABLE IF EXISTS public.$1_tmp;
COMMIT;
EOF
}

table="user"
table="ldap_user"
echo $targetconn
#clear_tmp
echo -e "\nsourcehost: $sourcehost"
echo -e "targethost: $targethost\n"
echo -e "making public.${table}_tmp at targethost"
mktmptable $table
echo -e "\ncopying user at sourcehost to public.${table}_tmp at targethost"
readsource $table |writetable $table
 
echo -e "\nrows to be inserted:"
list_copyrows $table
insert $table
drop_tmp $table

