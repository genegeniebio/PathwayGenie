'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=wrong-import-order
from collections import defaultdict
from io import BytesIO
import json
import os
import ssl
import sys
import tempfile
import traceback
from urllib.request import urlopen
import uuid
import zipfile

from Bio import Restriction
from flask import Flask, jsonify, make_response, request, Response, send_file
from synbiochem.utils import seq_utils
from synbiochem.utils.ice_utils import ICEClientFactory, get_ice_id, \
    get_ice_number
from synbiochem.utils.net_utils import NetworkError

import pandas as pd
from parts_genie import parts
from pathway_genie import export, pathway


# Configuration:
SECRET_KEY = str(uuid.uuid4())

# Create application:
_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              '../static')
APP = Flask(__name__, static_folder=_STATIC_FOLDER)
APP.config.from_object(__name__)
APP.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

_ICE_CLIENT_FACTORY = ICEClientFactory()
_MANAGER = pathway.PathwayGenie(_ICE_CLIENT_FACTORY)
_ORGANISMS = seq_utils.get_codon_usage_organisms(expand=True, verbose=True)

DEBUG = False
TESTING = False


@APP.route('/')
def home():
    '''Renders homepage.'''
    return APP.send_static_file('index.html')


@APP.route('/<path:path>')
def get_path(path):
    '''Renders homepage.'''
    return_path = path if path.startswith('export') else 'index.html'
    return APP.send_static_file(return_path)


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
                       for group in ice_client.search_groups(data['term'])
                       if data['term'] in group['label']])


@APP.route('/organisms/', methods=['POST'])
def get_organisms():
    '''Gets organisms from search term.'''
    query = json.loads(request.data)

    url = 'https://www.denovodna.com/software/return_species_list?term=' + \
        query['term']

    context = ssl._create_unverified_context()
    response = urlopen(url, context=context)

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
        _connect_ice(request)
        return json.dumps({'connected': True})
    except ConnectionError as err:
        print(str(err))
        message = 'Unable to connect. Is the URL correct?'
        status_code = 503
    except NetworkError as err:
        print(str(err))
        message = 'Unable to connect. Are the username and password correct?'
        status_code = err.get_status()

    response = jsonify({'message': message})
    response.status_code = status_code
    return response


@APP.route('/ice/search/', methods=['POST'])
def search_ice():
    '''Search ICE.'''
    try:
        ice_client = _connect_ice(request)
        data = json.loads(request.data)
        resp = ice_client.advanced_search(data['term'], data['type'], 16)
        return json.dumps([result['entryInfo']['partId']
                           for result in resp['results']
                           if data['term'] in result['entryInfo']['partId']])
    except ConnectionError as err:
        print(str(err))
        message = 'Unable to connect. Is the URL correct?'
        status_code = 503
    except NetworkError as err:
        print(str(err))
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


@APP.route('/export', methods=['POST'])
def export_order():
    '''Export order.'''
    ice_client = _connect_ice(request)
    data = json.loads(request.data)['designs']
    dfs = export.export(ice_client, data)

    return _save_export(dfs)


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

    return _ICE_CLIENT_FACTORY.get_ice_client(data['ice']['url'],
                                              data['ice']['username'],
                                              data['ice']['password'])


def _save_export(dfs):
    '''Save export file, returning the url.'''
    file_id = str(uuid.uuid4()).replace('-', '_')
    dir_name = os.path.join(os.path.join(_STATIC_FOLDER, 'export'), file_id)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    for df in dfs:
        df.to_csv(os.path.join(dir_name, df.name + '.csv'), index=False)

    zip_file = os.path.join(dir_name + '.zip')

    with zipfile.ZipFile(zip_file, 'w') as zf:
        for dirpath, _, filenames in os.walk(dir_name):
            for filename in filenames:
                zf.write(os.path.join(dirpath, filename), filename)

    return json.dumps({'path': 'export/' + file_id + '.zip'})
