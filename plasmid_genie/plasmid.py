'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from __future__ import division

from synbiochem.utils import dna_utils, ice_utils, pairwise, seq_utils
from synbiochem.utils.seq_utils import get_seq_by_melt_temp
from pathway_genie.utils import PathwayThread


class PlasmidThread(PathwayThread):
    '''Runs a PlasmidGenie job.'''

    def __init__(self, query):
        PathwayThread.__init__(self, query)

        self.__ice_client = ice_utils.ICEClient(
            query['ice']['url'],
            query['ice']['username'],
            query['ice']['password'],
            group_names=query['ice'].get('groups', None))

    def run(self):
        '''Designs dominoes (bridging oligos) for LCR.'''
        iteration = 0

        if 'components' not in self._query:
            self.__get_components()

        self._fire_designs_event('running', iteration, 'Running...')

        for dsgn in self._query['designs']:
            orig_comps = [comp.copy() for comp in dsgn['components']]

            # Apply restriction site digestion:
            dsgn['components'] = [_apply_restricts(dna, restr_enz)
                                  for dna, restr_enz in zip(
                dsgn['components'], self._query['restr_enzs'])]

            # Generate plasmid DNA object:
            dna = dna_utils.concat(dsgn['components'])
            dna['name'] = dsgn['name']
            dna['typ'] = dna_utils.SO_PLASMID
            dna['children'].extend(orig_comps)

            # Generate domino sequences:
            cmps = dsgn['components'] + [dsgn['components'][0]] \
                if self._query['circular'] else dsgn['components']

            dna['children'].extend([self.__get_domino(pair)
                                    for pair in pairwise(cmps)])

            self._results.append(dna)

            iteration += 1
            self._fire_designs_event('running', iteration, 'Running...')

        if self._cancelled:
            self._fire_designs_event('cancelled', iteration,
                                     message='Job cancelled')
        else:
            self._fire_designs_event('finished', iteration,
                                     message='Job completed')

    def analyse_dominoes(self):
        '''Analyse sequences for similarity using BLAST.'''
        for design in self._query['designs']:
            ids_seqs = dict(zip(design['design'], design['seqs']))
            analysis = seq_utils.do_blast(ids_seqs, ids_seqs)

            for result in analysis:
                for alignment in result.alignments:
                    for hsp in alignment.hsps:
                        if result.query != alignment.hit_def:
                            return hsp

    def __get_components(self):
        '''Gets DNA components from ICE.'''
        iteration = 0

        self._fire_designs_event('running', iteration,
                                 'Extracting sequences from ICE...')

        for design in self._query['designs']:
            design['components'] = \
                [self.__get_component(ice_id)
                 for ice_id in design['design']
                 if ice_id]

            iteration += 1
            self._fire_designs_event('running', iteration,
                                     'Extracting sequences from ICE...')

    def __get_component(self, ice_id):
        '''Gets a DNA component from ICE.'''
        ice_entry = self.__ice_client.get_ice_entry(ice_id)
        dna = ice_entry.get_dna()
        dna['desc'] = ice_id
        return dna

    def __get_domino(self, pair):
        '''Gets a domino from a pair of DNA objects.'''
        dna = dna_utils.concat([self.__get_domino_branch(pair[0], False),
                                self.__get_domino_branch(pair[1])])
        dna['parameters']['Type'] = 'DOMINO'
        return dna

    def __get_domino_branch(self, comp, forward=True):
        '''Gets domino branch from DNA object.'''
        target_melt_temp = self._query['melt_temp']
        reag_concs = self._query.get('reagent_concs', None)

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


def _apply_restricts(dna, restr_enz):
    '''Apply restruction enzyme.'''
    if not restr_enz:
        return dna

    restrict_dnas = dna_utils.apply_restricts(dna, restr_enz.split(','))

    # This is a bit fudgy...
    # Essentially, return the longest fragment remaining after digestion.
    # Assumes prefix and suffix are short sequences that are cleaved off.
    restrict_dnas.sort(key=lambda x: len(x['seq']), reverse=True)
    return restrict_dnas[0]
