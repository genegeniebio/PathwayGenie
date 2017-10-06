'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from synbiochem.utils.ice_utils import DNAWriter

from pathway_genie.utils import PathwayThread


class IceThread(PathwayThread):
    '''Runs a save-to-ICE job.'''

    def __init__(self, query):
        PathwayThread.__init__(self, query)

    def run(self):
        '''Saves results.'''
        iteration = 0

        self._fire_designs_event('running', iteration, 'Connecting to ICE...')

        url = self._query['ice']['url']
        self._query['ice']['url'] = url[:-1] if url[-1] == '/' else url

        writer = DNAWriter(self._query['ice']['url'],
                           self._query['ice']['username'],
                           self._query['ice']['password'],
                           self._query['ice'].get('groups', None))

        for result in self._query['designs']:
            ice_id = writer.submit(result)
            self._results.append(url + '/entry/' + str(ice_id))
            iteration += 1
            self._fire_designs_event('running', iteration, 'Saving...')

        if self._cancelled:
            self._fire_designs_event('cancelled', iteration,
                                     message='Job cancelled')
        else:
            self._fire_designs_event('finished', iteration,
                                     message='Job completed')
