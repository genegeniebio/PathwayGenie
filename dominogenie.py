'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''

from synbiochem.utils import sequence_utils

import synbiochem.utils


def get_dominoes(target_melt_temp, sequences, reagent_concs=None):
    '''Designs dominoes (bridging oligos) for LCR.'''
    return [_get_domino(pair, target_melt_temp, reagent_concs)
            for pair in synbiochem.utils.pairwise(sequences)]


def _get_domino(pair, target_melt_temp, reagent_concs=None):
    '''Get bridging oligo for pair of sequences.'''
    return (_get_domino_part(pair[0], False, target_melt_temp, reagent_concs),
            _get_domino_part(pair[1], True, target_melt_temp, reagent_concs))


def _get_domino_part(sequence, forward, target_melt_temp, reagent_concs=None):
    # TODO: replace with sequence_utils.get_seq_by_melt_temp
    '''Gets half of bridging oligo.'''
    for i in range(1, len(sequence)):
        subsequence = sequence[:(i + 1)] if forward else sequence[-(i + 1):]
        melting_temp = sequence_utils.get_melting_temp(subsequence, None,
                                                       reagent_concs)

        if melting_temp > target_melt_temp:
            return subsequence, melting_temp

    return None, -float('inf')
