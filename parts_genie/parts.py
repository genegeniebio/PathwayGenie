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
import sys

from synbiochem.optimisation.sim_ann import SimulatedAnnealer
from synbiochem.utils import dna_utils, sbol_utils, seq_utils
import numpy

from . import rbs_calculator as rbs_calc


class PartsSolution(object):
    '''Solution for RBS optimisation.'''

    def __init__(self, query):
        self.__query = query
        self.__calc = rbs_calc.RbsCalculator(self.__query['organism']['r_rna'])

        features = query['designs'][0]['dna']['features']

        # Check if dg_total or TIR (translation initiation rate) was specified.
        # If TIR, then convert to dg_total.
        self.__dg_target = rbs_calc.get_dg(float(features[1]['tir_target']))

        # Invalid pattern is restriction sites | repeating nucleotides:
        flt = query['filters']
        self.__inv_patt = '|'.join(([restr_enz['site']
                                     for restr_enz in flt['restr_enzs']]
                                    if 'restr_enzs' in query else []) +
                                   [x * int(flt['max_repeats'])
                                    for x in ['A', 'C', 'G', 'T']])

        self.__cod_opt = seq_utils.CodonOptimiser(
            query['organism']['taxonomy_id'])

        self.__get_seqs()

        # Randomly choose an RBS that is a decent starting point,
        # using the first CDS as the upstream sequence:
        rbs = self.__get_init_rbs(features[2][0]['seq'])

        self.__seqs = [features[0]['seq'],
                       self.__get_valid_rand_seq(max(0, features[1]['len'] -
                                                     len(rbs))),
                       rbs,
                       [feat['seq'] for feat in features[2]],
                       features[3]['seq']]

        self.__dgs = None
        self.__seqs_new = copy.deepcopy(self.__seqs)
        self.__dgs_new = None

    def get_query(self):
        '''Return query.'''
        return self.__query

    def get_values(self):
        '''Return update of in-progress solution.'''
        features = self.__query['designs'][0]['dna']['features']

        return [_get_value('mean_cai', 'CAI',
                           self.__get_mean_cai(self.__seqs[3]), 0, 1, 1),
                _get_value('mean_tir', 'TIR',
                           _get_mean_tir(self.__dgs), 0,
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

            cds = self.__seqs[3][idx]

            metadata = _get_metadata(prot_id,
                                     tirs[idx],
                                     self.__cod_opt.get_cai(cds),
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
        self.__mutate_pre_rbs()
        self.__mutate_rbs()
        self.__mutate_cds()
        self.__dgs_new = self.__calc_dgs(self.__seqs_new[1],
                                         self.__seqs_new[2],
                                         self.__seqs_new[3])
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

    def __get_seqs(self):
        '''Returns sequences from protein ids, which may be either Uniprot ids,
        or a protein sequence itself.'''
        uniprot_id_pattern = \
            '[OPQ][0-9][A-Z0-9]{3}[0-9]|' + \
            '[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}'

        for cds in self.__query['designs'][0]['dna']['features'][2]:
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

    def __get_init_rbs(self, cds, attempts=0, max_attempts=1000):
        '''Gets an initial RBS.'''
        if attempts > max_attempts - 1:
            raise ValueError('Unable to generate valid initial RBS.')

        rbs = self.__calc.get_initial_rbs(cds, self.__dg_target)

        if seq_utils.count_pattern(rbs,
                                   seq_utils.START_CODON_PATT) == 0:
            return rbs

        return self.__get_init_rbs(cds, attempts + 1, max_attempts)

    def __calc_dgs(self, pre_rbs, rbs, cdss):
        '''Calculates (simulated annealing) energies for given RBS.'''
        return [self.__calc.calc_dgs(pre_rbs + rbs + cds)
                for cds in cdss]

    def __mutate_pre_rbs(self):
        '''Mutates pre-RBS sequence.'''
        pos = int(random.random() * len(self.__seqs[1]))
        pre_seq_new = _replace(self.__seqs[1], pos, _rand_nuc())

        if seq_utils.count_pattern(pre_seq_new + self.__seqs[2],
                                   self.__inv_patt) + \
                seq_utils.count_pattern(pre_seq_new + self.__seqs[2],
                                        seq_utils.START_CODON_PATT) == 0:
            self.__seqs_new[1] = pre_seq_new
        else:
            self.__seqs_new[1] = self.__seqs[1]

    def __mutate_rbs(self):
        '''Mutates RBS.'''
        move = random.random()
        pos = int(random.random() * len(self.__seqs[2]))

        # Insert:
        if move < 0.1 and \
                len(self.__seqs[2]) < rbs_calc.MAX_RBS_LENGTH:
            base = random.choice(seq_utils.NUCLEOTIDES)
            rbs_new = self.__seqs[2][0:pos] + base + \
                self.__seqs[2][pos:len(self.__seqs[2])]
            pre_seq_new = self.__seqs_new[1][1:] \
                if len(self.__seqs_new[1]) > 0 else ''

        # Delete:
        elif move < 0.2 and len(self.__seqs[2]) > 1:
            rbs_new = _replace(self.__seqs[2], pos, '')
            pre_seq_new = random.choice(seq_utils.NUCLEOTIDES) + \
                self.__seqs_new[1]

        # Replace:
        else:
            rbs_new = _replace(self.__seqs[2], pos, _rand_nuc())
            pre_seq_new = self.__seqs_new[1]

        if seq_utils.count_pattern(pre_seq_new + rbs_new, self.__inv_patt) + \
                seq_utils.count_pattern(pre_seq_new + rbs_new,
                                        seq_utils.START_CODON_PATT) == 0:
            self.__seqs_new[1] = pre_seq_new
            self.__seqs_new[2] = rbs_new
        else:
            self.__seqs_new[1] = self.__seqs[1]
            self.__seqs_new[2] = self.__seqs[2]

    def __mutate_cds(self):
        '''Mutates (potentially) multiple CDS.'''
        for idx in range(len(self.__seqs[3])):
            self.__mutate_specific_cds(idx)

    def __mutate_single_cds(self):
        '''Mutates one randomly-selected CDS.'''
        idx = int(random.random() * len(self.__seqs[3]))
        self.__mutate_specific_cds(idx)

    def __mutate_specific_cds(self, idx):
        '''Mutates one specific CDS.'''
        prot_seq = self.__query['designs'][0][
            'dna']['features'][2][idx]['aa_seq']
        self.__seqs_new[3][idx] = \
            self.__cod_opt.mutate(prot_seq,
                                  self.__seqs[3][idx],
                                  5.0 / len(prot_seq))

    def __get_valid_rand_seq(self, length, attempts=0, max_attempts=1000):
        '''Returns a valid random sequence of supplied length.'''
        sys.setrecursionlimit(max_attempts)

        if attempts > max_attempts - 1:
            raise ValueError('Unable to generate valid random sequence of ' +
                             'length ' + str(length))

        seq = ''.join([_rand_nuc() for _ in range(0, length)])

        if seq_utils.count_pattern(seq, self.__inv_patt) + \
                seq_utils.count_pattern(seq,
                                        seq_utils.START_CODON_PATT) == 0:
            return seq

        return self.__get_valid_rand_seq(length, attempts + 1, max_attempts)

    def __get_mean_cai(self, cdss):
        '''Gets mean CAI.'''
        return numpy.mean([self.__cod_opt.get_cai(cds)
                           for cds in cdss])

    def __get_num_inv_seq(self, seqs):
        '''Returns number of invalid sequences.'''
        return sum([seq_utils.count_pattern(seqs[1] + seqs[2] + cds,
                                            self.__inv_patt)
                    for cds in seqs[3]])

    def __get_rogue_rbs(self, dgs):
        '''Returns rogue RBS sites.'''
        features = self.__query['designs'][0]['dna']['features']

        return [tir for tirs in _get_tirs(dgs) for tir in tirs[1:]
                if tir > float(features[1]['tir_target']) * 0.1]

    def __get_dna(self, prot_id, metadata, cds, idx):
        '''Writes SBOL document to temporary store.'''
        seq = self.__seqs[0] + self.__seqs[1] + self.__seqs[2] + \
            self.__seqs[3][idx] + self.__seqs[4]

        dna = dna_utils.DNA(name=metadata['name'],
                            desc=metadata['shortDescription'],
                            seq=seq)

        start = _add_subcomp(dna, self.__seqs[0], 1, name='Prefix')

        start = _add_subcomp(dna, self.__seqs[1] + self.__seqs[2], start,
                             name='RBS', typ=sbol_utils.SO_RBS)

        start = _add_subcomp(dna, cds, start,
                             name=prot_id + ' (CDS)',
                             typ=sbol_utils.SO_CDS)

        _add_subcomp(dna, self.__seqs[4], start, name='Suffix')

        return dna

    def __repr__(self):
        # return '%r' % (self.__dict__)
        cais = [self.__cod_opt.get_cai(prot_seq)
                for prot_seq in self.__seqs[3]]

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
        solution = PartsSolution(_process_query(query))
        SimulatedAnnealer.__init__(self, solution, verbose=True)


def _process_query(query):
    '''Perform application-specific pre-processing of query.'''

    # Designs:
    for design in query['designs']:
        for feature in design['dna']['features']:
            if isinstance(feature, list):
                for entry in feature:
                    entry['seq'] = entry['seq'].upper()
                    entry['len'] = int(entry['len'])
            else:
                feature['seq'] = feature['seq'].upper()
                feature['len'] = int(feature['len'])

                if 'tir_target' in feature:
                    feature['tir_target'] = float(feature['tir_target'])

    # Filters:
    query['filters']['excl_codons'] = \
        list(set([x.strip().upper()
                  for x in query['filters']['excl_codons'].split()])) \
        if 'excl_codons' in query['filters'] else []

    return query


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


def _replace(sequence, pos, nuc):
    '''Replace nucleotide at pos with nuc.'''
    return sequence[:pos] + nuc + sequence[pos + 1:]


def _rand_nuc():
    '''Returns a random nucleotide.'''
    return random.choice(['A', 'T', 'G', 'C'])


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
