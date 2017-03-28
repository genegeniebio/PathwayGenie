'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from synbiochem.utils import dna_utils, ice_utils


class DNAWriter(object):
    '''Class for writing DNA objects to ICE.'''

    def __init__(self, url, username, pssword, group_names):
        self.__ice_client = ice_utils.ICEClient(url, username, pssword,
                                                group_names=[group_names])

    def submit(self, dna):
        '''Submits DNA to ICE (or checks for existing entry.'''
        ice_entries = self.__ice_client.get_ice_entries_by_seq(dna['seq'])

        if len(ice_entries):
            return ice_entries[0].get_ice_id()
        else:
            return self.__write(dna)

    def __write(self, dna):
        '''Writes DNA document to ICE.'''
        typ = 'PLASMID' if dna.get('typ', None) == dna_utils.SO_PLASMID \
            else 'PART'

        ice_entry = ice_utils.ICEEntry(dna, typ)

        ice_entry.set_value('name', dna['name'])
        ice_entry.set_value('shortDescription', dna['desc'])

        _add_params(ice_entry, dna)
        links = set(dna['links'])

        for feature in dna['features']:
            _add_params(ice_entry, feature)
            links |= set(feature['links'])

        ice_entry.set_value('links', list(links))

        entry_id = self.__ice_client.set_ice_entry(ice_entry)

        for child in dna['children']:
            par_ice_entry = self.submit(child)
            self.__ice_client.add_link(entry_id, par_ice_entry)

        return entry_id


def _add_params(ice_entry, dna):
    '''Adds parameter values to ICEENtry.'''
    for key, value in dna['parameters'].iteritems():
        param = ice_entry.get_parameter(key)
        ice_entry.set_parameter(key, (value if param is None
                                      else ', '.join([param, value])))
