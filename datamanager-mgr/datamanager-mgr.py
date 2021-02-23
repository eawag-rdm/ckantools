"""datamanager-mgr

Lists the Datamangers for all organizations.

Usage: datamanger-mgr [-s HOST] [-a]
       datamanger-mgr [-s HOST] -e [-t TEMPLATE]
       datamanger-mgr [-h]

Options:
-s HOST           The URL of the host to use [default: https://data.eawag.ch]
-a                Only return list of emails. # not implemented
-h                This help.
-e                Create emails # not implemented
-t TEMPLATE       Email based on TEMPLATE. [default: ./email.tmpl] # not implemented

"""

import ckanapi
from docopt import docopt
import logging
import os
import sys
import csv

logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.WARNING)

NO_SKIP_DEPARTMENTS = ['communications-department', 'ecotox-centre-eawag-epfl',
                       'gis-services', 'research-data-management',
                       'urban-water-management']
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
        dmrecords = {}
        if not self.orgas:
            self.lg.error('No or empty list of organizations.')
            raise Exception('List of organizations is empty')
        
        for o in self.orgas:
            if not o.get('groups') and o['name'] not in NO_SKIP_DEPARTMENTS:
                self.lg.info('Skipping department {}'.format(o['display_name']))
                continue
            datamanager = self.conn.call_action(
                'user_show',data_dict={'id': o['datamanager']})
            try:
                department = self.conn.call_action(
                    'organization_show', data_dict={'id': o['groups'][0]['name']})
            except IndexError:
                department = o
                
            dmrecords[o['name']] = {'datamanager': datamanager,
                                    'orga': o,
                                    'department': department}
        self.lg.info('{} "real" organizations remaining'
                     .format(len(dmrecords)))

        # for user, orga in zip(dmlist, self.orgas):
        #     dmrecords.append(
        #         {'orga_name': orga['name'],
        #          'orga_display_name': orga['display_name'],
        #          'dm_name': user['name'],
        #          'dm_display_name': user['display_name']}
        #     )
        return dmrecords

    def _render_table(self):
        dmlist = sorted(self.dmrecords.values(),
                        key=lambda dm: dm['department']['name'])

        writer = csv.writer(sys.stdout, dialect='excel')
        writer.writerow(['DEPARTMENT','DEPARTMENT_NORMNAME','GROUP','GROUP_NORMNAME','DATAMANAGER_FULLNAME',
                         'DATAMANAGER_USERNAME','DATAMANAGER_EMAIL'])
        
        for dm in dmlist:
            writer.writerow([dm['department']['display_name'],
                             dm['department']['name'],
                             dm['orga']['display_name'],
                             dm['orga']['name'],
                             dm['datamanager']['display_name'],
                             dm['datamanager']['name'],
                             dm['datamanager']['email']])
        
    # To be implemented
    def _send_emails(self, templatefile):
        pass
        
    def main(self):
        if not self.args['-e']:
            self._render_table()
        else:
            self._send_emails(self.args['-t'])
        

if __name__ == '__main__':
    args = docopt(__doc__)
    dm = DatamanagerMgr(args)
    dm.main()
    
    

