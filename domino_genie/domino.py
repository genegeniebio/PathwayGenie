'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from __future__ import division

from synbiochem.utils import dna_utils, ice_utils, pairwise, seq_utils
from synbiochem.utils.job import JobThread
from synbiochem.utils.seq_utils import get_seq_by_melt_temp


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

        for dsgn in self.__query['designs']:
            orig_comps = [comp.copy()
                          for comp in dsgn['components'][:-1]]

            # Apply restriction site digestion to PARTs not PLASMIDs.
            # (Assumes PLASMID at positions 1 and -1 - first and last).
            for idx, dna_restr_enz in enumerate(
                    zip(dsgn['components'], self.__query['restr_enzs'])):
                dsgn['components'][idx] = \
                    self.__apply_restricts(dna_restr_enz[0], dna_restr_enz[1])

            # Generate plasmid DNA object:
            dna = dna_utils.concat(dsgn['components'][:-1])
            dna['typ'] = dna_utils.SO_PLASMID
            dna['children'].extend(orig_comps)

            # Generate domino sequences:
            dna['children'].extend([self.__get_domino(pair)
                                    for pair in pairwise(dsgn['components'])])

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
                [self.__get_component(ice_id) for ice_id in design['design']]

            iteration += 1
            self.__fire_event('running', iteration,
                              'Extracting sequences from ICE...')

    def __get_component(self, ice_id):
        '''Gets a DNA component from ICE.'''
        ice_entry = self.__ice_client.get_ice_entry(ice_id)
        dna = ice_entry.get_dna()
        dna['desc'] = ice_id
        return dna

    def __apply_restricts(self, dna, restr_enz):
        '''Apply restruction enzyme.'''
        if restr_enz == 'None':
            return dna

        restrict_dnas = dna_utils.apply_restricts(dna, restr_enz.split(','))

        # This is a bit fudgy...
        # Essentially, return the longest fragment remaining after digestion.
        # Assumes prefix and suffix are short sequences that are cleaved off.
        restrict_dnas.sort(key=lambda x: len(x['seq']), reverse=True)
        return restrict_dnas[0]

    def __get_domino(self, pair):
        '''Gets a domino from a pair of DNA objects.'''
        dna = dna_utils.concat([self.__get_domino_branch(pair[0], False),
                                self.__get_domino_branch(pair[1])])
        dna['parameters']['Type'] = 'DOMINO'
        return dna

    def __get_domino_branch(self, comp, forward=True):
        '''Gets domino branch from DNA object.'''
        target_melt_temp = self.__query['melt_temp']
        reag_concs = self.__query.get('reagent_concs', None)

        seq, melt_temp = get_seq_by_melt_temp(comp['seq'],
                                              target_melt_temp,
                                              forward,
                                              reag_concs)

        dna = dna_utils.DNA(name=comp['name'],
                            desc=comp['desc'],
                            seq=seq,
                            typ=dna_utils.SO_ASS_COMP,
                            forward=True)

        dna['features'].append(dna.copy())
        dna['parameters']['Tm'] = float('{0:.3g}'.format(melt_temp))

        return dna

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
