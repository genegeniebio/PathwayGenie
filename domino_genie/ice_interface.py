'''
synbiochem (c) University of Manchester 2016

synbiochem is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=no-member
from synbiochem.utils import dna_utils
from synbiochem.utils.ice_utils import ICEClient, ICEEntry


class ICEInterface(object):
    '''Class to inferface with ICE.'''

    def __init__(self, url, username, psswrd):
        self.__ice_client = ICEClient(url, username, psswrd)

    def get_dna(self, ice_id):
        '''Gets DNA object from ICE.'''
        return self.__ice_client.get_dna(ice_id)

    def submit(self, designs):
        '''Writes plasmids and dominoes to ICE.'''
        for design in designs:
            self.__write_plasmid(design)
            self.__write_dominoes(design)

    def __write_plasmid(self, design):
        '''Writes plasmids to ICE.'''
        ice_entry = ICEEntry(typ='PLASMID')
        self.__ice_client.set_ice_entry(ice_entry)
        design['ice_id'] = ice_entry.get_ice_id()

        _set_metadata(ice_entry, design['name'], ' '.join(design['design']),
                      'PLASMID')

        ice_entry.set_dna(design['plasmid'])
        self.__ice_client.set_ice_entry(ice_entry)

        # Add link from plasmid -> parts:
        for part_id in design['design']:
            self.__ice_client.add_link(design['ice_id'], part_id)

    def __write_dominoes(self, design):
        '''Writes dominoes to ICE, or retrieves them if pre-existing.'''
        seq_entries = {}

        for domino in design['dominoes']:
            seq = domino[1][0][0] + domino[1][1][0]

            if seq in seq_entries:
                ice_entry = seq_entries[seq]
            else:
                ice_entries = self.__ice_client.get_ice_entries_by_seq(seq)

                if len(ice_entries) == 0:
                    dna = _get_domino_dna('name', seq, domino[1][0][0],
                                          domino[1][1][0])
                    ice_entry = ICEEntry(dna, 'PART')
                else:
                    ice_entry = ice_entries[0]

            name, description = self.__get_metadata(ice_entry, domino[0])
            _set_metadata(ice_entry, name, description, 'DOMINO')
            self.__ice_client.set_ice_entry(ice_entry)

            # Add link from plasmid -> domino:
            self.__ice_client.add_link(
                design['ice_id'], ice_entry.get_ice_id())

            seq_entries[seq] = ice_entry

    def __get_metadata(self, ice_entry, part_ids):
        '''Gets metadata for a domino.'''
        metadata = ice_entry.get_metadata()

        # Set name if necessary:
        name = metadata['name'] if 'name' in metadata \
            else ' - '.join([self.__ice_client.get_ice_entry(prt_id).get_name()
                             for prt_id in part_ids])

        # Update Designs and Pairs in description:
        pairs = metadata['shortDescription'].split(', ') \
            if 'shortDescription' in metadata else []
        pairs.append('_'.join(part_ids))
        description = ', '.join(list(set(pairs)))

        return name, description


def _get_domino_dna(name, seq, left_subseq, right_subseq):
    '''Creates a DNA object representing a domino.'''
    dna = dna_utils.DNA(name=name, seq=seq)

    # Add annotations:
    dna.features.append(dna_utils.DNA(name='Left', start=1,
                                      end=len(left_subseq), forward=True))

    dna.features.append(dna_utils.DNA(name='Right', start=len(left_subseq) + 1,
                                      end=len(left_subseq) + len(right_subseq),
                                      forward=True))

    return dna


def _set_metadata(ice_entry, name, description, typ):
    '''Sets key metadata values for ICE entry.'''
    ice_entry.set_value('name', name)
    ice_entry.set_value('status', 'Complete')
    ice_entry.set_value('creator', 'SYNBIOCHEM')
    ice_entry.set_value('creatorEmail', 'support@synbiochem.co.uk')
    ice_entry.set_value('principalInvestigator', 'SYNBIOCHEM')
    ice_entry.set_value(
        'principalInvestigatorEmail', 'support@synbiochem.co.uk')
    ice_entry.set_value('shortDescription', description)
    ice_entry.set_value('parameters', [{'name': 'Type',
                                        'value': typ}])
