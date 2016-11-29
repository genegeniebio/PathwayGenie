'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import time

from flask import Response

from parts_genie.parts import PartsThread

from . import sbol_writer


class PathwayGenie(object):
    '''Class to run PathwayGenie application.'''

    def __init__(self):
        self.__status = {}
        self.__threads = {}

    def submit(self, req):
        '''Responds to submission.'''
        query = json.loads(req.data)

        # Do job in new thread, return result when completed:
        thread = PartsThread(query)
        job_id = thread.get_job_id()
        thread.add_listener(self)
        self.__threads[job_id] = thread
        thread.start()

        return json.dumps({'job_id': job_id})

    def get_progress(self, job_id):
        '''Returns progress of job.'''
        def _check_progress(job_id):
            '''Checks job progress.'''
            while job_id not in self.__status or \
                    self.__status[job_id]['update']['progress'] < 100:
                time.sleep(1)

                if job_id in self.__status:
                    yield 'data:' + self.__get_response(job_id) + '\n\n'

            yield 'data:' + self.__get_response(job_id) + '\n\n'

        return Response(_check_progress(job_id),
                        mimetype='text/event-stream')

    def cancel(self, job_id):
        '''Cancels job.'''
        self.__threads[job_id].cancel()
        return 'Cancelled: ' + job_id

    def event_fired(self, event):
        '''Responds to event being fired.'''
        self.__status[event['job_id']] = event

    def __get_response(self, job_id):
        '''Returns current progress for job id.'''
        return json.dumps(self.__status[job_id])


def save(req):
    '''Saves results.'''
    ice_entry_urls = []
    req_obj = json.loads(req.data)

    for result in req_obj['result']:
        dna = result['data']
        url = req_obj['ice']['url']
        url = url[:-1] if url[-1] == '/' else url
        ice_id = sbol_writer.submit(url,
                                    req_obj['ice']['username'],
                                    req_obj['ice']['password'],
                                    dna, result['metadata'])
        ice_entry_urls.append(url + '/entry/' + str(ice_id))

    return json.dumps(ice_entry_urls)
