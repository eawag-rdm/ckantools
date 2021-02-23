# _*_ coding: utf-8 _*_

''' package_update
Usage:
  package_update <record>

'''

import ckanapi
import os
from docopt import docopt
import json

host = "http://localhost:5000"
apikey = os.environ.get('CKAN_APIKEY')



if __name__ == '__main__':
    args = docopt(__doc__)
    with open(args.get('<record>'), 'r') as record:
        newpack = json.load(record)
    conn = ckanapi.RemoteCKAN(host, apikey=apikey)
    conn.call_action('package_update', data_dict=newpack)
        

    
