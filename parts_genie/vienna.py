'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import os.path
import popen2
import random
import re
import string
import time


_TMP_DIR = os.path.dirname(os.path.abspath(__file__)) + '/tmp'

if not os.path.exists(_TMP_DIR):
    os.mkdir(_TMP_DIR)


class ViennaRNA(dict):
    '''Class to encapsulate Vienna RNA.'''
    debug_mode = 0
    RT = 0.61597  # gas constant times 310 Kelvin (in units of kcal/mol)

    def __init__(self, sequence_list, material='rna37'):

        self.ran = 0

        exp = re.compile('[ATGCU]', re.IGNORECASE)

        for seq in sequence_list:
            if not exp.match(seq):
                error_string = 'Invalid letters found in inputted ' + \
                    'sequences. Only ATGCU allowed. \n Sequence is \'' + \
                    str(seq) + '\'.'
                raise ValueError(error_string)

        self['sequences'] = sequence_list
        self['material'] = material

        random.seed(time.time())
        long_id = ''.join(
            [random.choice(string.letters + string.digits) for _ in range(10)])
        self.prefix = _TMP_DIR + '/temp_' + long_id

    def mfe(self, strands, temp=37.0, dangles='all'):
        '''mfe.'''
        self['mfe_composition'] = strands

        assert temp > 0

        seq_string = '&'.join(self['sequences'])
        input_string = seq_string + '\n'

        handle = open(self.prefix, 'w')
        handle.write(input_string)
        handle.close()

        # Set arguments
        if dangles == 'none':
            dangles = ' -d0 '
        elif dangles == 'some':
            dangles = ' -d1 '
        elif dangles == 'all':
            dangles = ' -d2 '

        # Call ViennaRNA C programs
        cmd = 'RNAcofold'
        args = dangles + ' < ' + self.prefix

        output = popen2.Popen3(cmd + args)

        while output.poll() < 0:
            try:
                output.wait()
                time.sleep(0.001)
            except Exception:
                break

        # Skip the unnecessary output lines
        output.fromchild.readline()

        line = output.fromchild.readline()
        words = line.split(' ')
        bracket_string = words[0]
        (strands, bp_x, bp_y) = _get_numbered_pairs(bracket_string)

        energy = float(
            words[len(words) - 1].replace(')', '').replace('(', '').strip())

        self._cleanup()
        self['program'] = 'mfe'
        self['mfe_basepairing_x'] = [bp_x]
        self['mfe_basepairing_y'] = [bp_y]
        self['mfe_energy'] = [energy]
        self['totalnt'] = strands

    def subopt(self, strands, energy_gap, temp=37.0, dangles='all',
               output_ps=False):
        '''subopt.'''
        self['subopt_composition'] = strands

        assert temp > 0

        seq_string = '&'.join(self['sequences'])
        input_string = seq_string + '\n'

        handle = open(self.prefix, 'w')
        handle.write(input_string)
        handle.close()

        # Set arguments
        if dangles == 'none':
            dangles = ' -d0 '
        elif dangles == 'some':
            dangles = ' -d1 '
        elif dangles == 'all':
            dangles = ' -d2 '

        # Call ViennaRNA C programs
        cmd = 'RNAsubopt'
        args = ' -e ' + str(energy_gap) + ' < ' + self.prefix

        output = popen2.Popen3(cmd + args)

        while output.poll() < 0:
            try:
                output.wait()
                time.sleep(0.001)
            except Exception:
                break

        # Skip unnecessary line
        line = output.fromchild.readline()

        self['subopt_basepairing_x'] = []
        self['subopt_basepairing_y'] = []
        self['subopt_energy'] = []
        self['totalnt'] = []
        counter = 0

        while line:
            line = output.fromchild.readline()
            if line:
                counter += 1
                words = line.split(' ')
                bracket_string = words[0]
                energy = float(words[len(words) - 1].replace('\n', ''))

                (strands, bp_x, bp_y) = _get_numbered_pairs(bracket_string)

                self['subopt_energy'].append(energy)
                self['subopt_basepairing_x'].append(bp_x)
                self['subopt_basepairing_y'].append(bp_y)

        self['subopt_NumStructs'] = counter

        self._cleanup()
        self['program'] = 'subopt'

    def energy(self, strands, base_pairing_x, base_pairing_y, temp=37.0,
               dangles='all'):
        '''energy.'''
        self['energy_composition'] = strands

        assert temp > 0

        seq_string = '&'.join(self['sequences'])
        strands = [len(seq) for seq in self['sequences']]
        bracket_string = _get_bracket(
            strands, base_pairing_x, base_pairing_y)
        input_string = seq_string + '\n' + bracket_string + '\n'

        handle = open(self.prefix, 'w')
        handle.write(input_string)
        handle.close()

        # Set arguments
        if dangles == 'none':
            dangles = ' -d0 '
        elif dangles == 'some':
            dangles = ' -d1 '
        elif dangles == 'all':
            dangles = ' -d2 '

        # Call ViennaRNA C programs
        cmd = 'RNAeval'
        args = dangles + ' < ' + self.prefix

        output = popen2.Popen3(cmd + args)

        while output.poll() < 0:
            try:
                output.wait()
                time.sleep(0.001)
            except Exception:
                break

        self['energy_energy'] = []

        # Skip the unnecessary output lines
        output.fromchild.readline()

        line = output.fromchild.readline()
        words = line.split(' ')
        energy = float(
            words[len(words) - 1].replace('(', '').replace(')', '').strip())

        self['program'] = 'energy'
        self['energy_energy'].append(energy)
        self['energy_basepairing_x'] = [base_pairing_x]
        self['energy_basepairing_y'] = [base_pairing_y]
        self._cleanup()

        return energy

    def _cleanup(self):
        if os.path.exists(self.prefix):
            os.remove(self.prefix)


def _get_numbered_pairs(bracket_string):
    '''_get_numbered_pairs.'''
    bp_x = []
    bp_y = []
    strands = []

    for _ in range(bracket_string.count(')')):
        bp_y.append([])

    last_nt_x_list = []
    counter = 0
    num_strands = 0
    for (pos, letter) in enumerate(bracket_string[:]):
        if letter == '.':
            counter += 1

        elif letter == '(':
            bp_x.append(pos - num_strands)
            last_nt_x_list.append(pos - num_strands)
            counter += 1

        elif letter == ')':
            nt_x = last_nt_x_list.pop()
            nt_x_pos = bp_x.index(nt_x)
            bp_y[nt_x_pos] = pos - num_strands
            counter += 1

        elif letter == '&':
            strands.append(counter)
            counter = 0
            num_strands += 1

        else:
            raise ValueError('Error! Invalid character in bracket notation.')

    if last_nt_x_list:
        raise ValueError('Error! Leftover unpaired nucleotides when ' +
                         'converting from bracket notation to numbered base ' +
                         'pairs.')

    strands.append(counter)
    bp_x = [pos + 1 for pos in bp_x[:]]  # Shift so that 1st position is 1
    bp_y = [pos + 1 for pos in bp_y[:]]  # Shift so that 1st position is 1

    return (strands, bp_x, bp_y)


def _get_bracket(strands, bp_x, bp_y):
    '''get_bracket.'''
    bp_x = [pos - 1 for pos in bp_x[:]]  # Shift so that 1st position is 0
    bp_y = [pos - 1 for pos in bp_y[:]]  # Shift so that 1st position is 0

    bracket_notation = []
    counter = 0
    for (strand_number, seq_len) in enumerate(strands):
        if strand_number > 0:
            bracket_notation.append('&')
        for pos in range(counter, seq_len + counter):
            if pos in bp_x:
                bracket_notation.append('(')
            elif pos in bp_y:
                bracket_notation.append(')')
            else:
                bracket_notation.append('.')
        counter += seq_len

    return ''.join(bracket_notation)
