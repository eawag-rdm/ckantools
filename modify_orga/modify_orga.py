import ckanapi
import os
import re
from pprint import pprint

APK = os.environ['CKAN_APIKEY']
HOST = 'http://localhost:5000'

ck = ckanapi.RemoteCKAN(HOST, APK)

# Automated modifications to 'organization'

def make_homepage(ck, name):
    """
    Extracts homepage URL from description and inserts as
    field 'homepage', Removes homepage-reference
    from description.
    
    """
    print('make_homepage: Modifying {}'.format(name))
    o = ck.call_action('organization_show',
                       {'id': name})
    description0 = o.get('description')
    
    homepage0 = o.get('homepage')
    m = re.search(r'(\r\n)*\[Homepage\]\((?P<url>.*)\)', description0)
    try:
        homepage1 = m.group('url')
    except AttributeError:
        homepage1 = None
    if homepage1 is not None:
        print('   moving {}'.format(homepage1))
        description1 = description0.replace(m.group(), '')
        ck.call_action('organization_patch', data_dict=
                       {'id': name,
                        'homepage': homepage1,
                        'description': description1
                        })
        
def print_orga(ck, name):
    o = ck.call_action('organization_show', {'id': name})
    pprint(o)

def remove_field(ck, name, field):
    o = ck.call_action('organization_show', {'id': name})
    try:
        del o[field]
    except KeyError:
        print('\nCan not delete field {} - does not exist.'.format(field))
    ck.call_action('organization_update', o)


orga = 'fish-genomics'
print_orga(ck, orga)
remove_field(ck, orga, 'shortname')
# allorgas = ck.call_action('organization_list')
# for name in allorgas:
#     make_homepage(ck, name)

