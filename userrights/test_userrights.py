import userrights
import os
import pytest
import requests

defaultargs = {'--apikey': 'CKAN_APIKEY_PROD1', '--server': '',
               '<username>': '', '<permission>': ''}

def test_getapikey():
    ur = userrights.UserRights(defaultargs)
    assert(ur.apikey == os.environ['CKAN_APIKEY_PROD1'])
    args = defaultargs.update({'--apikey': 'glitschigerapikey'})
    ur = userrights.UserRights(defaultargs)
    assert(ur.apikey == 'glitschigerapikey')
    defaultargs.update({'somethingelse': 'glitschigerapikey'})
    del defaultargs['--apikey']
    ur = userrights.UserRights(defaultargs)
    assert(ur.apikey is None)

def test_connection():
    defaultargs.update({'--server': 'http://not.a.server'})
    ur = userrights.UserRights(defaultargs)
    with pytest.raises(requests.ConnectionError):
        status = ur.conn.call_action('get_status')
    defaultargs.update({'--server': 'https://data.eawag.ch'})
    ur = userrights.UserRights(defaultargs)
    status = ur.conn.call_action('status_show')
    assert(status['site_url'] == 'https://data.eawag.ch')

