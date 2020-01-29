'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from sbol import Document
from synbiochem.utils import dna_utils
from synbiochem.utils.seq_utils import get_uniprot_values


def to_query(filename):
    '''Convert SBOL documents to PartsGenie query.'''
    doc = Document()
    doc.read(filename)
    return _to_query(doc)


def _to_query(doc):
    '''Get query.'''
    query = {}
    query['app'] = 'PartsGenie'

    query['designs'] = []

    for comp_def in doc.componentDefinitions:
        if dna_utils.SO_GENE in comp_def.roles:
            query['designs'].append(_get_design(doc, comp_def))

    query['filters'] = {
        'max_repeats': 5,
        'gc_min': 0.25,
        'gc_max': 0.65,
        'local_gc_window': 50,
        'local_gc_min': 0.15,
        'local_gc_max': 0.8,
        'restr_enzs': [],
        'excl_codons': []
    }

    query['organism'] = {
        'taxonomy_id': '37762',
        'name': 'Escherichia coli',
        'r_rna': 'acctccttt'
    }

    return query


def _get_design(doc, comp_def):
    '''Get design.'''
    design = {}
    design['name'] = comp_def.displayId
    design['desc'] = comp_def.identity
    design['features'] = []

    for sub_comp_def in [doc.getComponentDefinition(c.definition)
                         for c in comp_def.components]:
        design['features'].append(_get_feature(sub_comp_def))

    # Flanking region:
    flank = {
        'typ': dna_utils.SO_ASS_COMP,
        'name': 'Sequence of defined melting temperature',
        'seq': '',
        'parameters': {
            'Tm target': 70
        },
        'temp_params': {
            'fixed': True,
            'required': ['name', 'tm'],
            'valid': True,
            'id': '_flank_id'
        }
    }

    # RBS:
    rbs = {
        'typ': dna_utils.SO_RBS,
        'name': 'RBS',
        'end': 60,
        'parameters': {
            'TIR target': 15000
        },
        'temp_params': {
            'fixed': False,
            'required': ['name', 'tir'],
            'min_end': 35,
            'max_end': 10000,
            'valid': True,
            'id': '_rbs_id'
        }
    }

    # CDS:
    uniprot_vals = get_uniprot_values([uniprot_id], ['sequence'])

    if uniprot_id not in uniprot_vals:
        raise ValueError('Uniprot id not found: %s' % uniprot_id)

    cds = {
        'typ': dna_utils.SO_CDS,
        'name': uniprot_id,
        'temp_params': {
            'fixed': False,
            'required': ['name', 'prot'],
            'valid': True,
            'id': '_cds_id',
            'aa_seq': uniprot_vals[uniprot_id]['Sequence'],
            'orig_seq': uniprot_vals[uniprot_id]['Sequence']
        },
        'desc': '',
        'links': ['http://identifiers.org/uniprot/%s' % uniprot_id]
    }

    design['features'] = [flank, rbs, cds, flank]

    return design


def _get_feature(comp_def):
    '''Get feature.'''


def main(args):
    '''main method.'''
    import json
    query = to_query(args[0])
    print(json.dumps(query, indent=4))


if __name__ == '__main__':
    main(sys.argv[1:])
