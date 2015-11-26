'''
Created on 19 Nov 2015

@author: neilswainston
'''
# import ast
import time
import uuid
from flask import Flask, Response, copy_current_request_context, \
    render_template, session

import job


# Configuration:
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# Create application:
app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def home():
    '''Renders homepage.'''
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    '''Responds to submission.'''
    # protein_ids = ast.literal_eval(request.form['protein_ids'])
    # taxonomy_id = '83333'
    # len_target = int(request.form['len_target'])
    # tir_target = float(request.form['tir_target'])

    # Do job in new thread, return result when completed:
    session['progress'] = 13

    with app.test_request_context():
        listener = Listener()
        thread = job.JobThread()
        thread.add_listener(listener)
        thread.start()

    return render_template('submitted.html')


@app.route('/progress')
def get_progress():
    '''Returns job progress.'''
    @copy_current_request_context
    def _check_progress():
        '''Checks job progress.'''
        while True:
            print session['progress']
            time.sleep(0.1)
            yield "data:" + str(session['progress']) + "\n\n"

    return Response(_check_progress(), mimetype='text/event-stream')


class Listener(object):
    '''Simple event listener.'''

    def event_fired(self, event):
        '''Responds to event being fired.'''
        session['progress'] = event


if __name__ == '__main__':
    app.run()
