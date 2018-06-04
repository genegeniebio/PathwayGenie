'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from Bio.Alphabet import generic_dna
from Bio.Seq import Seq
from synbiochem.utils import dna_utils, ice_utils, seq_utils


def generate_variants(ice_url, ice_username, ice_password,
                      template_ice_id, taxonomy_id, variants_aas,
                      group_names=None):
    '''Generate variants.'''
    cod_opt = seq_utils.CodonOptimiser(taxonomy_id)

    ice_client = ice_utils.ICEClient(ice_url, ice_username, ice_password,
                                     group_names=group_names)

    for variants_aa_name, variant_aa_seq in variants_aas.iteritems():
        # Generate new variant ICEEntry:
        ice_entry = ice_client.get_ice_entry(template_ice_id)
        _, cds_feat, cds_aa_seq = _get_cds_feat(ice_entry)
        var_ice_entry = ice_entry.copy()
        var_ice_entry.get_metadata()['name'] = variants_aa_name

        # Add stop-codon if missing:
        if cds_aa_seq[-1] == '*' and variant_aa_seq[-1] != '*':
            variant_aa_seq = variant_aa_seq + '*'

        _mutate(var_ice_entry,
                ice_entry.get_seq(),
                cds_feat['start'],
                cds_aa_seq,
                variant_aa_seq,
                cod_opt)

        ice_client.set_ice_entry(var_ice_entry)

        assert _translate(var_ice_entry) == variant_aa_seq


def _get_cds_feat(ice_entry):
    '''Get CDS feature from entry.'''
    # Get index and CDS feature:
    resp = [[idx, feat]
            for idx, feat in enumerate(ice_entry.get_dna()['features'])
            if feat['typ'] == dna_utils.SO_CDS]

    assert len(resp) == 1

    nucl_seq = ice_entry.get_seq()
    cds_nucl_seq = nucl_seq[resp[0][1]['start'] - 1:resp[0][1]['end']]
    cds_aa_seq = str(Seq(cds_nucl_seq, generic_dna).translate())

    return resp[0][0], resp[0][1], cds_aa_seq


def _mutate(var_ice_entry, template_nucl_seq, cds_start, cds_aa_seq,
            variant_aa_seq, cod_opt):
    '''Perform mutation.'''
    var_seq = template_nucl_seq

    for pos, pair in enumerate(zip(cds_aa_seq, variant_aa_seq)):
        if pair[0] != pair[1]:
            codon_start = (cds_start - 1) + pos * 3

            var_seq = \
                var_seq[:codon_start] + \
                cod_opt.get_best_codon(pair[1]) + \
                var_seq[codon_start + 3:]

    var_ice_entry.get_dna().set_seq(var_seq)


def _translate(var_ice_entry):
    '''Return translation.'''
    return str(Seq(var_ice_entry.get_dna()['seq']).translate())[5:]


def main(args):
    '''main method.'''
    generate_variants(args[0], args[1], args[2],
                      args[3], args[4],
                      seq_utils.read_fasta(args[5]),
                      args[6:])


if __name__ == '__main__':
    main(sys.argv[1:])
