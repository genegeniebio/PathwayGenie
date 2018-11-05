'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=invalid-name
# pylint: disable=wrong-import-order
from synbiochem.utils.ice_utils import get_ice_id

import pandas as pd


def export(ice_client, data):
    '''Export.'''
    source = 'plasmid' \
        if data[0]['typ'] == 'http://purl.obolibrary.org/obo/SO_0000637' \
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
    return df[['Part ID', 'Cloned ICE ID', 'Name', 'Sequence', 'Description']]


def _export_dominoes(ice_client, data):
    '''Export dominoes.'''
    all_parts = [ice_client.get_ice_entry(
        entry['ice_ids']['plasmid']['ice_id']).get_metadata()['linkedParts']
        for entry in data]

    parts = [[part['partId'],
              ice_client.get_ice_entry(part['partId']).get_seq(),
              part['name'], part['shortDescription']]
             for parts in all_parts
             for part in parts]

    return pd.DataFrame(parts, columns=['Part ID', 'Sequence', 'Name',
                                        'Description'])


def _get_ice_id(link, idx):
    '''Get ICE id.'''
    if idx < len(link):
        return get_ice_id(link[idx].split('/')[-1])

    return None
