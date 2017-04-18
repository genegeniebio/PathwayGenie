'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=fixme
from synbiochem.utils.job import JobThread


class SbcDoeThread(JobThread):
    '''Runs a SBC-DoE job.'''

    def __init__(self, query):
        JobThread.__init__(self)
        self.__query = query
        self.__result = None

    def run(self):
        '''Runs SBC-DoE job.'''

        iteration = 0
        self.__fire_event('running', iteration, 'Running...')

        # TODO: implement job.

        if self._cancelled:
            self.__fire_event('cancelled', iteration, message='Job cancelled')
        else:
            self.__fire_event('finished', iteration, message='Job completed')

    def __fire_event(self, status, iteration, max_iter=10, message=''):
        '''Fires an event.'''
        event = {'update': {'status': status,
                            'message': message,
                            'progress': iteration / max_iter * 100,
                            'iteration': iteration,
                            'max_iter': max_iter},
                 'query': self.__query
                 }

        if status == 'finished':
            event['result'] = self.__result

        self._fire_event(event)
