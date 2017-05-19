import sqlalchemy as sqa
from sqlalchemy.sql import text
import subprocess as sp

## Supply connection parameters to databases ###############
sourcehost = "eaw-ckan-dev1.eawag.wroot.emp-eaw.ch:5432"
targethost = "eaw-ckan-db1.eawag.wroot.emp-eaw.ch:5432"
# targethost="localhost:5432"

## My passwords are managed by "pass"
passkey_src = 'eawag/postgres:ckan_default@eaw-ckan-dev1'
passkey_target = 'eawag/postgres:ckan_default@eaw-ckan-db1'
# passkey_target = 'eawag/postgres:ckan_default@localhost'
pgsourcepw = sp.check_output(['pass', passkey_src]).strip()
pgtargetpw = sp.check_output(['pass', passkey_target]).strip()
############################################################

sourceconn = ('postgresql://ckan_default:{}@{}/ckan_default'
              .format(pgsourcepw, sourcehost))
targetconn = ('postgresql://ckan_default:{}@{}/ckan_default'
              .format(pgtargetpw, targethost))

print(sourceconn)
print(targetconn)

conn_s = sqa.create_engine(sourceconn).connect()
conn_t = sqa.create_engine(targetconn).connect()

def mktmptable(conn, table):
    s = text(
        "CREATE TABLE IF NOT EXISTS {} (LIKE {} INCLUDING ALL)"
        .format(table + '_tmp', table))
    return conn.execute(s)

def readtable(conn, table):
    s = text(
        "SELECT * FROM {}".format(table))
    return conn.execute(s).fetchall()
        

res = mktmptable(conn_t, 'public.revision')
#t_revision_src = readtable(conn_s, 'revision')

t_group_source = readtable(conn_s, 'public.group')
activegroups = [x for x in t_group_source if x[5] != 'deleted']
activegroups_id = [x[0] for x in activegroups]
revids = [x[6] for x in activegroups]

t_group_revision_source = readtable(conn_s, 'public.group_revision')
# remove records with continuity_id not in activegroups
activegroup_revision = [x for x in t_group_revision_source if x[7] in activegroups_id]
activegroup_revision_revision_id = [x[6] for x in activegroup_revision]

t_group_revision_source = readtable(conn_s, 'public.group_revision')


