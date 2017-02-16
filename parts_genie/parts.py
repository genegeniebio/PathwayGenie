'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
import copy
import math
import random
import re

from synbiochem.optimisation.sim_ann import SimulatedAnnealer
from synbiochem.utils import dna_utils, sbol_utils, seq_utils
import numpy

from parts_genie import rbs_calculator as rbs_calc


class PartsSolution(object):
    '''Solution for RBS optimisation.'''

    def __init__(self, query):
        self.__query = query
        self.__process_query()

        self.__calc = rbs_calc.RbsCalculator(self.__query['organism']['r_rna'])
        self.__cod_opt = seq_utils.CodonOptimiser(
            self.__query['organism']['taxonomy_id'])

        # Invalid pattern is restriction sites | repeating nucleotides:
        flt = query['filters']
        self.__inv_patt = '|'.join(([restr_enz['site']
                                     for restr_enz in flt['restr_enzs']]
                                    if 'restr_enzs' in query else []) +
                                   [x * int(flt['max_repeats'])
                                    for x in seq_utils.NUCLEOTIDES])

        self.__get_seqs()
        self.__seqs = query['designs'][0]['dna']['features']
        self.__dgs = None
        self.__seqs_new = copy.deepcopy(query['designs'][0]['dna']['features'])
        self.__dgs_new = None

    def get_query(self):
        '''Return query.'''
        return self.__query

    def get_values(self):
        '''Return update of in-progress solution.'''
        features = self.__query['designs'][0]['dna']['features']

        mean_cai = numpy.mean([self.__cod_opt.get_cai(cds['seq'])
                               for cds in self.__seqs[2]])

        return [_get_value('mean_cai', 'CAI', mean_cai, 0, 1, 1),
                _get_value('mean_tir', 'TIR', _get_mean_tir(self.__dgs), 0,
                           float(features[1]['tir_target']) * 1.2,
                           float(features[1]['tir_target'])),
                _get_value('num_invalid_seqs', 'Invalid seqs',
                           self.__get_num_inv_seq(self.__seqs), 0, 10, 0),
                _get_value('num_rogue_rbs', 'Rogue RBSs',
                           len(self.__get_rogue_rbs(self.__dgs)), 0, 10, 0)]

    def get_result(self):
        '''Return result of solution.'''
        result = []
        tirs = [tirs[0] for tirs in _get_tirs(self.__dgs)]

        cdss = self.__query['designs'][0]['dna']['features'][2]

        for idx, cds in enumerate(cdss):
            uniprot_id = cds.get('uniprot', None)

            if uniprot_id:
                prot_id = uniprot_id
            else:
                prot_id = cds['name']

            cds = self.__seqs[2][idx]

            metadata = _get_metadata(prot_id,
                                     tirs[idx],
                                     self.__cod_opt.get_cai(cds['seq']),
                                     self.__query['organism']['taxonomy_id'],
                                     uniprot_id)

            dna = self.__get_dna(prot_id, metadata, cds, idx)

            result.append({'metadata': metadata, 'dna': dna})

        return result

    def get_energy(self, seqs=None, dgs=None):
        '''Gets the (simulated annealing) energy.'''
        if seqs is None:
            return float('inf')

        features = self.__query['designs'][0]['dna']['features']
        tir_target = float(features[1]['tir_target'])
        mean_d_tir = abs(tir_target - _get_mean_tir(dgs)) / tir_target

        return math.erf(mean_d_tir) + \
            self.__get_num_inv_seq(seqs) + \
            len(self.__get_rogue_rbs(dgs))

    def mutate(self):
        '''Mutates and scores whole design.'''
        self.__seqs_new[1]['seq'] = seq_utils.mutate_seq(self.__seqs[1]['seq'])
        self.__mutate_cds()
        self.__dgs_new = self.__calc_dgs()
        return self.get_energy(self.__seqs_new, self.__dgs_new)

    def accept(self):
        '''Accept potential update.'''
        self.__seqs = copy.deepcopy(self.__seqs_new)
        self.__dgs = copy.deepcopy(self.__dgs_new)
        self.reject()

    def reject(self):
        '''Reject potential update.'''
        self.__seqs_new = copy.deepcopy(self.__seqs)
        self.__dgs_new = copy.deepcopy(self.__dgs)

    def __process_query(self):
        '''Perform application-specific pre-processing of query.'''

        # Designs:
        for design in self.__query['designs']:
            features = design['dna']['features']

            for feature in features:
                if isinstance(feature, list):
                    for entry in feature:
                        entry['seq'] = entry['seq'].upper()
                        entry['len'] = int(entry['len'])
                else:
                    feature['seq'] = feature['seq'].upper()
                    feature['len'] = int(feature['len'])

                    if 'tir_target' in feature:
                        feature['tir_target'] = float(feature['tir_target'])
                        feature['dg_target'] = \
                            rbs_calc.get_dg(feature['tir_target'])

        # Filters:
        filters = self.__query['filters']

        filters['excl_codons'] = \
            list(set([x.strip().upper()
                      for x in filters['excl_codons'].split()])) \
            if 'excl_codons' in filters else []

    def __get_seqs(self):
        '''Returns sequences from protein ids, which may be either Uniprot ids,
        or a protein sequence itself.'''
        uniprot_id_pattern = \
            '[OPQ][0-9][A-Z0-9]{3}[0-9]|' + \
            '[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}'

        features = self.__query['designs'][0]['dna']['features']

        for cds in features[2]:
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
                self.__query['filters']['excl_codons'],
                self.__inv_patt,
                tolerant=False)

        # Randomly choose an RBS that is a decent starting point,
        # using the first CDS as the upstream sequence:
        rbs = features[1]
        features[1]['seq'] = self.__calc.get_initial_rbs(rbs['len'],
                                                         features[2][0]['seq'],
                                                         rbs['dg_target'])

    def __calc_dgs(self):
        '''Calculates (simulated annealing) energies for given RBS.'''
        return [self.__calc.calc_dgs(self.__seqs_new[1]['seq'] +
                                     cds['seq'])
                for cds in self.__seqs_new[2]]

    def __mutate_cds(self):
        '''Mutates (potentially) multiple CDS.'''
        for idx in range(len(self.__seqs[2])):
            self.__mutate_specific_cds(idx)

    def __mutate_single_cds(self):
        '''Mutates one randomly-selected CDS.'''
        idx = int(random.random() * len(self.__seqs[2]))
        self.__mutate_specific_cds(idx)

    def __mutate_specific_cds(self, idx):
        '''Mutates one specific CDS.'''
        prot_seq = self.__query['designs'][0][
            'dna']['features'][2][idx]['aa_seq']
        self.__seqs_new[2][idx]['seq'] = \
            self.__cod_opt.mutate(prot_seq,
                                  self.__seqs[2][idx]['seq'],
                                  5.0 / len(prot_seq))

    def __get_num_inv_seq(self, seqs):
        '''Returns number of invalid sequences.'''
        return sum([seq_utils.count_pattern(seqs[1]['seq'] + cds['seq'],
                                            self.__inv_patt)
                    for cds in seqs[2]])

    def __get_rogue_rbs(self, dgs):
        '''Returns rogue RBS sites.'''
        features = self.__query['designs'][0]['dna']['features']

        return [tir for tirs in _get_tirs(dgs) for tir in tirs[1:]
                if tir > float(features[1]['tir_target']) * 0.1]

    def __get_dna(self, prot_id, metadata, cds, idx):
        '''Writes SBOL document to temporary store.'''
        seq = self.__seqs[0]['seq'] + self.__seqs[1]['seq'] + \
            self.__seqs[2][idx]['seq'] + self.__seqs[3]['seq']

        dna = dna_utils.DNA(name=metadata['name'],
                            desc=metadata['shortDescription'],
                            seq=seq)

        start = _add_subcomp(dna, self.__seqs[0]['seq'], 1, name='Prefix')

        start = _add_subcomp(dna, self.__seqs[1]['seq'], start,
                             name='RBS', typ=sbol_utils.SO_RBS)

        start = _add_subcomp(dna, cds['seq'], start,
                             name=prot_id + ' (CDS)',
                             typ=sbol_utils.SO_CDS)

        _add_subcomp(dna, self.__seqs[3]['seq'], start, name='Suffix')

        return dna

    def __repr__(self):
        # return '%r' % (self.__dict__)
        cais = [self.__cod_opt.get_cai(cds['seq'])
                for cds in self.__seqs[2]]

        return '\t'.join(['' if self.__dgs is None
                          else str([tirs[0]
                                    for tirs in _get_tirs(self.__dgs)]),
                          str(cais),
                          str(self.__get_num_inv_seq(self.__seqs)),
                          str(len(self.__get_rogue_rbs(self.__dgs))),
                          ' '.join([str(seq) for seq in self.__seqs])])

    def __print__(self):
        return self.__repr__


class PartsThread(SimulatedAnnealer):
    '''Wraps a PartsGenie job into a thread.'''

    def __init__(self, query):
        solution = PartsSolution(query)
        SimulatedAnnealer.__init__(self, solution, verbose=True)


def _get_value(value_id, name, value, min_value, max_value, target):
    '''Returns value data as a dict.'''
    return {'id': value_id,
            'name': name,
            'value': value,
            'min': min_value,
            'max': max_value,
            'target': target}


def _get_tirs(dgs):
    '''Gets the translation initiation rates.'''
    return [[rbs_calc.get_tir(d_g) for d_g in lst[1]] for lst in dgs]


def _get_mean_tir(dgs):
    '''Gets mean TIR of RBS sites (not rogue RBSs).'''
    return 0 if dgs is None \
        else numpy.mean([tirs[0] for tirs in _get_tirs(dgs)])


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


def _add_subcomp(dna, seq, start, forw=True, name=None, typ=None, desc=None):
    '''Adds a subcompartment.'''
    if seq is not None and len(seq):
        end = start + len(seq) - 1
        feature = dna_utils.DNA(name=name, desc=desc, typ=typ,
                                start=start, end=end, forward=forw)
        dna['features'].append(feature)

        return end + 1

    return start
