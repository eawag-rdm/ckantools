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
        

mktmptable(conn_t, 'revision')
t_revision_src = readtable(conn_s, 'revision')

