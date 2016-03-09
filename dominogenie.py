'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import itertools
import os
import sys

from synbiochem.utils.ice_utils import ICEClient
import synbiochem.utils
import synbiochem.utils.sequence_utils as seq_utils


class DominoGenie(object):
    '''DominoGenie class for designing dominoes (bridging oligos) for LCR.'''

    def __init__(self, ice_url, ice_username, ice_password):
        self.__ice_client = ICEClient(ice_url, ice_username, ice_password)

    def get_dominoes(self, design_filename, melt_temp, restrict=None):
        '''Designs dominoes (bridging oligos) for LCR.'''
        pair_oligos = {}

        with open(design_filename) as designfile:
            for line in designfile:
                line = line.split()[1:]
                line = line + [line[0]]
                pairs = [pair for pair in synbiochem.utils.pairwise(line)]
                oligos = _get_dominoes(melt_temp,
                                       [self.__get_seq(val, restrict)
                                        for val in line])
                pair_oligos.update({pair: oligo[2:]
                                    for pair, oligo in zip(pairs, oligos)})

        _write_results(pair_oligos,
                       os.path.splitext(design_filename)[0] + '_dominoes.xls')

    def __get_seq(self, seq_id, restrict):
        '''Gets sequence from sequence id, applying restriction site cleavage
        if necessary.'''
        seq = self.__ice_client.get_sequence(seq_id)

        if restrict is not None:
            seq = seq_utils.apply_restriction(seq, restrict)

        return seq


def _get_dominoes(target_melt_temp, sequences, plasmid_seq=None,
                  shuffle=False, reagent_concs=None):
    '''Designs dominoes (bridging oligos) for LCR.'''
    num_sequences = len(sequences)
    orderings = sorted([list(a) for a in
                        set(itertools.permutations(range(num_sequences)))]) \
        if shuffle else [range(num_sequences)]

    if plasmid_seq is not None:
        sequences.append(plasmid_seq)
        for ordering in orderings:
            ordering.insert(0, num_sequences)
            ordering.append(num_sequences)

    pairs = []

    for ordering in orderings:
        pairs.extend(synbiochem.utils.pairwise(ordering))

    return [_get_bridge(sequences, num_sequences, pair, target_melt_temp,
                        reagent_concs)
            for pair in sorted(set(pairs))]


def _get_bridge(sequences, num_sequences, pair, target_melt_temp,
                reagent_concs=None):
    '''Get bridging oligo for pair of sequences.'''
    reverse, reverse_tm = _get_bridge_part(sequences[pair[0]], False,
                                           target_melt_temp, reagent_concs)
    forward, forward_tm = _get_bridge_part(sequences[pair[1]], True,
                                           target_melt_temp, reagent_concs)
    return ['SEQ' + str(pair[0] + 1) if pair[0] is not num_sequences else 'P',
            'SEQ' +
            str(pair[1] + 1) if pair[1] is not num_sequences else 'P',
            reverse, forward, str(reverse_tm), str(forward_tm),
            reverse + forward
            if reverse is not None and forward is not None else '']


def _get_bridge_part(sequence, forward, target_melt_temp, reagent_concs=None):
    '''Gets half of bridging oligo.'''
    for i in range(1, len(sequence)):
        subsequence = sequence[
            :(i + 1)] if forward else sequence[-(i + 1):]
        melting_temp = seq_utils.get_melting_temp(subsequence, None,
                                                  reagent_concs)

        if melting_temp > target_melt_temp:
            return subsequence, melting_temp

    return None, -float('inf')


def _write_results(pair_oligos, filename):
    '''Writes bridging oligos to file in Excel (tabbed) format.'''
    result_file = open(filename, 'w+')

    oligo_pairs = {}

    for pair, oligo in pair_oligos.iteritems():
        result_line = '\t'.join(list(pair) + oligo)
        print result_line
        result_file.write(result_line + '\n')

        if oligo[4] not in oligo_pairs:
            oligo_pairs[oligo[4]] = [list(pair)]
        else:
            oligo_pairs[oligo[4]].append(list(pair))

    result_file.write('\n')

    for oligo, pairs in oligo_pairs.iteritems():
        result_file.write('\t'.join([oligo] + [pair[0] + '_' + pair[1]
                                               for pair in pairs]) + '\n')

    result_file.close()


def main(args):
    '''main method.'''
    domino_genie = DominoGenie(args[2], args[3], args[4])

    for filename in args[5:]:
        domino_genie.get_dominoes(filename, float(args[0]), args[1])


if __name__ == '__main__':
    main(sys.argv[1:])
