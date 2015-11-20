'''
Created on 19 Nov 2015

@author: neilswainston
'''
import ast
import time
import uuid

from flask import Flask, Response, render_template, request

from rbs import RBSThread


# configuration
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def home():
    '''Renders homepage.'''
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    '''Responds to submission.'''
    protein_ids = ast.literal_eval(request.form['protein_ids'])
    taxonomy_id = '83333'
    len_target = int(request.form['len_target'])
    tir_target = float(request.form['tir_target'])

    # Do job in new thread, return result when completed:
    thread = RBSThread(protein_ids, taxonomy_id, len_target, tir_target)
    thread.start()

    return render_template('submitted.html')


@app.route('/progress')
def get_progress():
    '''Returns job progress.'''
    in_progress = True

    def check_progress():
        '''Checks job progress.'''
        prog = 0
        while in_progress:
            print prog
            prog = (prog + 10) % 100
            time.sleep(1)
            yield "data:" + str(prog) + "\n\n"

    return Response(check_progress(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run()
