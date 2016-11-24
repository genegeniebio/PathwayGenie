'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from synbiochem.utils import seq_utils
import synbiochem.utils


def get_dominoes(target_melt_temp, sequences, reagent_concs=None):
    '''Designs dominoes (bridging oligos) for LCR.'''
    return [_get_domino(pair, target_melt_temp, reagent_concs)
            for pair in synbiochem.utils.pairwise(sequences)]


def _get_domino(pair, target_melt_temp, reagent_concs=None):
    '''Get bridging oligo for pair of sequences.'''
    return (seq_utils.get_seq_by_melt_temp(pair[0], target_melt_temp, False,
                                           reagent_concs),
            seq_utils.get_seq_by_melt_temp(pair[1], target_melt_temp,
                                           reagent_concs))
