'''
Created on 19 Nov 2015

@author: neilswainston
'''
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

    return render_template('submitted.html', job_id=job_id)


@_APP.route('/progress/<job_id>')
def get_progress(job_id):
    '''Returns job progress.'''
    def _check_progress(job_id):
        '''Checks job progress.'''
        while True:
            print _PROGRESS[job_id]
            time.sleep(5)
            yield "data:" + str(_PROGRESS[job_id]) + "\n\n"

    return Response(_check_progress(job_id), mimetype='text/event-stream')


class Listener(object):
    '''Simple event listener.'''

    def event_fired(self, event):
        '''Responds to event being fired.'''
        _PROGRESS[event.get_job_id()] = event.get_progress()


if __name__ == '__main__':
    _APP.run()
