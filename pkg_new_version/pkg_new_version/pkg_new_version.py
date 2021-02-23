'''
This script will generate a new version of a given package. Resources will
point to the respective URL of the original package. When unchanged
Usage:
    pkg_new_version [--opendata-deriv] [--exclude_res] <old_pkg_url>
    pkg_new_version -h

Arguments:
    <old_pkg_url>   URL of previous version of the data package

Options:
    --opendata-deriv, -od    

TODO: 
   + The newly introduces extras are not persistent when package is changed
     via the UI. Need to put them into schmeming.
   + "immutable" needs to be implemented
   + GUI representation of everything

'''
import ckanapi
import docopt
import os
import re

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

def _modify_pkg(pkg):
    
    def _safename(name):
        newname = ''
        for c in name:
            newname = newname + c if c in SAFENAMECHARS else newname
        return newname
    
    oldversion = pkg.get('version')
    if oldversion:
        try:
            newversion = int(oldversion) + 1
        except Exception as e:
            print("\nVersion of original package doesn't follow convention.\n")
            print(e)
            raise e
    else:
        oldversion = 1
        newversion = 2
        
    # Set root_package_id field (if not yet present)
    extras = pkg.get('extras', [])
    for e in extras:
        if e['key'] == 'root_pkg_id':
            break
    else:
        # this is a first time versioning
        extras.append({'key': 'root_pkg_id',
                       'value': pkg['id']})
    pkg['extras'] = extras
    # Make way for new id
    del pkg['id']
    # Strip previous version from title/name if present and add new version
    title = re.sub(r'\[Version \d+\] ', '', pkg['title'])
    pkg['title'] = '[Version {}] '.format(str(newversion)) + title
    name = pkg['title'].replace(' ', '_').lower()
    name = _safename(name)
    pkg['name'] = name[:99] if len(name) > 99 else name
    # Set new version field, private and status, review_level
    pkg['version'] = newversion
    pkg['private'] = True
    pkg['status'] = 'incomplete'
    pkg['review_level'] = 'none'
    pkg['reviewed_by'] = ''
    
    # Clean resources of ids and set url_type indicating link, not upload
    for n, r in enumerate(pkg.get('resources', [])): 
        del pkg['resources'][n]['id']
        del pkg['resources'][n]['revision_id']
        pkg['resources'][n]['url_type'] = None

    return extras
    
def _create_new_pkg(pkg, conn):
    try:
        res = conn.call_action('package_create', data_dict=pkg)
    except Exception as e:
        print("\nERROR: Something went wrong creating the new package\n")
        raise e

def _update_old_pkg_version(conn, oldpkgpatch):
    conn.call_action('package_patch', oldpkgpatch)

        
def main():
    args = docopt.docopt(__doc__)
    url = args['<old_pkg_url>']
    conn = _getconn(url)
    pkg = _read_pkg(url, conn)
    oldid = pkg['id']
    oldversion = pkg.get('version') or 1
    oldextras = _modify_pkg(pkg)
    _create_new_pkg(pkg, conn)
    oldextras.append({'key': 'immutable', 'value': True})
    oldpkgpatch = {'id': oldid, 'version': oldversion,
                   'extras': oldextras}
    _update_old_pkg_version(conn, oldpkgpatch)

if __name__ == '__main__':
    main()

