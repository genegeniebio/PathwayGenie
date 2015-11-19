'''
Created on 19 Nov 2015

@author: neilswainston
'''
import ast
from flask import Flask, render_template, request
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
    sim_ann.optimise(RBSSolution(protein_ids, taxonomy_id, len_target,
                                 tir_target), verbose=True)
    return render_template('submitted.html')


if __name__ == '__main__':
    app.run()
