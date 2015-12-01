'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from compiler.ast import flatten
import math
from numpy import mean
import random
import sys

import RBS_Calculator
import RBS_MC_Design
from synbiochem.optimisation.sim_ann import SimulatedAnnealer
from synbiochem.utils import sequence_utils as seq_utils
from synbiochem.utils.job import JobThread


# Necessary to get constants hidden as class variables in RBS_Calculator:
_RBS_CALC = RBS_Calculator.RBS_Calculator('A', [0, 0])

# Invalid pattern is restriction sites | repeating nucleotides:
_MAX_REPEATING_NUCS = 6
_INVALID_PATTERN = '|'.join(['GGTCTC', 'GAGACC',
                             'CACCTGC', 'GCAGGTG',
                             'GAATTC',
                             'AGATCT',
                             'GGATCC',
                             'CTCGAG',
                             'GAGTC[ACGT]{5}', '[ACGT]{5}GACTC'] +
                            [x * _MAX_REPEATING_NUCS
                             for x in ['A', 'C', 'G', 'T']])

_START_CODON_PATTERN = '[ACGT]TG'


class PartsSolution(object):
    '''Solution for RBS optimisation.'''

    def __init__(self, protein_ids, taxonomy_id, len_target, tir_target):
        self.__query = {'query': {'protein_ids': protein_ids,
                                  'taxonomy_id': taxonomy_id,
                                  'len_target': len_target,
                                  'tir_target': tir_target}}

        # Check if dg_total or TIR (translation initiation rate) was specified.
        # If TIR, then convert to dg_total.
        self.__dg_target = _RBS_CALC.RT_eff * \
            (_RBS_CALC.logK - math.log(float(tir_target)))

        self.__cod_opt = seq_utils.CodonOptimiser(taxonomy_id)

        self.__prot_seqs = seq_utils.get_sequences(protein_ids)
        cds = [self.__cod_opt.get_codon_optimised_seq(prot_seq,
                                                      _INVALID_PATTERN)
               for prot_seq in self.__prot_seqs.values()]

        stop_codon = self.__cod_opt.get_codon_optimised_seq('*')

        # Randomly choose an RBS that is a decent starting point,
        # using the first CDS as the upstream sequence:
        rbs = self.__get_init_rbs(cds[0])

        post_seq_length = 30
        self.__seqs = [self.__get_valid_rand_seq(max(0,
                                                     len_target - len(rbs))),
                       rbs,
                       cds,
                       stop_codon,
                       self.__get_valid_rand_seq(post_seq_length)
                       if len(self.__prot_seqs) > 1 else None]
        self.__dgs = self.__calc_dgs(rbs)
        self.__seqs_new = [None, None, cds, self.__seqs[3], self.__seqs[4]]
        self.__dgs_new = None

    def get_status(self):
        '''Return status of solution.'''
        mean_cai = mean([self.__cod_opt.get_cai(cds)
                         for cds in self.__seqs[2]])
        mean_tir = 0 if self.__dgs is None else mean(_get_tirs(self.__dgs))
        inv_patt = sum(flatten([seq_utils.count_pattern(seq, _INVALID_PATTERN)
                                for seq in self.__seqs]))

        status = {'status': {'mean_cai': mean_cai,
                             'mean_tir': mean_tir,
                             'invalid_patterns': inv_patt}}

        return dict(self.__query.items() + status.items())

    def get_result(self):
        '''Return result of solution.'''
        return {'result': {'seqs': self.__seqs}}

    def get_energy(self, dgs=None, cdss=None):
        '''Gets the (simulated annealing) energy.'''
        dgs = self.__dgs if dgs is None else dgs
        cdss = self.__seqs[2] if cdss is None else cdss
        return sum([abs(d_g - self.__dg_target) for d_g in dgs]) / \
            len(self.__seqs[2]) * \
            (1 + (sum(seq_utils.count_pattern([self.__seqs[1]] + cdss,
                                              _INVALID_PATTERN)))**10)

    def mutate(self, verbose=False):
        '''Mutates and scores whole design.'''
        self.__mutate_pre_seq()
        self.__mutate_rbs()
        self.__mutate_cds()
        self.__dgs_new = self.__calc_dgs(self.__seqs_new[1], verbose)
        return self.get_energy(self.__dgs_new, self.__seqs_new[2])

    def accept(self):
        '''Accept potential update.'''
        self.__seqs = self.__seqs_new
        self.__dgs = self.__dgs_new
        self.__seqs_new = [None, None, self.__seqs[2], self.__seqs[3],
                           self.__seqs[4]]
        self.__dgs_new = None

    def __get_init_rbs(self, cds, attempts=0, max_attempts=1000):
        '''Gets an initial RBS.'''
        if attempts > max_attempts - 1:
            raise ValueError('Unable to generate valid initial RBS.')

        (rbs, _) = RBS_MC_Design.GetInitialRBS('', cds,
                                               self.__dg_target)

        if seq_utils.count_pattern(rbs, _INVALID_PATTERN) + \
                seq_utils.count_pattern(rbs, _START_CODON_PATTERN) == 0:
            return rbs

        return self.__get_init_rbs(cds, attempts + 1, max_attempts)

    def __calc_dgs(self, rbs, verbose=False):
        '''Calculates (simulated annealing) energies for given RBS.'''
        return [RBS_MC_Design.Run_RBS_Calculator(self.__seqs[0],
                                                 cds,
                                                 rbs,
                                                 verbose).dG_total_list[0]
                for cds in self.__seqs[2]]

    def __mutate_pre_seq(self):
        '''Mutates pre-sequence.'''
        pos = int(random.random() * len(self.__seqs[0]))
        pre_seq_new = _replace(self.__seqs[0], pos, _rand_nuc())

        if seq_utils.count_pattern(pre_seq_new + self.__seqs[1],
                                   _INVALID_PATTERN) + \
                seq_utils.count_pattern(pre_seq_new + self.__seqs[1],
                                        _START_CODON_PATTERN) == 0:
            self.__seqs_new[0] = pre_seq_new
        else:
            self.__seqs_new[0] = self.__seqs[0]

    def __mutate_rbs(self):
        '''Mutates RBS.'''
        weighted_moves = [('insert', 0.1), ('delete', 0.1), ('replace', 0.8)]
        move = RBS_MC_Design.weighted_choice(weighted_moves)
        pos = int(random.random() * len(self.__seqs[1]))

        if move == 'insert' and \
                len(self.__seqs[1]) < RBS_MC_Design.Max_RBS_Length:
            letter = random.choice(['A', 'T', 'G', 'C'])
            rbs_new = self.__seqs[1][0:pos] + letter + \
                self.__seqs[1][pos:len(self.__seqs[1])]
            pre_seq_new = self.__seqs_new[0][1:] \
                if len(self.__seqs_new[0]) > 0 else ''

        elif move == 'delete' and len(self.__seqs[1]) > 1:
            rbs_new = _replace(self.__seqs[1], pos, '')
            pre_seq_new = random.choice(['A', 'T', 'G', 'C']) + \
                self.__seqs_new[0]

        elif move == 'replace':
            rbs_new = _replace(self.__seqs[1], pos, _rand_nuc())
            pre_seq_new = self.__seqs_new[0]

        else:
            pre_seq_new = self.__seqs_new[0]
            rbs_new = self.__seqs[1]

        if seq_utils.count_pattern(pre_seq_new + rbs_new, _INVALID_PATTERN) + \
                seq_utils.count_pattern(pre_seq_new + rbs_new,
                                        _START_CODON_PATTERN) == 0:
            self.__seqs_new[0] = pre_seq_new
            self.__seqs_new[1] = rbs_new
        else:
            self.__seqs_new[0] = self.__seqs[0]
            self.__seqs_new[1] = self.__seqs[1]

    def __mutate_cds(self):
        '''Mutates (potentially) multiple CDS.'''
        new_cds = [self.__cod_opt.mutate(prot_seq, dna_seq, 3.0 / len(dna_seq))
                   for dna_seq, prot_seq in zip(self.__seqs[2],
                                                self.__prot_seqs.values())]

        self.__seqs_new[2] = [cds
                              if seq_utils.count_pattern(cds,
                                                         _INVALID_PATTERN) == 0
                              else self.__seqs_new[2][idx]
                              for idx, cds in enumerate(new_cds)]

    def __mutate_single_cds(self):
        '''Mutates one randomly-selected CDS.'''
        idx = int(random.random() * len(self.__seqs[2]))
        new_cds = self.__cod_opt.mutate(self.__prot_seqs.values()[idx],
                                        self.__seqs[2][idx],
                                        3.0 * len(self.__seqs[2]) /
                                        len(self.__seqs[2][idx]))

        if seq_utils.count_pattern(new_cds, _INVALID_PATTERN) == 0:
            self.__seqs_new[2][idx] = new_cds

    def __get_valid_rand_seq(self, length, attempts=0, max_attempts=1000):
        '''Returns a valid random sequence of supplied length.'''
        if attempts > max_attempts - 1:
            raise ValueError('Unable to generate valid random sequence of ' +
                             'length ' + str(length))

        seq = ''.join([_rand_nuc() for _ in range(0, length)])

        if seq_utils.count_pattern(seq, _INVALID_PATTERN) + \
                seq_utils.count_pattern(seq, _START_CODON_PATTERN) == 0:
            return seq

        return self.__get_valid_rand_seq(length, attempts + 1, max_attempts)

    def __repr__(self):
        # return '%r' % (self.__dict__)
        cai = [self.__cod_opt.get_cai(prot_seq) for prot_seq in self.__seqs[2]]
        invalid_patterns = [seq_utils.count_pattern(seq, _INVALID_PATTERN)
                            for seq in self.__seqs]
        start_codons = [seq_utils.count_pattern(seq, _START_CODON_PATTERN)
                        for seq in self.__seqs]

        return str(cai) + '\t' + \
            str(invalid_patterns) + '\t' + \
            str(start_codons) + '\t' + \
            '' if self.__dgs is None else str(_get_tirs(self.__dgs)) + '\t' + \
            self.__seqs[0] + ' ' + self.__seqs[1] + ' ' + \
            str(len(self.__seqs[2])) + ' '

    def __print__(self):
        return self.__repr__

    def print_sol(self):
        '''Prints the solution.'''
        tirs = _get_tirs(self.__dgs)
        for i, cds in enumerate(self.__seqs[2]):
            print str(self.__dgs[i]) + '\t' + str(tirs[i]) + '\t' + \
                self.__seqs[0] + '\t' + self.__seqs[1] + '\t' + cds + '\t' + \
                self.__seqs[3] + '\t' + \
                ('' if self.__seqs[4] is None else self.__seqs[4])


class PartsThread(JobThread):
    '''Wraps a Parts optimisation job into a thread.'''

    def __init__(self, job_id, protein_ids, taxonomy_id, len_target,
                 tir_target):
        self.__solution = PartsSolution(protein_ids, taxonomy_id, len_target,
                                        tir_target)
        JobThread.__init__(self, job_id)

    def run(self):
        sim_ann = SimulatedAnnealer(self.__solution, verbose=True)
        sim_ann.add_listener(self)
        sim_ann.optimise()


def _get_tirs(dgs):
    '''Gets the translation initiation rate.'''
    return [_RBS_CALC.calc_expression_level(d_g) for d_g in dgs]


def _replace(sequence, pos, nuc):
    '''Replace nucleotide at pos with nuc.'''
    return sequence[:pos] + nuc + sequence[pos + 1:]


def _rand_nuc():
    '''Returns a random nucleotide.'''
    return random.choice(['A', 'T', 'G', 'C'])


def main(argv):
    '''main method.'''
    sim_ann = SimulatedAnnealer(PartsSolution(argv[5:], argv[1],
                                              len_target=int(argv[2]),
                                              tir_target=float(argv[3])),
                                acceptance=float(argv[4]),
                                verbose=True)
    print sim_ann.optimise()


if __name__ == '__main__':
    main(sys.argv)
