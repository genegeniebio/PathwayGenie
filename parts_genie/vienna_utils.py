'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
import RNA

from parts_genie import nupack_utils


def run(cmd, sequences, temp, dangles, energy_gap=None, bp_x=None, bp_y=None):
    '''Runs ViennaRNA.'''
    if cmd == 'mfe':
        return _mfe(sequences, temp, dangles)

    if cmd == 'subopt':
        return _subopt(sequences, energy_gap, temp, dangles)

    if cmd == 'energy':
        return _energy(sequences, bp_x, bp_y, temp, dangles)

    return None


def _mfe(sequences, temp=37.0, dangles='some'):
    '''mfe.'''
    model = RNA.md()
    model.temperature = temp
    model.dangles = _get_dangles(dangles)
    result = map(list, zip(*[RNA.fold_compound(sequence, model).mfe()
                             for sequence in sequences]))

    bp_xs, bp_ys = _get_numbered_pairs(result[0])

    return result[1], bp_xs, bp_ys


def _subopt(sequences, energy_gap, temp=37.0, dangles='some'):
    '''subopt.'''
    model = RNA.md()
    model.temperature = temp
    model.dangles = _get_dangles(dangles)
    return [RNA.fold_compound(sequence, model).subopt(energy_gap)[1]
            for sequence in sequences]


def _energy(sequences, bp_xs, bp_ys, temp=37.0, dangles='some'):
    '''energy.'''
    model = RNA.md()
    model.temperature = temp
    model.dangles = _get_dangles(dangles)
    structure = '&'.join([_get_brackets(len(seq), bp_x, bp_y)
                          for seq, bp_x, bp_y in zip(sequences, bp_xs, bp_ys)])

    return [RNA.fold_compound(sequence, model).eval_structure(structure)[1]
            for sequence in sequences]


def _get_dangles(dangles):
    '''Get dangles.'''
    return 0 if dangles == 'none' else 1 if dangles == 'some' else 2


def _get_numbered_pairs(bracket_strs):
    '''_get_numbered_pairs'''
    all_bp_x = []
    all_bp_y = []

    for bracket_str in bracket_strs:
        bp_x = []
        bp_y = [None for _ in range(bracket_str.count(')'))]
        last_nt_x = []

        for pos, letter in enumerate(bracket_str):
            if letter == '(':
                bp_x.append(pos)
                last_nt_x.append(pos)

            elif letter == ')':
                nt_x = last_nt_x.pop()
                nt_x_pos = bp_x.index(nt_x)
                bp_y[nt_x_pos] = pos

        all_bp_x.append([pos + 1 for pos in bp_x])
        all_bp_y.append([pos + 1 for pos in bp_y])

    return all_bp_x, all_bp_y


def _get_brackets(seq_len, bp_x, bp_y):
    '''_get_brackets'''
    bp_x = [pos - 1 for pos in bp_x]
    bp_y = [pos - 1 for pos in bp_y]

    return ''.join(['(' if pos in bp_x
                    else ')' if pos in bp_y
                    else '.'
                    for pos in range(seq_len)])


m_rna = 'AGGGGGGATCTCCCCCCAAAAAATAAGAGGTACACATGACTAAAACTTTCAAAGGCTCAGTATT' + \
    'CCCACT'
print run('mfe', [m_rna], temp=37.0, dangles='none')
print nupack_utils.run('mfe', [m_rna], temp=37.0, dangles='none')
