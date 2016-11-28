'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=no-member
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes
import copy
import json
import math
import os
import random
import re
import sys
import urlparse
import uuid

import numpy

from synbiochem.optimisation.sim_ann import SimulatedAnnealer
from synbiochem.utils import dna_utils, sbol_utils, seq_utils, taxonomy_utils
from synbiochem.utils.job import JobThread
from . import rbs_calculator as rbs_calc, sbol_writer


class PartsGenie(object):
    '''Class to run PartsGenie application.'''

    def __init__(self, sbol_dir):
        self.__sbol_dir = sbol_dir

        if not os.path.exists(self.__sbol_dir):
            os.makedirs(self.__sbol_dir)

    def get_thread(self, query):
        '''Gets a thread to run query.'''
        job_id = _process_query(query)
        return job_id, PartsThread(job_id, query, self.__sbol_dir)

    def get_result(self, file_id):
        '''Returns results.'''
        path = os.path.join(self.__sbol_dir, file_id)

        with open(path, 'r') as fle:
            content = fle.read()
            return content, 'text/xml'

    def save(self, req):
        '''Saves results.'''
        ice_entry_urls = []
        req_obj = json.loads(req.data)

        for result in req_obj['result']:
            path = str(os.path.join(self.__sbol_dir, result['data']['file']))

            dna = sbol_utils.read(path)
            url = req_obj['ice']['url']
            url = url[:-1] if url[-1] == '/' else url
            ice_id = sbol_writer.submit(url,
                                        req_obj['ice']['username'],
                                        req_obj['ice']['password'],
                                        dna, result['metadata'])
            ice_entry_urls.append(url + '/entry/' + str(ice_id))

        return ice_entry_urls


class PartsSolution(object):
    '''Solution for RBS optimisation.'''

    def __init__(self, query, sbol_dir):
        self.__query = query
        self.__sbol_dir = sbol_dir
        self.__calc = rbs_calc.RbsCalculator(self.__query['organism']['r_rna'])

        # Check if dg_total or TIR (translation initiation rate) was specified.
        # If TIR, then convert to dg_total.
        self.__dg_target = rbs_calc.get_dg(float(query['tir_target']))

        # Invalid pattern is restriction sites | repeating nucleotides:
        self.__inv_patt = '|'.join(([restr_enz['site']
                                     for restr_enz in query['restr_enzs']]
                                    if 'restr_enzs' in query else []) +
                                   [x * int(query['max_repeats'])
                                    for x in ['A', 'C', 'G', 'T']])

        self.__cod_opt = seq_utils.CodonOptimiser(
            query['organism']['taxonomy_id'])

        self.__prot_seqs = seq_utils.get_sequences(query['protein_ids'])

        cds = [self.__cod_opt.get_codon_optim_seq(prot_seq,
                                                  query['excl_codons'],
                                                  self.__inv_patt,
                                                  tolerant=False)
               for prot_seq in self.__prot_seqs.values()]

        stop_codon = self.__cod_opt.get_codon_optim_seq('*',
                                                        query['excl_codons'])

        # Randomly choose an RBS that is a decent starting point,
        # using the first CDS as the upstream sequence:
        rbs = self.__get_init_rbs(cds[0])

        post_seq_length = 30
        self.__seqs = [query['prefix'] if 'prefix' in query else '',
                       self.__get_valid_rand_seq(max(0, query['len_target'] -
                                                     len(rbs))),
                       rbs,
                       cds,
                       stop_codon,
                       self.__get_valid_rand_seq(post_seq_length)
                       if len(self.__prot_seqs) > 1 else '',
                       query['suffix'] if 'suffix' in query else '']

        self.__dgs = None
        self.__seqs_new = copy.deepcopy(self.__seqs)
        self.__dgs_new = None

    def get_query(self):
        '''Return query.'''
        return self.__query

    def get_values(self):
        '''Return update of in-progress solution.'''
        return [_get_value('mean_cai', 'CAI',
                           self.__get_mean_cai(self.__seqs[3]), 0, 1, 1),
                _get_value('mean_tir', 'TIR',
                           _get_mean_tir(self.__dgs), 0,
                           float(self.__query['tir_target']) * 1.2,
                           float(self.__query['tir_target'])),
                _get_value('num_invalid_seqs', 'Invalid seqs',
                           self.__get_num_inv_seq(self.__seqs), 0, 10, 0),
                _get_value('num_rogue_rbs', 'Rogue RBSs',
                           len(self.__get_rogue_rbs(self.__dgs)), 0, 10, 0)]

    def get_result(self):
        '''Return result of solution.'''
        result = []
        tirs = [tirs[0] for tirs in _get_tirs(self.__dgs)]

        for idx, prot_id in enumerate(self.__query['protein_ids']):
            uniprot_regex = \
                r'^([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})' + \
                r'|([O,P,Q][0-9][A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\.\d+)?$'

            if re.match(uniprot_regex, prot_id):
                uniprot_id = prot_id
            else:
                prot_id = self.__query['protein_names'][idx]
                uniprot_id = None

            cds = self.__seqs[3][idx] + self.__seqs[4]

            metadata = sbol_writer.get_metadata(prot_id, uniprot_id)
            parameters = metadata['parameters']
            parameters.append({'name': 'Type', 'value': 'PART'})
            parameters.append({'name': 'TIR',
                               'value': float("{0:.2f}".format(tirs[idx]))})
            parameters.append({'name': 'CAI',
                               'value': float("{0:.2f}".format(
                                   self.__cod_opt.get_cai(cds)))})

            result_file = self.__write_sbol(prot_id, metadata, cds, idx)

            result.append({'metadata': metadata,
                           'data': {'file': result_file,
                                    'mimetype': 'text/xml'}})

        return result

    def get_energy(self, seqs=None, dgs=None):
        '''Gets the (simulated annealing) energy.'''
        if seqs is None:
            return float('inf')

        tir_target = float(self.__query['tir_target'])
        mean_d_tir = abs(tir_target - _get_mean_tir(dgs)) / tir_target

        return math.erf(mean_d_tir) + \
            self.__get_num_inv_seq(seqs) + \
            len(self.__get_rogue_rbs(dgs))

    def mutate(self):
        '''Mutates and scores whole design.'''
        self.__mutate_pre_seq()
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

    def __get_init_rbs(self, cds, attempts=0, max_attempts=1000):
        '''Gets an initial RBS.'''
        if attempts > max_attempts - 1:
            raise ValueError('Unable to generate valid initial RBS.')

        rbs = self.__calc.get_initial_rbs(cds, self.__dg_target)

        if seq_utils.count_pattern(rbs,
                                   seq_utils.START_CODON_PATT) == 0:
            return rbs

        return self.__get_init_rbs(cds, attempts + 1, max_attempts)

    def __calc_dgs(self, pre_seq, rbs, cdss):
        '''Calculates (simulated annealing) energies for given RBS.'''
        return [self.__calc.calc_dgs(pre_seq + rbs + cds)
                for cds in cdss]

    def __mutate_pre_seq(self):
        '''Mutates pre-sequence.'''
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
        prot_seq = self.__prot_seqs.values()[idx]
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
        return sum([seq_utils.count_pattern(seqs[1] + seqs[2] + cds +
                                            seqs[4] + seqs[5], self.__inv_patt)
                    for cds in seqs[3]])

    def __get_rogue_rbs(self, dgs):
        '''Returns rogue RBS sites.'''
        return [tir for tirs in _get_tirs(dgs) for tir in tirs[1:]
                if tir > float(self.__query['tir_target']) * 0.1]

    def __write_sbol(self, prot_id, metadata, cds, idx):
        '''Writes SBOL document to temporary store.'''
        seq = self.__seqs[0] + self.__seqs[1] + self.__seqs[2] + \
            self.__seqs[3][idx] + self.__seqs[4] + self.__seqs[5] + \
            self.__seqs[6]

        dna = dna_utils.DNA(name=metadata['name'],
                            desc=metadata['shortDescription'],
                            seq=seq)

        start = sbol_writer.add_subcomp(dna, self.__seqs[0], 1, name='Prefix')

        start = sbol_writer.add_subcomp(dna, self.__seqs[1], start,
                                        name='5\' Insulator')

        start = sbol_writer.add_subcomp(dna, self.__seqs[2], start, name='RBS',
                                        typ=sbol_utils.SO_RBS)

        start = sbol_writer.add_subcomp(dna, cds, start,
                                        name=prot_id + ' (CDS)',
                                        typ=sbol_utils.SO_CDS)

        start = sbol_writer.add_subcomp(dna, self.__seqs[5], start,
                                        name='3\' Insulator')

        sbol_writer.add_subcomp(dna, self.__seqs[6], start, name='Suffix')

        result_file = str(uuid.uuid4()) + '.xml'
        sbol_url = urlparse.urljoin(self.__sbol_dir, result_file)
        sbol_utils.write(dna, sbol_url)

        return result_file

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


class PartsThread(JobThread):
    '''Wraps a Parts optimisation job into a thread.'''

    def __init__(self, job_id, query, sbol_dir):
        solution = PartsSolution(query, sbol_dir)
        self.__sim_ann = SimulatedAnnealer(solution, verbose=True)
        self.__sim_ann.add_listener(self)

        JobThread.__init__(self, job_id)

    def cancel(self):
        '''Cancels the current job.'''
        self.__sim_ann.cancel()

    def run(self):
        '''Runs the current job.'''
        self.__sim_ann.optimise()


def _process_query(query):
    '''Perform application-specific pre-processing of query.'''
    query['protein_names'] = \
        list([x.strip() for x in query['protein_names'].split(',')])
    query['protein_ids'] = \
        list([x.strip() for x in query['protein_ids'].split(',')])
    query['len_target'] = int(query['len_target'])
    query['tir_target'] = float(query['tir_target'])
    query['excl_codons'] = \
        list(set([x.strip().upper()
                  for x in query['excl_codons'].split()])) \
        if 'excl_codons' in query else []

    # Map organism to taxonomy id:
    query['organism']['taxonomy_id'] = taxonomy_utils.get_taxonomy_id(
        query['organism']['name'])

    if 'prefix' in query:
        query['prefix'] = query['prefix'].upper()

    if 'suffix' in query:
        query['suffix'] = query['suffix'].upper()

    return str(uuid.uuid4())


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
