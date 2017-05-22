'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import time

from synbiochem.utils.ice_utils import DNAWriter

from parts_genie.parts import PartsThread


# from metabolomics_genie.metabolomics import MetabolomicsThread
class PathwayGenie(object):
    '''Class to run PathwayGenie application.'''

    def __init__(self):
        self.__status = {}
        self.__threads = {}

    def submit(self, data):
        '''Responds to submission.'''
        query = json.loads(data)

        # Do job in new thread, return result when completed:
        thread = _get_thread(query)
        job_id = thread.get_job_id()
        thread.add_listener(self)
        self.__threads[job_id] = thread
        thread.start()

        return job_id

    def get_progress(self, job_id):
        '''Returns progress of job.'''
        def _check_progress(job_id):
            '''Checks job progress.'''
            while (job_id not in self.__status or
                    self.__status[job_id]['update']['status'] == 'running'):
                time.sleep(1)

                if job_id in self.__status:
                    yield 'data:' + self.__get_response(job_id) + '\n\n'

            yield 'data:' + self.__get_response(job_id) + '\n\n'

        return _check_progress(job_id)

    def cancel(self, job_id):
        '''Cancels job.'''
        self.__threads[job_id].cancel()
        return job_id

    def event_fired(self, event):
        '''Responds to event being fired.'''
        self.__status[event['job_id']] = event

    def __get_response(self, job_id):
        '''Returns current progress for job id.'''
        return json.dumps(self.__status[job_id])


def save(data):
    '''Saves results.'''
    ice_entry_urls = []

    url = data['ice']['url']
    url = url[:-1] if url[-1] == '/' else url
    writer = DNAWriter(url,
                       data['ice']['username'],
                       data['ice']['password'],
                       data['ice'].get('groups', None))

    for result in data['result']:
        ice_id = writer.submit(result)
        ice_entry_urls.append(url + '/entry/' + str(ice_id))

    return ice_entry_urls


def _get_thread(query):
    app = query.get('app', 'undefined')

    if app == 'PartsGenie':
        return PartsThread(query)

    raise ValueError('Unknown app: ' + app)
