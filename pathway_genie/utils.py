'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from synbiochem.utils.job import JobThread


class PathwayThread(JobThread):
    '''A PathwayThread base class.'''

    def __init__(self, query):
        JobThread.__init__(self)

        self._query = query
        self._results = []

    def _fire_designs_event(self, status, iteration, message=''):
        '''Fires an event.'''
        event = {'update': {'status': status,
                            'message': message,
                            'progress': float(iteration) /
                            len(self._query['designs']) * 100,
                            'iteration': iteration,
                            'max_iter': len(self._query['designs'])},
                 'query': self._query
                 }

        if status == 'finished':
            event['result'] = self._results

        self._fire_event(event)
