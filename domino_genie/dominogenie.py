'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from domino_genie import doe, ice_interface
from synbiochem.utils import pairwise, seq_utils, dna_utils
from synbiochem.utils.job import JobThread


class DominoThread(JobThread):
    '''Runs a DominoGenie job.'''

    def __init__(self, query):
        self.__designs = query['designs']
        self.__melt_temp = query['melt_temp']
        self.__restricts = query.get('restricts', None)
        self.__reagent_concs = query.get('reagent_concs', None)
        JobThread.__init__(self)

    def run(self):
        '''Designs dominoes (bridging oligos) for LCR.'''

        for design in self.__designs:
            design['name'] = ' - '.join([dna['name'] for dna in design['dna']])

            # Apply restriction site digestion to PARTs not PLASMIDs.
            # (Assumes PLASMID at positions 1 and -1 - first and last).
            if self.__restricts is not None:
                design['dna'] = [design['dna'][0]] + \
                    [self.__apply_restricts(dna)
                     for dna in design['dna'][1:-1]] + \
                    [design['dna'][-1]]

            # Generate plasmid DNA object:
            design['plasmid'] = dna_utils.concat(design['dna'][:-1])

            # Generate domino sequences:
            seqs = [dna['seq'] for dna in design['dna']]

            oligos = [self.__get_domino(pair)
                      for pair in pairwise(seqs)]
            pairs = [pair for pair in pairwise(design['design'])]
            design['dominoes'] = zip(pairs, oligos)

    def analyse_dominoes(self):
        '''Analyse sequences for similarity using BLAST.'''
        for design in self.__designs:
            ids_seqs = dict(zip(design['design'], design['seqs']))
            analysis = seq_utils.do_blast(ids_seqs, ids_seqs)

            try:
                for result in analysis:
                    for alignment in result.alignments:
                        for hsp in alignment.hsps:
                            if result.query != alignment.hit_def:
                                print hsp
            except ValueError as err:
                print err

    def __apply_restricts(self, dna):
        '''Cleave off prefix and suffix, according to restriction sites.'''
        restrict_dnas = dna_utils.apply_restricts(dna, self.__restricts)

        # This is a bit fudgy...
        # Essentially, return the longest fragment remaining after digestion.
        # Assumes prefix and suffix are short sequences that are cleaved off.
        restrict_dnas.sort(key=lambda x: len(x['seq']), reverse=True)
        return restrict_dnas[0]

    def __get_domino(self, pair):
        '''Get bridging oligo for pair of sequences.'''
        return (seq_utils.get_seq_by_melt_temp(pair[0], self.__melt_temp,
                                               False, self.__reagent_concs),
                seq_utils.get_seq_by_melt_temp(pair[1], self.__melt_temp,
                                               self.__reagent_concs))


def main(args):
    '''main method.'''
    ice = ice_interface.ICEInterface(args[2], args[3], args[4], [args[5]])

    for filename in args[6:]:
        designs = doe.get_designs(filename)

        for design in designs:
            design['dna'] = [ice.get_dna(iceid)
                             for iceid in design['design']]

        query = {'designs': designs,
                 'melt_temp': float(args[0]),
                 'restricts': [args[1]]}

        runner = DominoThread(query)
        runner.run()

        print designs
        # ice.submit(designs)


if __name__ == '__main__':
    main(sys.argv[1:])
