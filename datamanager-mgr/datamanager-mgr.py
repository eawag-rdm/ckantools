"""datamanager-mgr

Lists the Datamangers for all organizations.

Usage: datamanger-mgr [-s HOST] [-a]
       datamanger-mgr [-s HOST] -e [-t TEMPLATE]]
       datamanger-mgr [-h]

Options:
    -s HOST           The URL of the host to use [default: https://data.eawag.ch]
    -a                Only return list of emails.
    -h                This help.
    -e                Create emails
    -t TEMPLATE       Email based on TEMPLATE. [default: ./email.tmpl]
"""

import ckanapi
from docopt import docopt
import logging
import os
import sys

#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.WARNING)

class DatamanagerMgr:
    def __init__(self, args):
        self.lg = logging.getLogger(name=self.__class__.__name__)
        self.args = args
        self.host = args['-s']
        self.conn = self._conn()
        self.orgas = self._get_organizations()
        self.dmrecords = self._mk_dm_records()
        
    def _getapikey(self, host):
        if host == 'https://data.eawag.ch':
            return os.environ['CKAN_APIKEY_PROD1']
        else:
            self.lg.warning('No API-key for {} found. Limited functionality'
                        .format(host))

    def _conn(self, host=None):
        host = host or self.host
        conn = ckanapi.RemoteCKAN(host, apikey=self._getapikey(host))
        return conn

    def _get_organizations(self):
        self.lg.info('Retrieving organizations from {}'.format(self.host))
        orgas = self.conn.call_action(
            'organization_list',
            data_dict={'all_fields': True,
                       'include_extras': True,
                       'include_groups': True,
                       'include_users': False}
        )
        self.lg.info('Found {} organizations'.format(len(orgas)))
        return orgas

    def _mk_dm_records(self):
        dmrecords = []
        if not self.orgas:
            self.lg.error('No or empty list of organizations.')
            raise Exception('List of organizations is empty')
        
        dmlist = []
        for o in self.orgas:
            if not o.get('groups'):
                self.lg.info('Skipping department {}'.format(o['display_name']))
                continue
            dmlist.append(self.conn.call_action(
                'user_show',data_dict={'id': o['datamanager']})
            )
        self.lg.info('{} "real" organizations remaining'
                     .format(len(dmlist)))

        for user, orga in zip(dmlist, self.orgas):
            dmrecords.append(
                {'orga_name': orga['name'],
                 'orga_display_name': orga['display_name'],
                 'dm_name': user['name'],
                 'dm_display_name': user['display_name']}
            )
        return dmrecords
    
    def _render_table(self):
        for dmrec in self.dmrecords:
            print('{}\t{}\t{}\t{}'.format(dmrec['orga_name'],
                                          dmrec['orga_display_name'],
                                          dmrec['dm_name'],
                                          dmrec['dm_display_name'])
            )
        
    def _send_emails(self, templatefile):
        
        

        
    def main(self):
        if not self.args['-e']:
            self._render_table()
        else:
            self._send_emails(self.args['-t'])
        

if __name__ == '__main__':
    args = docopt(__doc__)
    dm = DatamanagerMgr(args)
    dm.main()
    
    

