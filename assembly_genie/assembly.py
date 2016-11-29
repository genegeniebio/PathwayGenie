'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys
from synbiochem.utils.ice_utils import ICEClient


def export_order(url, username, password, ice_ids):
    '''Exports a plasmids constituent parts for ordering.'''
    ice_client = ICEClient(url, username, password)
    entries = {}

    for ice_id in ice_ids:
        data = get_data(ice_id, ice_client)

        for part in data[0].get_metadata()['linkedParts']:
            data = get_data(part['partId'], ice_client)
            entries[data[1]] = data[2:]

    for entry_id, entry in entries.iteritems():
        print '\t'.join([entry_id] + [str(item) for item in entry])


def get_data(ice_id, ice_client):
    '''Gets data from ICE entry.'''
    ice_entry = ice_client.get_ice_entry(ice_id)
    metadata = ice_entry.get_metadata()

    return ice_entry, \
        metadata['partId'], \
        metadata['name'], \
        metadata['type'], \
        ice_entry.get_parameter('Type'), \
        ice_entry.get_seq()


def main(args):
    '''main method.'''
    export_order(args[0], args[1], args[2], args[3:])


if __name__ == '__main__':
    main(sys.argv[1:])
