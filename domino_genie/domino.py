'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from __future__ import division

from synbiochem.utils import dna_utils, ice_utils, pairwise, seq_utils
from synbiochem.utils.job import JobThread


class DominoThread(JobThread):
    '''Runs a DominoGenie job.'''

    def __init__(self, query):
        JobThread.__init__(self)

        self.__query = query
        self.__ice_client = ice_utils.ICEClient(
            query['ice']['url'],
            query['ice']['username'],
            query['ice']['password'],
            group_names=query['ice'].get('groups', None))

        self.__results = []

    def run(self):
        '''Designs dominoes (bridging oligos) for LCR.'''
        iteration = 0

        if 'components' not in self.__query:
            self.__get_components()

        self.__fire_event('running', iteration, 'Running...')

        for design in self.__query['designs']:
            orig_comps = [comp.copy()
                          for comp in design['components'][:-1]]

            # Apply restriction site digestion to PARTs not PLASMIDs.
            # (Assumes PLASMID at positions 1 and -1 - first and last).
            if self.__query.get('restr_enzs', None) is not None:
                design['components'] = [design['components'][0]] + \
                    [self.__apply_restricts(dna)
                     for dna in design['components'][1:-1]] + \
                    [design['components'][-1]]

            # Generate plasmid DNA object:
            dna = dna_utils.concat(design['components'][:-1])
            dna['typ'] = dna_utils.SO_PLASMID
            dna['desc'] = ' - '.join(design['design'])
            dna['children'].extend(orig_comps)

            # Generate domino sequences:
            seqs = [comp['seq'] for comp in design['components']]

            oligos = [self.__get_domino(pair)
                      for pair in pairwise(seqs)]
            pairs = [pair for pair in pairwise(design['design'])]
            design['dominoes'] = zip(pairs, oligos)

            import json
            print json.dumps(dna, indent=2)
            print

            self.__results.append(dna)

            iteration += 1
            self.__fire_event('running', iteration, 'Running...')

        if self._cancelled:
            self.__fire_event('cancelled', iteration,
                              message='Job cancelled')
        else:
            self.__fire_event('finished', iteration,
                              message='Job completed')

    def analyse_dominoes(self):
        '''Analyse sequences for similarity using BLAST.'''
        for design in self.__query['designs']:
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

    def __get_components(self):
        '''Gets DNA components from ICE.'''
        iteration = 0

        self.__fire_event('running', iteration,
                          'Extracting sequences from ICE...')

        for design in self.__query['designs']:
            design['components'] = \
                [self.__ice_client.get_ice_entry(ice_id).get_dna()
                 for ice_id in design['design']]

            iteration += 1
            self.__fire_event('running', iteration,
                              'Extracting sequences from ICE...')

    def __apply_restricts(self, dna):
        '''Cleave off prefix and suffix, according to restriction sites.'''
        if 'pQLINK' in dna['name']:
            restrict_dnas = [dna]
        else:
            if 'restr_enzs' in self.__query:
                restricts = [res['name'] for res in self.__query['restr_enzs']]
            else:
                restricts = []

            restrict_dnas = dna_utils.apply_restricts(dna, restricts)

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
                            'progress': iteration /
                            len(self.__query['designs']) * 100,
                            'iteration': iteration,
                            'max_iter': len(self.__query['designs'])},
                 'query': self.__query
                 }

        if status == 'finished':
            event['result'] = self.__results

        self._fire_event(event)
