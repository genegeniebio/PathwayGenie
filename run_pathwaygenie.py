'''
Created on 19 Nov 2015

@author: neilswainston
'''
import ast
import time
from flask import Flask, Response, render_template, request, session
from rbs import RBSSolution
from synbiochemdev.optimisation import simulated_annealing as sim_ann

# configuration
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    protein_ids = ast.literal_eval(request.form['protein_ids'])
    taxonomy_id = '83333'
    len_target = int(request.form['len_target'])
    tir_target = float(request.form['tir_target'])

    session['in_progress'] = True
    return render_template('submitted.html')

    # Do job in new thread, return result when completed:
    sim_ann.optimise(RBSSolution(protein_ids, taxonomy_id, len_target,
                                 tir_target), verbose=True)
    return render_template('finished.html', result=None)


@app.route('/progress')
def get_progress():

    in_progress = True

    def check_progress():
        x = 0
        while in_progress:
            print x
            x = (x + 10) % 100
            time.sleep(1)
            yield "data:" + str(x) + "\n\n"

    return Response(check_progress(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run()
