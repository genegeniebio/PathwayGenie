'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-few-public-methods
import sys

from Bio.Alphabet import generic_dna
from Bio.Seq import Seq
from synbiochem.utils import dna_utils, seq_utils
from synbiochem.utils.ice_utils import ICEClientFactory


class ProssOptimiser():
    '''Class to optimise designs based on PROSS output.'''

    def __init__(self, ice_parms, taxonomy_id,
                 group_names=None):
        self.__ice_client_factory = ICEClientFactory()
        self.__ice_client = \
            self.__ice_client_factory.get_ice_client(ice_parms[0],
                                                     ice_parms[1],
                                                     ice_parms[2],
                                                     group_names=group_names)

        self.__cod_opt = seq_utils.CodonOptimiser(taxonomy_id)

    def close(self):
        '''Close.'''
        self.__ice_client_factory.close()

    def generate_variants(self, template_ice_id, variants_aas):
        '''Generate variants.'''

        for variants_aa_name, variant_aa_seq in variants_aas.items():
            # Generate new variant ICEEntry:
            ice_entry = self.__ice_client.get_ice_entry(template_ice_id)
            _, cds_feat, cds_aa_seq = _get_cds_feat(ice_entry)
            var_ice_entry = ice_entry.copy()
            var_ice_entry.get_metadata()['name'] = variants_aa_name

            # Add stop-codon if missing:
            if cds_aa_seq[-1] == '*' and variant_aa_seq[-1] != '*':
                variant_aa_seq = variant_aa_seq + '*'

            var_seq = self.__mutate(ice_entry.get_seq(),
                                    cds_feat['start'],
                                    cds_aa_seq,
                                    variant_aa_seq)

            var_ice_entry.get_dna().set_seq(var_seq)

            self.__ice_client.set_ice_entry(var_ice_entry)

            assert _translate(var_ice_entry) == variant_aa_seq

    def __mutate(self, template_nucl_seq, cds_start, cds_aa_seq,
                 variant_aa_seq):
        '''Perform mutation.'''
        var_seq = template_nucl_seq

        for pos, pair in enumerate(zip(cds_aa_seq, variant_aa_seq)):
            if pair[0] != pair[1]:
                codon_start = (cds_start - 1) + pos * 3

                var_seq = \
                    var_seq[:codon_start] + \
                    self.__cod_opt.get_best_codon(pair[1]) + \
                    var_seq[codon_start + 3:]

        return var_seq


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


def _translate(var_ice_entry):
    '''Return translation.'''
    return str(Seq(var_ice_entry.get_dna()['seq']).translate())[5:]


def main(args):
    '''main method.'''
    optimiser = ProssOptimiser([args[0], args[1], args[2]], args[4], args[6:])
    optimiser.generate_variants(args[3], seq_utils.read_fasta(args[5]))
    optimiser.close()


if __name__ == '__main__':
    main(sys.argv[1:])
