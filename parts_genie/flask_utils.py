'''
synbiochem (c) University of Manchester 2016

synbiochem is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import time

from flask import Response


class FlaskManager(object):
    '''Class to run Flask application.'''

    def __init__(self, engine):
        self.__engine = engine
        self.__status = {}
        self.__threads = {}

    def submit(self, req):
        '''Responds to submission.'''
        query = json.loads(req.data)

        # Do job in new thread, return result when completed:
        job_id, thread = self.__engine.get_thread(query)
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

    def get_result(self, req):
        '''Gets result file.'''
        return self.__engine.get_result(req)

    def save(self, req):
        '''Saves results.'''
        return json.dumps(self.__engine.save(req))

    def event_fired(self, event):
        '''Responds to event being fired.'''
        self.__status[event['job_id']] = event

    def __get_response(self, job_id):
        '''Returns current progress for job id.'''
        return json.dumps(self.__status[job_id])
