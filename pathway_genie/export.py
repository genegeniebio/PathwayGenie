'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=consider-using-set-comprehension
# pylint: disable=invalid-name
# pylint: disable=wrong-import-order
from synbiochem.utils import dna_utils
from synbiochem.utils.ice_utils import get_ice_id

import pandas as pd


def export(ice_client, data):
    '''Export.'''
    source = 'plasmid' \
        if data[0]['typ'] == dna_utils.SO_PLASMID \
        else 'parts'

    if source == 'plasmid':
        return _export_dominoes(ice_client, data)

    # else assume parts:
    return _export_parts(data)


def _export_parts(data):
    '''Export parts.'''
    df = pd.DataFrame(data)
    df.rename(columns={'name': 'Name',
                       'seq': 'Sequence',
                       'desc': 'Description'}, inplace=True)

    # Get ICE ids:
    df['Part ID'] = df['links'].apply(lambda link: _get_ice_id(link, 0))
    df['Cloned ICE ID'] = df['links'].apply(lambda link: _get_ice_id(link, 1))

    # Return selected columns:
    df = df[['Part ID', 'Cloned ICE ID', 'Name', 'Sequence', 'Description']]
    df.name = 'parts'
    return [df]


def _export_dominoes(ice_client, data):
    '''Export dominoes.'''
    design_id = '_'.join(list(set([plasmid['parameters']['Design id']
                                   for plasmid in data])))

    all_parts = [ice_client.get_ice_entry(
        entry['ice_ids']['plasmid']['ice_id']).get_metadata()['linkedParts']
        for entry in data]

    part_data = set([(part['partId'], part['name'], part['shortDescription'])
                     for parts in all_parts for part in parts])

    parts = [list(part) + _get_ice_data(ice_client, part[0])
             for part in part_data]

    dominoes_df = pd.DataFrame(parts, columns=['Part ID', 'Name',
                                               'Description', 'Sequence',
                                               'Type'])

    dominoes_df = dominoes_df.sort_values(by=['Type', 'Part ID'])
    dominoes_df.name = design_id + '_export'

    mapping_df = pd.DataFrame([[plasmid['name'],
                                plasmid['ice_ids']['part']['ice_id']]
                               for plasmid in data], columns=['Name', 'ICE'])

    mapping_df.name = design_id + '_export_mapping'

    return [dominoes_df, mapping_df]


def _get_ice_id(link, idx):
    '''Get ICE id.'''
    if idx < len(link):
        return get_ice_id(link[idx].split('/')[-1])

    return None


def _get_ice_data(ice_client, ice_id):
    '''Get ICE data.'''
    ice_entry = ice_client.get_ice_entry(ice_id)

    metadata = ice_entry.get_metadata()

    typ = None

    if 'parameters' in metadata:
        types = [parameter['value']
                 for parameter in metadata['parameters']
                 if parameter['name'] == 'Type']

        if types:
            typ = types[0]

    return [ice_entry.get_seq(), typ]
