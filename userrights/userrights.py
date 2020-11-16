"""userrights

Usage:
  user_rights [-k APIKEY] [-s SERVER] <permission> <username>
  user_rights (-h | --help)

Options:
  -h --help             Show this help.
  -k --apikey=APIKEY    CKAN API-Key. Either the key itself or an environment variable containing the key. [default: CKAN_APIKEY_PROD1]
  -s --server=SERVER    The CKAN server. [default: https://data.eawag.ch]

Arguments:
  <permission>         One of "read", "create_dataset", "admin"

"""
import os
import ckanapi
from docopt import docopt

class UserRights(object):
    def __init__(self, args):
        print(args)
        apikeyinput = args.get('--apikey')
        self.apikey = self.getapikey(apikeyinput) if apikeyinput else None
        self.conn = ckanapi.RemoteCKAN(args['--server'], self.apikey)
        self.user = args['<username>']
        self.permission = args['<permission>']
        

    def getapikey(self, apikeyin):
        try:
            apikey = os.environ[apikeyin]
        except KeyError:
            apikey = apikeyin
        return apikey

    def main(self):
        res = self.conn.call_action(
            'organization_list_for_user',
            data_dict={'id': self.user,
                       'permission': self.permission})
        print(res)
        
if __name__ == '__main__':
    args = docopt(__doc__)
    ur=UserRights(args)
    ur.main()
