'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments


class NuclAcidCalcRunner():
    '''NuclAcidCalcRunner.'''

    def __init__(self, calc, temp=37.0):
        self.__calc = calc
        self.__temp = temp
        self.__cache = {}

    def mfe(self, sequences, dangles='some'):
        '''Runs mfe.'''
        return self.__get('mfe', sequences, dangles)

    def subopt(self, sequences, energy_gap, dangles='some'):
        '''Runs subopt.'''
        return self.__get('subopt', sequences, dangles, energy_gap=energy_gap)

    def energy(self, sequences, bp_x, bp_y, dangles='some'):
        '''Runs energy.'''
        return self.__get('energy', sequences, dangles, bp_x=bp_x, bp_y=bp_y)

    def __get(self, cmd, sequences, dangles, energy_gap=None, bp_x=None,
              bp_y=None):
        '''Gets the NuPACK result (which may be cached).'''
        key = ';'.join([cmd, str(sequences), dangles, str(energy_gap),
                        str(bp_x), str(bp_y)])

        if key not in self.__cache:
            self.__cache[key] = self.__calc.run(cmd, sequences, self.__temp,
                                                dangles, energy_gap,
                                                bp_x, bp_y)

        return self.__cache[key]
