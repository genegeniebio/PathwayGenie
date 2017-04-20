'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

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
from requests.exceptions import ConnectionError
from synbiochem.utils import seq_utils
from synbiochem.utils.ice_utils import ICEClient
from synbiochem.utils.net_utils import NetworkError

from parts_genie import parts

from . import pathway_genie


# Configuration:
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# Create application:
_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              '../static')
APP = Flask(__name__, static_folder=_STATIC_FOLDER)
APP.config.from_object(__name__)

_MANAGER = pathway_genie.PathwayGenie()
_ORGANISMS = seq_utils.get_codon_usage_organisms(expand=True, verbose=True)


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


@APP.route('/save', methods=['POST'])
def save():
    '''Saves result.'''
    return pathway_genie.save(request)


@APP.route('/organisms/<term>')
def get_organisms(term):
    '''Gets organisms from search term.'''
    url = "https://salislab.net/software/return_species_list?term=" + term

    response = urllib2.urlopen(url)
    data = [{'taxonomy_id': _ORGANISMS[term[:term.rfind('(')].strip()],
             'name': term[:term.rfind('(')].strip(),
             'r_rna': term[term.rfind('(') + 1:term.rfind(')')]}
            for term in json.loads(response.read())
            if term[:term.rfind('(')].strip() in _ORGANISMS]

    return json.dumps(data)


@APP.route('/restr_enzymes')
def get_restr_enzymes():
    '''Gets supported restriction enzymes.'''
    return json.dumps([{'name': str(enz),
                        'site': seq_utils.ambiguous_to_regex(enz.site)}
                       for enz in Restriction.AllEnzymes])


@APP.route('/ice/search/<term>')
def search_ice(term, url, username, password):
    '''Searches ICE database.'''
    ice_client = ICEClient(url, username, password)
    return ice_client.search(term, limit=10)


@APP.route('/ice/connect', methods=['POST'])
def connect_ice():
    '''Searches ICE database.'''
    data = json.loads(request.data)

    try:
        ICEClient(data['ice']['url'],
                  data['ice']['username'],
                  data['ice']['password'])
        connected = True
    except (ConnectionError, NetworkError):
        connected = False

    return json.dumps({'connected': connected})


@APP.errorhandler(Exception)
def handle_exception(err):
    '''Exception handling method.'''
    message = err.__class__.__name__ + ': ' + str(err)
    APP.logger.error('Exception: ' + message)
    response = jsonify({'message': message})
    response.status_code = 500
    return response
