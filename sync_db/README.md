## sync_users.sh

Copies  users from one CKAN instance to another.

HvW @ Eawag - 2017-05-17

When username or id already exists in target,
the record is skipped. The script iterates
through tables "user" and "ldap_user".
Both have to exist on target (activate ckanext-ldap).

Set parameters by modifying variables at the beginning of the script.
