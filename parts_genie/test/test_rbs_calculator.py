'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import unittest

import parts_genie.nupack_utils as nupack_calc
from parts_genie.rbs_calculator import RbsCalculator


class TestRbsCalculator(unittest.TestCase):
    '''Test class for RbsCalculator.'''

    def test_calc_kinetic_score(self):
        '''Tests calc_kinetic_score method.'''
        r_rna = 'acctcctta'
        calc = RbsCalculator(r_rna, nupack_calc)

        m_rna = 'TTCTAGAGGGGGGATCTCCCCCCAAAAAATAAGAGGTACACATGACTAAAACTTTCA' + \
            'AAGGCTCAGTATTCCCACTGAG'

        start_pos = 41
        self.assertAlmostEqual(calc.calc_kinetic_score(m_rna, start_pos),
                               0.628571428571)

    def test_get_calc_dgs(self):
        '''Tests calc_dgs method.'''
        r_rna = 'acctcctta'
        calc = RbsCalculator(r_rna, nupack_calc)

        m_rna = 'TTCTAGAGGGGGGATCTCCCCCCAAAAAATAAGAGGTACACATGACTAAAACTTTCA' + \
            'AAGGCTCAGTATTCCCACTGAG'

        dgs = calc.calc_dgs(m_rna)
        self.assertEqual(dgs.keys(), [41, 74])
        self.assertAlmostEqual(dgs[41][0], -8.070025836938619)
        self.assertAlmostEqual(dgs[74][0], 3.312588580920539)

        dgs = calc.calc_dgs(m_rna)
        self.assertEqual(dgs.keys(), [41, 74])
        self.assertAlmostEqual(dgs[41][0], -8.070025836938619)
        self.assertAlmostEqual(dgs[74][0], 3.312588580920539)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
