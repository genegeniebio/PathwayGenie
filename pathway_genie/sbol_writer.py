'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from synbiochem.utils import dna_utils, ice_utils


def submit(url, username, pssword, dna):
    '''Forms SBOL document and submits to ICE.'''
    ice_client = ice_utils.ICEClient(url, username, pssword)

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

    return ice_client.set_ice_entry(ice_entry)


def _add_params(ice_entry, dna):
    '''Adds parameter values to ICEENtry.'''
    for key, value in dna['parameters'].iteritems():
        ice_entry.set_parameter(key, value)
