'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from sbol import Document
from synbiochem.utils.seq_utils import get_uniprot_values

_CDS_SO = 'http://identifiers.org/so/SO:0000316'


def to_query(filenames):
    '''Convert SBOL documents to PartsGenie query.'''
    docs = _parse(filenames)
    uniprot_docs = _get_uniprot_docs(docs)
    return _to_query(uniprot_docs)


def _parse(filenames):
    '''Parse SBOL documents.'''
    docs = [Document() for _ in filenames]

    for doc, filename in zip(docs, filenames):
        doc.read(filename)

    return docs


def _get_uniprot_docs(docs):
    '''Get uniprot docs.'''
    uniprot_docs = {}

    for doc in docs:
        for comp_def in doc.componentDefinitions:
            if _CDS_SO in comp_def.roles:
                uniprot_docs[comp_def.description] = comp_def.identity

    return uniprot_docs


def _to_query(uniprot_docs):
    '''Get query.'''
    query = {}
    query['app'] = 'PartsGenie'

    query['designs'] = []

    for uniprot_id, sbol_comp_def in uniprot_docs.items():
        try:
            query['designs'].append(_get_design(uniprot_id, sbol_comp_def))
        except ValueError:
            pass

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


def _get_design(uniprot_id, sbol_comp_def):
    '''Get design.'''
    design = {}
    design['name'] = 'Part'
    design['desc'] = sbol_comp_def

    # Flanking region:
    flank = {
        'typ': 'http://purl.obolibrary.org/obo/SO_0000143',
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
        'typ': 'http://purl.obolibrary.org/obo/SO_0000139',
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
        'typ': 'http://purl.obolibrary.org/obo/SO_0000316',
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


def main(args):
    '''main method.'''
    import json
    query = to_query(args)
    print(json.dumps(query, indent=4))


if __name__ == '__main__':
    main(sys.argv[1:])
