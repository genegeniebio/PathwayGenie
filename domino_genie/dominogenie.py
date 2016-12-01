'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from __future__ import division

import sys

from domino_genie import doe
from domino_genie.ice_interface import ICEInterface
from synbiochem.utils import pairwise, seq_utils, dna_utils
from synbiochem.utils.job import JobThread


class DominoThread(JobThread):
    '''Runs a DominoGenie job.'''

    def __init__(self, query):
        JobThread.__init__(self)

        self.__query = query
        self.__designs = query['designs']
        self.__restr_enzs = query.get('restr_enzs', None)
        self.__ice_int = None

    def run(self):
        '''Designs dominoes (bridging oligos) for LCR.'''
        if 'dna' not in self.__query:
            self.__get_dna()

        iteration = 0
        self.__fire_event('running', iteration, 'Running...')

        for design in self.__designs:

            design['name'] = ' - '.join([dna['name'] for dna in design['dna']])

            # Apply restriction site digestion to PARTs not PLASMIDs.
            # (Assumes PLASMID at positions 1 and -1 - first and last).
            if self.__restr_enzs is not None:
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

            iteration += 1
            self.__fire_event('running', iteration, 'Running...')

        if self._cancelled:
            self.__fire_event('cancelled', iteration, message='Job cancelled')
        else:
            self.__fire_event('finished', iteration, message='Job completed')

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

    def __get_dna(self):
        '''Gets DNA sequences from ICE.'''
        self.__ice_int = self.__get_ice_interface()

        iteration = 0

        self.__fire_event('running', iteration,
                          'Extracting sequences from ICE...')

        for design in self.__query['designs']:
            design['dna'] = [self.__ice_int.get_dna(iceid)
                             for iceid in design['design']]

            iteration += 1
            self.__fire_event('running', iteration,
                              'Extracting sequences from ICE...')

    def __get_ice_interface(self):
        '''Gets an ICEClient if not already instantiated.'''
        if not self.__ice_int:
            self.__fire_event('running', 0,
                              'Connecting to ICE...')

            self.__ice_int = ICEInterface(self.__query['ice']['url'],
                                          self.__query['ice']['username'],
                                          self.__query['ice']['password'],
                                          self.__query['ice']['groups'])

        return self.__ice_int

    def __apply_restricts(self, dna):
        '''Cleave off prefix and suffix, according to restriction sites.'''
        restrict_dnas = dna_utils.apply_restricts(dna, self.__restr_enzs)

        # This is a bit fudgy...
        # Essentially, return the longest fragment remaining after digestion.
        # Assumes prefix and suffix are short sequences that are cleaved off.
        restrict_dnas.sort(key=lambda x: len(x['seq']), reverse=True)
        return restrict_dnas[0]

    def __get_domino(self, pair):
        '''Get bridging oligo for pair of sequences.'''
        melt_temp = self.__query['melt_temp']
        reagent_concs = self.__query.get('reagent_concs', None)

        return (seq_utils.get_seq_by_melt_temp(pair[0], melt_temp,
                                               False, reagent_concs),
                seq_utils.get_seq_by_melt_temp(pair[1], melt_temp,
                                               reagent_concs))

    def __fire_event(self, status, iteration, message=''):
        '''Fires an event.'''
        event = {'update': {'status': status,
                            'message': message,
                            'progress': iteration / len(self.__designs) * 100,
                            'iteration': iteration,
                            'max_iter': len(self.__designs)},
                 'query': self.__query
                 }

        if status == 'finished':
            event['result'] = self.__designs

        self._fire_event(event)


def main(args):
    '''main method.'''
    for filename in args[6:]:
        designs = doe.get_designs(filename)

        _query = {'designs': designs,
                  'melt_temp': float(args[0]),
                  'restr_enzs': [args[1]],
                  'ice': {'url': args[2],
                          'username': args[3],
                          'password': args[4],
                          'groups': args[5:]}}

        runner = DominoThread(_query)
        runner.add_listener(Listener())
        runner.start()

        # ice.submit(designs)


class Listener(object):
    '''Basic Listener class.'''

    def event_fired(self, event):
        '''Responds to event.'''
        print event

if __name__ == '__main__':
    main(sys.argv[1:])
