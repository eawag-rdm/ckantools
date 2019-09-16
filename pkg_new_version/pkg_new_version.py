'''
This script will generate a new version of a given package. Resources will
point to the respective URL of the original package. When unchanged
Usage:
    pkg_new_version <old_pkg_url>
    pkg_new_version -h

Arguments:
    <old_pkg_url>   URL of previous version of the data package

'''
import ckanapi
import docopt
import os
import re
import urllib

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
            newversion += int(oldversion)
        except Exception as e:
            print("\nVersion of original package doesn't follow convention.\n")
            print(e)
            raise e
    else:
        oldversion = 1
        newversion = 2
        
    del pkg['id']
    pkg['title'] = '[Version {}] '.format(str(newversion)) + pkg['title']
    name = pkg['title'].replace(' ', '_').lower()
    name = _safename(name)
    pkg['name'] = name[:99] if len(name) > 99 else name
    pkg['version'] = newversion
    for n, r in enumerate(pkg.get('resources', [])): 
        del pkg['resources'][n]['id']
        del pkg['resources'][n]['revision_id']
        pkg['resources'][n]['url_type'] = None

    return oldversion
    
def _create_new_pkg(pkg, conn):
    print(pkg['name'])
    res = conn.call_action('package_create', data_dict=pkg)
    print(res)

def _update_old_pkg_version(conn, oldid, oldversion):
    conn.call_action(
        'package_patch',
        data_dict={'id': oldid, 'version': oldversion})
        
def main(url, conn, titleprefix):
    pkg = _read_pkg(url, conn)
    oldid = pkg['id']
    oldversion = _modify_pkg(pkg, titleprefix)
    _create_new_pkg(pkg, conn)
    _update_old_pkg_version(conn, oldid, oldversion)

if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    oldurl = args['<old_pkg_url>']
    titleprefix = args['--title-prefix']
    titleprefix = titleprefix if titleprefix[-1] == ' ' else  titleprefix + ' '
    conn = _getconn(oldurl)
    main(oldurl, conn, titleprefix)

