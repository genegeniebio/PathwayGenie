'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=no-self-use
# pylint: disable=too-few-public-methods

import time
import uuid
from flask import Flask, Response, render_template

import job


# Configuration:
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# Create application:
_APP = Flask(__name__)
_APP.config.from_object(__name__)

_PROGRESS = {}


@_APP.route('/')
def home():
    '''Renders homepage.'''
    return render_template('index.html')


@_APP.route('/submit', methods=['POST'])
def submit():
    '''Responds to submission.'''
    # protein_ids = ast.literal_eval(request.form['protein_ids'])
    # taxonomy_id = '83333'
    # len_target = int(request.form['len_target'])
    # tir_target = float(request.form['tir_target'])

    # Do job in new thread, return result when completed:
    job_id = str(uuid.uuid4())
    _PROGRESS[job_id] = 0
    listener = Listener()
    thread = job.JobThread(job_id)
    thread.add_listener(listener)
    thread.start()

    def _check_progress(job_id):
        '''Checks job progress.'''
        while _PROGRESS[job_id] < 100:
            print _PROGRESS[job_id]
            time.sleep(1)
            yield "data:" + str(_PROGRESS[job_id]) + "\n\n"

        yield "data:" + str(_PROGRESS[job_id]) + "\n\n"

    return Response(_check_progress(job_id), mimetype='text/event-stream')


class Listener(object):
    '''Simple event listener.'''

    def event_fired(self, event):
        '''Responds to event being fired.'''
        _PROGRESS[event.get_job_id()] = event.get_progress()


if __name__ == '__main__':
    _APP.run()
