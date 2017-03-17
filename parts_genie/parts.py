'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from itertools import product
import copy
import re

from numpy import mean
from synbiochem.optimisation.sim_ann import SimulatedAnnealer
from synbiochem.utils import dna_utils, sbol_utils, seq_utils

from parts_genie import rbs_calculator as rbs_calc


class PartsSolution(object):
    '''Solution for RBS optimisation.'''

    def __init__(self, dna, organism, filters):
        self.__dna = dna
        self.__organism = organism
        self.__filters = filters

        self.__calc = rbs_calc.RbsCalculator(organism['r_rna'])
        self.__cod_opt = seq_utils.CodonOptimiser(organism['taxonomy_id'])

        # Invalid pattern is restriction sites | repeating nucleotides:
        self.__inv_patt = '|'.join(([restr_enz['site']
                                     for restr_enz in filters['restr_enzs']]
                                    if 'restr_enzs' in filters else []) +
                                   [x * int(filters['max_repeats'])
                                    for x in seq_utils.NUCLEOTIDES])

        self.__get_seqs()
        self.__update(self.__dna)
        self.__dna_new = copy.deepcopy(self.__dna)

    def get_query(self):
        '''Return query.'''
        return {'dna': self.__dna,
                'organism': self.__organism,
                'filters': self.__filters}

    def get_values(self):
        '''Return update of in-progress solution.'''
        return [_get_value('mean_cai',
                           'CAI',
                           self.__dna['mean_cai'],
                           0, 1, 1),
                _get_value('mean_tir',
                           'TIR',
                           self.__dna['mean_tir_errs'],
                           0, 1, 0),
                _get_value('num_invalid_seqs',
                           'Invalid seqs',
                           self.__dna['num_inv_seq'],
                           0, 10, 0),
                _get_value('num_rogue_rbs',
                           'Rogue RBSs',
                           self.__dna['num_rogue_rbs'],
                           0, 10, 0)]

    def get_result(self):
        '''Return result of solution.'''
        all_dnas = []

        for feature in self.__dna['features']:
            if len(feature.get('seq', '')) or len(feature.get('options', '')):
                if feature['typ'] == sbol_utils.SO_RBS:
                    tirs = _get_non_rogue_tirs(feature)

                if feature['typ'] == sbol_utils.SO_CDS:
                    for tir, cds in zip(tirs, feature['options']):
                        metadata = _get_metadata(cds['name'],
                                                 tir,
                                                 self.__cod_opt.get_cai(
                                                     cds['seq']),
                                                 self.__organism[
                                                     'taxonomy_id'],
                                                 cds.get('uniprot', None))

                        cds['name'] = metadata['name']
                        cds['desc'] = metadata['shortDescription']

                        _add_feature_to_all(all_dnas, cds)
                else:
                    _add_feature_to_all(all_dnas, feature)

        return all_dnas

    def get_energy(self, dna=None):
        '''Gets the (simulated annealing) energy.'''
        return float('inf') if dna is None else dna['energy']

    def mutate(self):
        '''Mutates and scores whole design.'''
        for feature in self.__dna_new['features']:
            if not feature['fixed']:
                if feature['typ'] == sbol_utils.SO_CDS:
                    for idx, cds in enumerate(feature['options']):
                        cds = feature['options'][idx]
                        mutation_rate = 5.0 / len(cds['aa_seq'])
                        cds['seq'] = self.__cod_opt.mutate(cds['aa_seq'],
                                                           cds['seq'],
                                                           mutation_rate)
                else:
                    feature['seq'] = seq_utils.mutate_seq(feature['seq'],
                                                          mutations=3)

        return self.__update(self.__dna_new)

    def accept(self):
        '''Accept potential update.'''
        self.__dna = copy.deepcopy(self.__dna_new)

    def reject(self):
        '''Reject potential update.'''
        self.__dna_new = copy.deepcopy(self.__dna)

    def __get_seqs(self):
        '''Returns sequences from protein ids, which may be either Uniprot ids,
        or a protein sequence itself.'''
        uniprot_id_pattern = \
            '[OPQ][0-9][A-Z0-9]{3}[0-9]|' + \
            '[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}'

        for feature in self.__dna['features']:
            if feature['typ'] == sbol_utils.SO_CDS:
                for cds in feature['options']:
                    if re.match(uniprot_id_pattern, cds['aa_seq']):
                        uniprot_vals = seq_utils.get_uniprot_values(
                            [cds['aa_seq']], ['sequence']).values()

                        cds['uniprot'] = cds['aa_seq']
                        cds['aa_seq'] = [values['Sequence']
                                         for values in uniprot_vals][0]

                        if cds['aa_seq'][-1] != '*':
                            cds['aa_seq'] += '*'

                    cds['seq'] = self.__cod_opt.get_codon_optim_seq(
                        cds['aa_seq'],
                        self.__filters['excl_codons'],
                        self.__inv_patt,
                        tolerant=False)

        # Randomly choose an RBS that is a decent starting point,
        # using the first CDS as the upstream sequence:
        for idx, feature in enumerate(self.__dna['features']):
            if feature['typ'] == sbol_utils.SO_RBS:
                rbs = self.__dna['features'][idx]
                rbs['seq'] = self.__calc.get_initial_rbs(
                    rbs['len'],
                    self.__dna['features'][idx + 1]['options'][0]['seq'],
                    rbs['dg_target'])

    def __update(self, dna):
        '''Calculates (simulated annealing) energies for given RBS.'''
        cais = []
        mean_tir_errs = []
        num_rogue_rbs = 0

        for idx, feature in enumerate(dna['features']):
            if feature['typ'] == sbol_utils.SO_RBS:
                cdss = dna['features'][idx + 1]['options']

                feature['rbs_vals'] = [self.__calc.calc_dgs(feature['seq'] +
                                                            cds['seq'])
                                       for cds in cdss]

                mean_tir_errs.append(_get_mean_tir_err(feature))
                num_rogue_rbs += len(_get_rogue_rbs(feature))

            elif feature['typ'] == sbol_utils.SO_CDS:
                for cds in feature['options']:
                    cds['cai'] = self.__cod_opt.get_cai(cds['seq'])
                    cais.append(cds['cai'])

        dna['cais'] = cais
        dna['mean_cai'] = mean(cais)
        dna['mean_tir_errs'] = mean(mean_tir_errs)
        dna['num_rogue_rbs'] = num_rogue_rbs

        # Get number of invalid seqs:
        dna['num_inv_seq'] = sum([seq_utils.count_pattern(seq, self.__inv_patt)
                                  for seq in _get_all_seqs(dna)])

        dna['energy'] = dna['mean_tir_errs'] + \
            dna['num_inv_seq'] + \
            dna['num_rogue_rbs']

        return self.get_energy(dna)

    def __repr__(self):
        # return '%r' % (self.__dict__)
        tirs = []

        for feature in self.__dna['features']:
            if feature['typ'] == sbol_utils.SO_RBS:
                tirs.append(_get_non_rogue_tirs(feature))

        return '\t'.join(['' if tirs is None
                          else str(tirs),
                          str(self.__dna['cais']),
                          str(self.__dna['num_inv_seq']),
                          str(self.__dna['num_rogue_rbs']),
                          ' '.join([str(feat)
                                    for feat in self.__dna['features']])])

    def __print__(self):
        return self.__repr__


class PartsThread(SimulatedAnnealer):
    '''Wraps a PartsGenie job into a thread.'''

    def __init__(self, query):
        _process_query(query)

        solution = PartsSolution(query['designs'][0]['dna'],
                                 query['organism'],
                                 query['filters'])

        SimulatedAnnealer.__init__(self, solution, verbose=True)


def _process_query(query):
    '''Perform application-specific pre-processing of query.'''

    # Designs:
    for design in query['designs']:
        features = design['dna']['features']

        for feature in features:
            if 'seq' in feature:
                feature['seq'] = feature['seq'].upper()

            if 'tir_target' in feature:
                feature['dg_target'] = \
                    rbs_calc.get_dg(feature['tir_target'])

            for cds in feature.get('options', []):
                cds['aa_seq'] = cds['aa_seq'].upper()

    # Filters:
    filters = query['filters']

    filters['excl_codons'] = \
        list(set([x.strip().upper()
                  for x in filters['excl_codons'].split()])) \
        if 'excl_codons' in filters else []


def _get_all_seqs(dna):
    '''Return all sequences.'''
    all_seqs = ['']

    for feature in dna['features']:
        if feature['typ'] == sbol_utils.SO_CDS:
            all_seqs = [''.join(term)
                        for term in product([option['seq']
                                             for option in feature['options']],
                                            all_seqs)]
        else:
            for idx, seq in enumerate(all_seqs):
                all_seqs[idx] = seq + feature['seq']

    return all_seqs


def _get_value(value_id, name, value, min_value, max_value, target):
    '''Returns value data as a dict.'''
    return {'id': value_id,
            'name': name,
            'value': value,
            'min': min_value,
            'max': max_value,
            'target': target}


def _get_rogue_rbs(rbs, cutoff=0.1):
    '''Returns rogue RBS sites.'''
    return [(pos, terms)
            for rbs_vals in rbs['rbs_vals']
            for pos, terms in rbs_vals.iteritems()
            if pos != rbs['len'] and terms[1] > rbs['tir_target'] * cutoff]


def _get_non_rogue_tirs(rbs):
    '''Gets all non-rogue TIRs for RBS sites.'''
    return [terms[1]
            for rbs_vals in rbs['rbs_vals']
            for pos, terms in rbs_vals.iteritems()
            if pos == rbs['len']]


def _get_mean_tir_err(rbs):
    '''Gets mean TIR error of RBS sites (not rogue RBSs) as proportion of
    target TIR.'''
    return abs(rbs['tir_target'] - mean(_get_non_rogue_tirs(rbs))) / \
        rbs['tir_target']


def _get_metadata(prot_id, tir, cai, target_org=None, uniprot_id=None):
    '''Gets metadata.'''
    name = prot_id
    description = prot_id
    links = []
    parameters = []

    if uniprot_id is not None:
        uniprot_vals = seq_utils.get_uniprot_values([uniprot_id],
                                                    ['entry name',
                                                     'protein names',
                                                     'organism-id',
                                                     'organism',
                                                     'ec'])
        # Add metadata:
        if len(uniprot_vals.keys()):
            prot_id = uniprot_vals.keys()[0]
            name = uniprot_vals[prot_id]['Entry name']
            organism = uniprot_vals[prot_id]['Organism']
            prot_names = uniprot_vals[prot_id]['Protein names']
            description = ', '.join(prot_names) + ' (' + organism + ')'
            ec_number = uniprot_vals[prot_id].get('EC number', None)

            parameters.append({'name': 'Organism', 'value': organism})
            links.append('http://identifiers.org/uniprot/' + uniprot_id)

            if ec_number:
                links.append('http://identifiers.org/ec-code/' + ec_number)

    parameters.append({'name': 'Type', 'value': 'PART'})
    parameters.append({'name': 'TIR', 'value': float("{0:.2f}".format(tir))})
    parameters.append({'name': 'CAI', 'value': float("{0:.2f}".format(cai))})

    if target_org:
        links.append('http://identifiers.org/taxonomy/' + target_org)

    metadata = {'name': name,
                'shortDescription': description,
                'links': links,
                'parameters': parameters}

    return metadata


def _add_feature_to_all(all_dnas, feature):
    if not len(all_dnas):
        dna = dna_utils.DNA(name=feature['name'],
                            desc=feature.get('desc', None),
                            seq=feature['seq'],
                            forward=feature.get('forward', True))
        _add_feature(dna, feature)
        all_dnas.append(dna)
    else:
        for dna in all_dnas:
            _add_feature(dna, feature)


def _add_feature(dna, feature):
    '''Adds a subcompartment.'''
    start = len(dna['seq']) + 1
    seq = feature['seq']

    if seq is not None and len(seq):
        end = start + len(seq) - 1
        feature = dna_utils.DNA(name=feature['name'],
                                desc=feature.get('desc', None),
                                typ=feature['typ'],
                                start=start,
                                end=end,
                                forward=feature.get('forward', True))
        dna['features'].append(feature)
