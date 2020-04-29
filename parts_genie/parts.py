'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=no-self-use
# pylint: disable=wrong-import-order
import collections
import copy
from itertools import product
import math

from synbiochem.optimisation.sim_ann import SimulatedAnnealer
from synbiochem.utils import dna_utils, seq_utils

from parts_genie import rbs_calculator as rbs_calc
from parts_genie import vienna_utils as calc


class PartsSolution():
    '''Solution for RBS optimisation.'''

    def __init__(self, dna, organism, filters):
        self.__dna = dna_utils.get_dna(dna)
        self.__dna['typ'] = dna_utils.SO_PART
        self.__dna['parameters']['Type'] = 'PART'
        self.__organism = organism
        self.__filters = filters
        self.__filters['restr_enzs'] = self.__filters.get('restr_enzs', [])
        self.__filters['gc_min'] = float(self.__filters['gc_min'])
        self.__filters['gc_max'] = float(self.__filters['gc_max'])

        self.__calc = rbs_calc.RbsCalculator(organism['r_rna'], calc) \
            if self.__organism else None

        self.__cod_opt = seq_utils.CodonOptimiser(organism['taxonomy_id']) \
            if self.__organism else None

        self.__dna_new = None

    def init(self):
        '''Initialisation method for longer initiation tasks.'''
        self.__init_seqs()
        self.__calc_num_fixed()
        self.__update(self.__dna)

        self.__dna_new = copy.deepcopy(self.__dna)

    def get_query(self):
        '''Return query.'''
        return {'dna': self.__dna,
                'organism': self.__organism,
                'filters': self.__filters}

    def get_values(self):
        '''Return update of in-progress solution.'''
        keys = ['id', 'name', 'value', 'min', 'max',
                'target_min', 'target_max']
        params = self.__dna['temp_params']

        if params:
            return [dict(zip(keys, ('mean_cai',
                                    'CAI',
                                    params['mean_cai'],
                                    0, 1, 0.9, 1))),
                    dict(zip(keys, ('mean_tir',
                                    'TIR',
                                    params['mean_tir_errs'],
                                    0, 1, 0, 0.05))),
                    dict(zip(keys, ('num_invalid_seqs',
                                    'Invalid seqs',
                                    params['num_inv_seq'],
                                    0, 10, 0, 0.5))),
                    dict(zip(keys, ('num_rogue_rbs',
                                    'Rogue RBSs',
                                    params['num_rogue_rbs'],
                                    0, 10, 0, 0.5))),
                    dict(zip(keys, ('global_gc',
                                    'Global GC',
                                    self.__dna['parameters']['Global GC'],
                                    0, 1,
                                    self.__filters['gc_min'],
                                    self.__filters['gc_max']))),
                    dict(zip(keys, ('local_gc',
                                    'Local GC',
                                    self.__dna['temp_params']['Local GC'],
                                    0, 10, 0, 0.5))),
                    dict(zip(keys, ('gc_var',
                                    'GC variance',
                                    self.__dna['temp_params']['GC variance'],
                                    0, 10, 0, 0.5))),
                    dict(zip(keys, ('repeats',
                                    'Repeats',
                                    self.__dna['temp_params']['num_repeats'],
                                    0, 10, 0, 0.5)))]
        # else:
        return []

    def get_result(self):
        '''Return result of solution.'''
        return dna_utils.expand(self.__dna)

    def get_energy(self, dna=None):
        '''Gets the (simulated annealing) energy.'''
        return float('inf') if dna is None else dna['temp_params']['energy']

    def mutate(self):
        '''Mutates and scores whole design.'''
        for feature in self.__dna_new['features']:
            if feature['typ'] == dna_utils.SO_CDS \
                    and not feature['temp_params']['fixed']:
                mutation_rate = 5.0 / len(feature['temp_params']['aa_seq'])
                feature.set_seq(self.__cod_opt.mutate(
                    feature['temp_params']['aa_seq'],
                    feature['seq'],
                    mutation_rate))
            elif not feature['temp_params']['fixed']:
                feature.set_seq(seq_utils.mutate_seq(feature['seq'],
                                                     mutations=3))

        return self.__update(self.__dna_new)

    def accept(self):
        '''Accept potential update.'''
        self.__dna = copy.deepcopy(self.__dna_new)

    def reject(self):
        '''Reject potential update.'''
        self.__dna_new = copy.deepcopy(self.__dna)

    def __calc_num_fixed(self, flank=16):
        '''Calculate number of anomalies in fixed sequences.'''
        fixed_seqs = [feat['seq']
                      for feat in self.__dna['features']
                      if feat['temp_params'].get('fixed', False)]

        flanked_fixed_seqs = ['N' * flank + seq + 'N' * flank
                              for seq in fixed_seqs]

        self.__calc_num_inv_seq_fixed(flanked_fixed_seqs)
        self.__calc_num_local_gc_fixed(fixed_seqs)
        self.__calc_num_repeats_fixed(fixed_seqs)
        self.__calc_num_rogue_rbs_fixed()

    def __calc_num_inv_seq_fixed(self, fixed_seqs):
        '''Calculate number of invalid sequences in fixed sequences.'''
        self.__dna['temp_params']['num_inv_seq_fixed'] = \
            sum([len(seq_utils.find_invalid(seq,
                                            self.__filters['max_repeats'],
                                            self.__filters['restr_enzs']))
                 for seq in fixed_seqs])

    def __calc_num_local_gc_fixed(self, fixed_seqs):
        '''Calculate number of invalid sequences in fixed sequences.'''
        self.__dna['temp_params']['num_local_gc_fixed'] = \
            self.__get_local_gc(fixed_seqs)

    def __calc_num_repeats_fixed(self, fixed_seqs):
        '''Calculate number of repeats in fixed sequences.'''
        self.__dna['temp_params']['num_repeats_fixed'] = \
            _get_repeats(fixed_seqs)

    def __calc_num_rogue_rbs_fixed(self):
        '''Calculate number of rogue RBS sequences in fixed CDS.'''
        num_rogue_rbs = 0

        for idx, feature in enumerate(self.__dna['features']):
            if feature['typ'] == dna_utils.SO_RBS:
                cds = self.__dna['features'][idx + 1]

                if cds['temp_params']['fixed']:
                    _, rogue_rbs = self.__calc_tirs(feature, cds)
                    num_rogue_rbs += len(rogue_rbs)

        self.__dna['temp_params']['num_rogue_rbs_fixed'] = num_rogue_rbs

    def __init_seqs(self):
        '''Returns sequences from protein ids, which may be either Uniprot ids,
        or a protein sequence itself.'''
        for idx, feature in enumerate(self.__dna['features']):
            if feature['typ'] == dna_utils.SO_CDS \
                    and not feature['temp_params']['fixed']:
                feature['temp_params']['aa_seq'] = \
                    ''.join(feature['temp_params']['aa_seq'].upper().split())

                if feature['temp_params']['aa_seq'][-1] != '*':
                    feature['temp_params']['aa_seq'] += '*'

                feature['links'].append(
                    'http://identifiers.org/taxonomy/' +
                    self.__organism['taxonomy_id'])

                feature.set_seq(self.__cod_opt.get_codon_optim_seq(
                    feature['temp_params']['aa_seq'],
                    self.__filters.get('excl_codons', None),
                    self.__filters['max_repeats'],
                    self.__filters['restr_enzs'],
                    tolerant=False))

            elif feature['typ'] == dna_utils.SO_RBS:
                # Randomly choose an RBS that is a decent starting point,
                # using the first CDS as the upstream sequence:
                feature.set_seq(self.__calc.get_initial_rbs(
                    feature['end'],
                    self.__dna['features'][idx + 1]['seq'],
                    feature['parameters']['TIR target']))

            elif feature['typ'] == dna_utils.SO_ASS_COMP:
                # Generate bridging oligo site of desired melting temp:
                if not feature['seq']:
                    seq, melt_temp = seq_utils.get_rand_seq_by_melt_temp(
                        feature['parameters']['Tm target'],
                        self.__filters['max_repeats'],
                        self.__filters['restr_enzs'])

                    feature.set_seq(seq)
                else:
                    melt_temp = seq_utils.get_melting_temp(feature['seq'])

                feature['parameters']['Tm'] = melt_temp

            elif feature['typ'] == dna_utils.SO_RANDOM:
                # Randomly choose a sequence:
                seq = seq_utils.get_random_dna(feature.pop('end'),
                                               self.__filters['max_repeats'],
                                               self.__filters['restr_enzs'])
                feature.set_seq(seq)
            else:
                feature['seq'] = ''.join(feature['seq'].upper().split())

    def __update(self, dna):
        '''Calculates (simulated annealing) energies for given RBS.'''
        cais = []
        tir_errs = []
        num_rogue_rbs = 0

        for idx, feature in enumerate(dna['features']):
            if feature['typ'] == dna_utils.SO_RBS:
                cds = dna['features'][idx + 1]
                tir_err, rogue_rbs = self.__calc_tirs(feature, cds)
                tir_errs.append(tir_err)
                num_rogue_rbs += len(rogue_rbs)

            elif feature['typ'] == dna_utils.SO_CDS \
                    and not feature['temp_params']['fixed']:
                cai = self.__cod_opt.get_cai(feature['seq'])
                feature['parameters']['CAI'] = cai
                cais.append(cai)

        dna['temp_params']['mean_cai'] = _mean(cais) if cais else 0
        dna['temp_params']['mean_tir_errs'] = _mean(tir_errs) \
            if tir_errs else 0
        dna['temp_params']['num_rogue_rbs'] = num_rogue_rbs - \
            dna['temp_params']['num_rogue_rbs_fixed']

        # Get number of invalid seqs:
        all_seqs = _get_all_seqs(dna)

        dna['temp_params']['num_inv_seq'] = \
            sum([len(seq_utils.find_invalid(seq,
                                            self.__filters['max_repeats'],
                                            self.__filters['restr_enzs']))
                 for seq in all_seqs]) - \
            dna['temp_params']['num_inv_seq_fixed']

        # Calculate GC content:
        dna['parameters']['Global GC'] = \
            _mean([_get_gc(seq) for seq in all_seqs])

        dna['temp_params']['Local GC'] = self.__get_local_gc(all_seqs) - \
            self.__dna['temp_params']['num_local_gc_fixed']

        dna['temp_params']['GC variance'] = _get_gc_var(all_seqs)

        dna['temp_params']['num_repeats'] = _get_repeats(all_seqs) - \
            self.__dna['temp_params']['num_repeats_fixed']

        dna['temp_params']['energy'] = dna['temp_params']['mean_tir_errs'] + \
            dna['temp_params']['num_inv_seq'] + \
            dna['temp_params']['num_rogue_rbs'] + \
            _get_delta_range(self.__filters['gc_min'],
                             self.__filters['gc_max'],
                             dna['parameters']['Global GC']) * 100 + \
            dna['temp_params']['Local GC'] + \
            dna['temp_params']['GC variance'] + \
            dna['temp_params']['num_repeats']

        return self.get_energy(dna)

    def __calc_tirs(self, rbs, cds):
        '''Performs TIR calculations.'''
        tir_vals = self.__calc.calc_dgs(rbs['seq'] + cds['seq'],
                                        len(rbs['seq']))

        cds['temp_params']['tir_vals'] = tir_vals

        # Get TIR:
        try:
            tir = tir_vals[rbs['end']][1]
        except KeyError:
            # If RBS cannot be found at start position, set tir to be zero:
            tir = 0

        cds['parameters']['TIR'] = tir
        target = rbs['parameters']['TIR target']

        try:
            tir_err = 1 - math.log(target - abs(target - tir), target)
        except ValueError:
            # If tir is -ve, set tir_err to be a large number:
            tir_err = 2.0 ** 32

        # Get rogue RBS sites:
        cutoff = 0.1
        rogue_rbs = [(pos, terms)
                     for pos, terms in tir_vals.items()
                     if pos != rbs['end'] and terms[1] >
                     rbs['parameters']['TIR target'] * cutoff]

        return tir_err, rogue_rbs

    def __get_local_gc(self, seqs):
        '''Get local GC score.'''
        local_gc_count = 0

        window_size = self.__filters['local_gc_window']

        for seq in seqs:
            local_gcs = [_get_gc(seq[idx:idx + window_size])
                         for idx in range(len(seq) - window_size + 1)]

            for local_gc in local_gcs:
                if _get_delta_range(self.__filters['local_gc_min'],
                                    self.__filters['local_gc_max'],
                                    local_gc):
                    local_gc_count += 1

        return local_gc_count

    def __repr__(self):
        # return '%r' % (self.__dict__)
        tirs = []
        cais = []

        for feature in self.__dna['features']:
            if feature['typ'] == dna_utils.SO_CDS:
                tirs.append(feature['parameters'].get('TIR', None))
                cais.append(feature['parameters'].get('CAI', None))

        return '\t'.join([str(tirs),
                          str(cais),
                          str(self.__dna['parameters']['Global GC']),
                          str(self.__dna['temp_params']['num_inv_seq']),
                          str(self.__dna['temp_params']['num_rogue_rbs']),
                          str(self.__dna['temp_params']['Local GC']),
                          str(self.__dna['temp_params']['GC variance']),
                          str(self.__dna['temp_params']['num_repeats'])])

    def __print__(self):
        return self.__repr__


class PartsThread(SimulatedAnnealer):
    '''Wraps a PartsGenie job into a thread.'''

    def __init__(self, query, idx, verbose=True):
        solution = PartsSolution(query['designs'][idx],
                                 query.get('organism', None),
                                 query['filters'])

        SimulatedAnnealer.__init__(self, solution, verbose=verbose)


def _mean(lst):
    '''Gets mean of list.'''
    return float(sum(lst)) / len(lst) if lst else 0.0


def _get_delta_range(min_val, max_val, val):
    '''Gets delta of val from min_val, max_val range.'''
    if val < min_val:
        return min_val - val
    if val > max_val:
        return val - max_val

    return 0


def _get_gc(seq):
    '''Get GC content.'''
    return (seq.count('G') + seq.count('C')) / float(len(seq))


def _get_gc_var(seqs, window_size=50, tol=0.52):
    '''Get local GC variance.'''
    local_gc_var = 0

    for seq in seqs:
        local_gcs = sorted([_get_gc(seq[idx:idx + window_size])
                            for idx in range(len(seq) - window_size + 1)])

        if local_gcs[-1] - local_gcs[0] > tol:
            local_gc_var += 1

    return local_gc_var


def _get_repeats(seqs, window_size=25):
    '''Get local GC score.'''
    repeats = 0

    for seq in seqs:
        windows = [seq[idx:idx + window_size]
                   for idx in range(len(seq) - window_size + 1)]
        counter = collections.Counter(windows)
        repeats += sum(i for i in counter.values() if i > 1)

    return repeats


def _get_all_seqs(dna):
    '''Return all sequences.'''
    all_seqs = ['']

    for feature in dna['features']:
        if feature['typ'] == dna_utils.SO_CDS:
            options = [feature['seq']]
            all_seqs = [''.join(term) for term in product(all_seqs, options)]
        else:
            for idx, seq in enumerate(all_seqs):
                all_seqs[idx] = seq + feature['seq']

    return all_seqs
