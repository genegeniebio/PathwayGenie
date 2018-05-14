'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import unittest

from scipy.stats.stats import pearsonr
from synbiochem.utils import seq_utils

import parts_genie.nupack_utils as nupack_utils
from parts_genie.rbs_calculator import RbsCalculator
import parts_genie.vienna_utils as vienna_utils


class TestRbsCalculator(unittest.TestCase):
    '''Test class for RbsCalculator.'''

    def test_calc_kinetic_score(self):
        '''Tests calc_kinetic_score method.'''
        r_rna = 'acctcctta'
        nupack_calc = RbsCalculator(r_rna, nupack_utils)
        vienna_calc = RbsCalculator(r_rna, vienna_utils)
        start_pos = 41
        m_rna_len = 79

        results = zip(*[[nupack_calc.calc_kinetic_score(m_rna, start_pos),
                         vienna_calc.calc_kinetic_score(m_rna, start_pos)]
                        for m_rna in _get_random_dna(250, m_rna_len)])

        self.assertTrue(pearsonr(results[0], results[1])[0] > 0.75)

    def test_get_calc_dgs(self):
        '''Tests calc_dgs method.'''
        r_rna = 'acctcctta'
        nupack_calc = RbsCalculator(r_rna, nupack_utils)
        vienna_calc = RbsCalculator(r_rna, vienna_utils)
        m_rna_len = 79
        results = []

        while len(results) < 50:
            try:
                m_rna = _get_random_dna(1, m_rna_len)[0]
                results.append([nupack_calc.calc_dgs(m_rna),
                                vienna_calc.calc_dgs(m_rna)])
            except TypeError:
                pass

        nupack_dgs = []
        vienna_dgs = []

        for row in results:
            self.assertEqual(set(row[0].keys()), set(row[1].keys()))

            for pos, vals in row[0].iteritems():
                nupack_dgs.append(vals[0])
                vienna_dgs.append(row[1][pos][0])

        self.assertTrue(pearsonr(nupack_dgs, vienna_dgs)[0] > 0.75)


def _get_random_dna(number, length):
    '''Get random DNA.'''
    return [seq_utils.get_random_dna(length) for _ in range(number)]


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
