'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
from synbiochem.utils import dna_utils, ice_utils, seq_utils


def submit(url, username, pssword, dna, metadata):
    '''Forms SBOL document and submits to ICE.'''
    ice_client = ice_utils.ICEClient(url, username, pssword)
    ice_entry = ice_utils.ICEEntry(dna, 'PART', metadata)
    return ice_client.set_ice_entry(ice_entry)


def add_subcomp(dna, seq, start, forward=True, name=None,
                typ=None, desc=None):
    '''Adds a subcompartment.'''
    if seq is not None and len(seq) > 0:
        end = start + len(seq) - 1
        feature = dna_utils.DNA(name=name, desc=desc, typ=typ,
                                start=start, end=end, forward=forward)
        dna.features.append(feature)

        return end + 1

    return start


def get_metadata(prot_id, uniprot_id=None):
    '''Gets metadata.'''
    name = prot_id
    description = prot_id
    links = []
    parameters = []

    uniprot_vals = {}

    if uniprot_id is not None:
        uniprot_vals = seq_utils.get_uniprot_values([uniprot_id],
                                                    ['entry name',
                                                     'protein names',
                                                     'organism'])

    # Add metadata:
    if len(uniprot_vals.keys()) > 0:
        prot_id = uniprot_vals.keys()[0]
        name = uniprot_vals[prot_id]['Entry name']
        names = ', '.join(uniprot_vals[prot_id]['Protein names'])
        organism = uniprot_vals[prot_id]['Organism']
        description = names + ' (' + organism + ')'
        links.append('http://identifiers.org/uniprot/' + uniprot_id)
        parameters.append({'name': 'Organism', 'value': organism})

    metadata = {'name': name,
                'shortDescription': description,
                'links': links,
                'parameters': parameters}

    return metadata
