'''
PartsGenie (c) University of Manchester 2015

PartsGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import os
import sys
import traceback
import urllib2
import uuid

from Bio import Restriction
from flask import Flask, jsonify, request, Response

from parts_genie import parts
from parts_genie.flask_utils import FlaskManager
from synbiochem.utils import seq_utils


# Configuration:
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# Create application:
_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              '../static')
APP = Flask(__name__, static_folder=_STATIC_FOLDER)
APP.config.from_object(__name__)

_RESULTS_DIR = os.path.join(_STATIC_FOLDER, 'sbol/')
_ENGINE = parts.PartsGenie(_RESULTS_DIR)
_MANAGER = FlaskManager(_ENGINE)
_ORGANISMS = seq_utils.get_codon_usage_organisms()


@APP.route('/')
def home():
    '''Renders homepage.'''
    return APP.send_static_file('index.html')


@APP.route('/submit', methods=['POST'])
def submit():
    '''Responds to submission.'''
    return _MANAGER.submit(request)


@APP.route('/progress/<job_id>')
def progress(job_id):
    '''Returns progress of job.'''
    return _MANAGER.get_progress(job_id)


@APP.route('/cancel/<job_id>')
def cancel(job_id):
    '''Cancels job.'''
    return _MANAGER.cancel(job_id)


@APP.route('/result/<file_id>')
def get_result(file_id):
    '''Gets result file.'''
    content, mimetype = _MANAGER.get_result(file_id)
    return Response(content, mimetype=mimetype)


@APP.route('/save', methods=['POST'])
def save():
    '''Saves result.'''
    return _MANAGER.save(request)


@APP.route('/organisms/<term>')
def get_organisms(term):
    '''Gets organisms from search term.'''
    url = "https://salislab.net/software/return_species_list?term=" + term

    response = urllib2.urlopen(url)
    data = [{'name': term[:term.rfind('(')].strip(),
             'r_rna': term[term.rfind('(') + 1:term.rfind(')')]}
            for term in json.loads(response.read())
            if term[:term.rfind('(')].strip() in _ORGANISMS]

    return json.dumps(data)


@APP.route('/restr_enzymes')
def get_restr_enzymes():
    '''Gets supported restriction enzymes (sequences to exclude).'''
    return json.dumps([{'name': str(enz),
                        'site': seq_utils.ambiguous_to_regex(enz.site)}
                       for enz in Restriction.AllEnzymes])


@APP.errorhandler(Exception)
def handle_exception(err):
    '''Exception handling method.'''
    response = jsonify({'message': err.__class__.__name__ + ': ' + str(err)})
    response.status_code = 500
    return response
