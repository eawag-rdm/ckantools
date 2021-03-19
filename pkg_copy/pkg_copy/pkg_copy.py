'''
This script will generate a copy of a given package. Resources will be omitted.
New title ist take from STDIN.
Usage:
    pkg_copy <old_pkg_url>
    pkg_copy -h

Arguments:
    <old_pkg_url>   URL of source data package

'''
import ckanapi
import docopt
import os
import re
import sys
import copy

APIKEY = os.environ['CKAN_APIKEY_PROD1']
HOSTPAT = re.compile(r'^(https?://[^/]+\.[^/]+).*$')
SAFENAMECHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_-'

def _getconn(url):
    host = re.match(HOSTPAT, url)
    try:
        host = host.group(1)
    except Exception as e:
        print("\nERROR: Can't figure out host for {}\n".format(url))
        raise e
    conn = ckanapi.RemoteCKAN(host, APIKEY)
    return conn

def _read_pkg(url, conn):
    ds_name = url.rsplit('/', 1)[1]
    pkg = conn.call_action('package_show', data_dict={'id': ds_name})
    return pkg

def _modify_pkg(origpkg, title):
    
    def _safename(name):
        newname = ''
        for c in name:
            newname = newname + c if c in SAFENAMECHARS else '_'
        return newname

    ## New title, remove id
    pkg = copy.deepcopy(origpkg)
    pkg['title'] = title
    name = pkg['title'].replace(' ', '_').lower()
    name = _safename(name)
    del pkg['id']
    pkg['name'] = name[:99] if len(name) > 99 else name
    
    # Set new status, review_level
    pkg['status'] = 'incomplete'
    pkg['review_level'] = 'none'
    pkg['reviewed_by'] = ''
    
    # remove ressources
    del pkg['resources']
                          
    return pkg

def _create_new_pkg(pkg, conn):
    try:
        res = conn.call_action('package_create', data_dict=pkg)
    except Exception as e:
        print("\nERROR: Something went wrong creating the new package\n")
        raise e

def read_titles():
    titles = sys.stdin.readlines()
    titles = [t.strip() for t in titles]
    return titles

def create_dummy_resource(conn, pkg_id):
    conn.call_action('resource_create',
                     data_dict={'package_id': pkg_id,
                                'resource_type': 'Other',
                                'restricted_level': 'public',
                                'name': 'dummy',
                                'url': 'https://eawag.ch'
                                })

def main():
    args = docopt.docopt(__doc__)
    url = args['<old_pkg_url>']
    titles = read_titles()
    conn = _getconn(url)
    origpkg = _read_pkg(url, conn)
    for title in titles:
        newpkg = _modify_pkg(origpkg, title)
        print('before create {}'.format(newpkg['name']))
        _create_new_pkg(newpkg, conn)
        newid = newpkg['name']
        create_dummy_resource(conn, newid)


if __name__ == '__main__':
    main()

