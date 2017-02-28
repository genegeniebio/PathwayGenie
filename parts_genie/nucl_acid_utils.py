'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
import subprocess
import tempfile


class RunnerBase(object):
    '''Base class for NuPackRunner.'''

    def __init__(self, temp=37.0):
        self._temp = temp
        self._cache = {}

    def mfe(self, sequences, dangles='some'):
        '''Runs mfe.'''
        return self._get('mfe', sequences, dangles)

    def subopt(self, sequences, energy_gap, dangles='some'):
        '''Runs subopt.'''
        return self._get('subopt', sequences, dangles, energy_gap=energy_gap)

    def energy(self, sequences, bp_x, bp_y, dangles='some'):
        '''Runs energy.'''
        return self._get('energy', sequences, dangles, bp_x=bp_x, bp_y=bp_y)

    def _get(self, cmd, sequences, dangles, energy_gap=None, bp_x=None,
             bp_y=None):
        '''Abstract method.'''
        raise NotImplementedError()


class NuPackRunner(RunnerBase):
    '''Wrapper class for running NuPACK jobs.'''

    def __init__(self, temp=37.0):
        super(NuPackRunner, self).__init__(temp)

    def _get(self, cmd, sequences, dangles, energy_gap=None, bp_x=None,
             bp_y=None):
        '''Gets the NuPACK result (which may be cached).'''
        key = ';'.join([cmd, str(sequences), dangles, str(energy_gap),
                        str(bp_x), str(bp_y)])

        if key not in self._cache:
            self._cache[key] = self.__run(cmd, sequences, dangles, energy_gap,
                                          bp_x, bp_y)

        return self._cache[key]

    def __run(self, cmd, sequences, dangles, energy_gap=None, bp_x=None,
              bp_y=None):
        '''Runs NuPACK.'''
        filename = _write_nupack_input(sequences, energy_gap=energy_gap,
                                       bp_x=bp_x, bp_y=bp_y)

        output = subprocess.check_output([cmd,
                                          '-T', str(self._temp),
                                          '-multi',
                                          '-material', 'rna1999',
                                          '-dangles', dangles,
                                          filename])

        try:
            with open(filename + '.' + cmd) as out_file:
                return _read_nupack_output(out_file)
        except IOError:
            # Skip the comments of the text file
            for line in output.splitlines():
                if line[0] != '%':
                    return float(line)


def _write_nupack_input(sequences, energy_gap=None, bp_x=None, bp_y=None):
    '''Creates the input file functions.'''
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.in')

    with open(tmpfile.name, 'w') as fle:
        fle.write(str(len(sequences)) + '\n')
        fle.write('\n'.join(sequences) + '\n')
        fle.write(' '.join([str(x + 1)
                            for x in range(len(sequences))]) + '\n')

        if energy_gap is not None:
            fle.write(str(energy_gap) + '\n')

        if bp_x is not None and bp_y is not None:
            for x_val, y_val in zip(bp_x, bp_y):
                fle.write(str(x_val) + '\t' + str(y_val) + '\n')

    return tmpfile.name[:-3]


def _read_nupack_output(out_file):
    '''Read the output text file generated by NuPACK.'''

    # Skip the comments of the text file
    line = out_file.readline()
    while line[0] == '%':
        line = out_file.readline()

    energies = []
    bp_xs = []
    bp_ys = []

    while line:
        words = line.split()

        if not line == '\n' and not words[0] == '%' and not words[0] == '':

            # Read the line containing the number of total nucleotides in
            # the complex

            # Read the line containing the mfe
            words = out_file.readline().split()
            energies.append(float(words[0]))

            # Skip the line containing the dot/parens description of the
            # secondary structure
            line = out_file.readline()

            # Read in the lines containing the base pairing description of
            # the secondary structure
            # Continue reading until a % comment
            bp_x = []
            bp_y = []

            line = out_file.readline()
            words = line.split()
            while not line == '\n' and not words[0] == '%':
                bp_x.append(int(words[0]))
                bp_y.append(int(words[1]))
                words = out_file.readline().split()

            bp_xs.append(bp_x)
            bp_ys.append(bp_y)

        line = out_file.readline()

    return energies, bp_xs, bp_ys
