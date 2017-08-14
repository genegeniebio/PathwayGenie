'''
PartsGenie (c) University of Manchester 2017

PartsGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=attribute-defined-outside-init
# pylint: disable=no-self-use
import json
import os
import time
import unittest

from parts_genie.parts import PartsThread


class TestPartsThread(unittest.TestCase):
    '''Test class for PartsThread.'''

    def test_submit_simple(self):
        '''Tests submit method with simple query.'''
        self.__test_submit('simple_query.json')

    def test_submit_complex(self):
        '''Tests submit method with complex query.'''
        self.__test_submit('complex_query.json')

    def test_submit_promoter(self):
        '''Tests submit method with simple query.'''
        self.__test_submit('promoter_query.json')

    def test_submit_multiple(self):
        '''Tests submit method with simple query.'''
        self.__test_submit('multiple_query.json')

    def event_fired(self, event):
        '''Responds to event being fired.'''
        self.__status = event['update']['status']

    def __test_submit(self, filename):
        '''Tests submit method.'''
        self.__status = None
        directory = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(directory, filename)

        with open(filename) as fle:
            query = json.load(fle)

        # Do job in new thread, return result when completed:
        thread = PartsThread(query, idx=0, verbose=True)
        thread.add_listener(self)
        thread.start()

        while True:
            if self.__status == 'finished' or \
                    self.__status == 'cancelled' or \
                    self.__status == 'error':
                break

            time.sleep(1)

        self.assertEqual(self.__status, 'finished')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
