'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=no-member
# pylint: disable=wrong-import-order
from collections import defaultdict
import json
import os
import sys
import traceback
import urllib2
import uuid

from Bio import Restriction
from flask import Flask, jsonify, make_response, request, Response
from requests.exceptions import ConnectionError
from synbiochem.utils import seq_utils
from synbiochem.utils.ice_utils import ICEClient
from synbiochem.utils.net_utils import NetworkError

from parts_genie import parts
from pathway_genie import pathway


# Configuration:
DEBUG = True
SECRET_KEY = str(uuid.uuid4())

# Create application:
_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              '../static')
APP = Flask(__name__, static_folder=_STATIC_FOLDER)
APP.config.from_object(__name__)

_MANAGER = pathway.PathwayGenie()
_ORGANISMS = seq_utils.get_codon_usage_organisms(expand=True, verbose=True)

_ICE_IDS = defaultdict(list)


@APP.route('/')
def home():
    '''Renders homepage.'''
    return APP.send_static_file('index.html')


@APP.route('/<path:path>')
def get_path(_):
    '''Renders homepage.'''
    return APP.send_static_file('index.html')


@APP.route('/submit', methods=['POST'])
def submit():
    '''Responds to submission.'''
    return json.dumps({'job_ids': _MANAGER.submit(request.data)})


@APP.route('/progress/<job_id>')
def progress(job_id):
    '''Returns progress of job.'''
    return Response(_MANAGER.get_progress(job_id),
                    mimetype='text/event-stream')


@APP.route('/cancel/<job_id>')
def cancel(job_id):
    '''Cancels job.'''
    return _MANAGER.cancel(job_id)


@APP.route('/groups/', methods=['POST'])
def get_groups():
    '''Gets groups from search term.'''
    ice_client = _connect_ice(request)
    data = json.loads(request.data)
    return json.dumps([group['label']
                       for group in ice_client.search_groups(data['term'])])


@APP.route('/organisms/', methods=['POST'])
def get_organisms():
    '''Gets organisms from search term.'''
    query = json.loads(request.data)

    url = "https://www.denovodna.com/software/return_species_list?term=" + \
        query['term']

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
    return json.dumps([str(enz) for enz in Restriction.AllEnzymes])


@APP.route('/ice/connect', methods=['POST'])
def connect_ice():
    '''Connects to ICE.'''
    try:
        ice_client = _connect_ice(request)

        for typ in ['PLASMID', 'STRAIN']:
            resp = ice_client.advanced_search('*', typ, 2**8)
            _ICE_IDS[typ] = [result['entryInfo']['partId']
                             for result in resp['results']]

        return json.dumps({'connected': True})
    except ConnectionError, err:
        print str(err)
        message = 'Unable to connect. Is the URL correct?'
        status_code = 503
    except NetworkError, err:
        print str(err)
        message = 'Unable to connect. Are the username and password correct?'
        status_code = err.get_status()

    response = jsonify({'message': message})
    response.status_code = status_code
    return response


@APP.route('/ice/search/', methods=['POST'])
def search_ice():
    '''Search ICE.'''
    try:
        data = json.loads(request.data)
        return json.dumps([ice_id
                           for ice_id in _ICE_IDS[data['type']]
                           if data['term'] in ice_id])
    except ConnectionError, err:
        print str(err)
        message = 'Unable to connect. Is the URL correct?'
        status_code = 503
    except NetworkError, err:
        print str(err)
        message = 'Unable to connect. Are the username and password correct?'
        status_code = err.get_status()

    response = jsonify({'message': message})
    response.status_code = status_code
    return response


@APP.route('/uniprot/<query>')
def search_uniprot(query):
    '''Search Uniprot.'''
    fields = ['entry name', 'protein names', 'sequence', 'ec', 'organism',
              'organism-id']
    result = seq_utils.search_uniprot(query, fields)
    return json.dumps(result)


@APP.route('/twist', methods=['POST'])
def get_twist_plate():
    '''Get Twist plate order.'''
    data = json.loads(request.data)
    content = 'attachment; filename=mycsv.csv'

    csv = 'foo,bar,baz\nhai,bai,crai\n'
    response = make_response(csv)
    response.headers['Content-Disposition'] = content
    response.mimetype = 'text/csv'

    return response


@APP.errorhandler(Exception)
def handle_error(error):
    '''Handles errors.'''
    APP.logger.error('Exception: %s', (error))
    traceback.print_exc()

    response = jsonify({'message': traceback.format_exc()})
    response.status_code = 500
    return response


def _connect_ice(req):
    '''Connects to ICE.'''
    data = json.loads(req.data)

    return ICEClient(data['ice']['url'],
                     data['ice']['username'],
                     data['ice']['password'])
