'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=no-self-use
# pylint: disable=too-few-public-methods
import json
import time
import uuid
from flask import Flask, Response, render_template, request

import parts


# Configuration:
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# Create application:
_APP = Flask(__name__)
_APP.config.from_object(__name__)

_STATUS = {}
_THREADS = {}


@_APP.route('/')
def home():
    '''Renders homepage.'''
    return render_template('index.html')


@_APP.route('/submit', methods=['POST'])
def submit():
    '''Responds to submission.'''
    query = {'protein_ids': [x.strip()
                             for x in request.form['protein_ids'].split(',')],
             'taxonomy_id': '83333',
             'len_target': int(request.form['len_target']),
             'tir_target': float(request.form['tir_target'])}

    # Do job in new thread, return result when completed:
    job_id = str(uuid.uuid4())
    _STATUS[job_id] = {'job_id': job_id, 'progress': 0}
    listener = Listener()
    thread = parts.PartsThread(job_id, query)
    thread.add_listener(listener)
    _THREADS[job_id] = thread
    thread.start()

    return job_id


@_APP.route('/progress/<job_id>')
def progress(job_id):
    '''Returns progress of job.'''
    def _check_progress(job_id):
        '''Checks job progress.'''
        while _STATUS[job_id]['progress'] < 100:
            time.sleep(1)
            yield 'data:' + _get_response(job_id) + '\n\n'

        yield 'data:' + _get_response(job_id) + '\n\n'

    if job_id in _STATUS:
        return Response(_check_progress(job_id), mimetype='text/event-stream')
    else:
        return 'Job ' + job_id + ' unknown or finished.'


@_APP.route('/cancel/<job_id>')
def cancel(job_id):
    '''Cancels job.'''
    _THREADS[job_id].cancel()
    return 'Cancelled: ' + job_id


def _get_response(job_id):
    '''Returns current progress for job id.'''
    return json.dumps(_STATUS[job_id])


class Listener(object):
    '''Simple event listener.'''

    def event_fired(self, event):
        '''Responds to event being fired.'''
        _STATUS[event['job_id']] = event


if __name__ == '__main__':
    _APP.run(threaded=True)
