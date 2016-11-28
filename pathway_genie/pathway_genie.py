'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import os

from parts_genie.parts import PartsThread
from synbiochem.utils import sbol_utils
from . import sbol_writer


class PathwayGenie(object):
    '''Class to run PathwayGenie application.'''

    def __init__(self, sbol_dir):
        self.__sbol_dir = sbol_dir

        if not os.path.exists(self.__sbol_dir):
            os.makedirs(self.__sbol_dir)

    def get_thread(self, query):
        '''Gets a thread to run query.'''
        return PartsThread(query, self.__sbol_dir)

    def get_result(self, file_id):
        '''Returns results.'''
        path = os.path.join(self.__sbol_dir, file_id)

        with open(path, 'r') as fle:
            content = fle.read()
            return content, 'text/xml'

    def save(self, req):
        '''Saves results.'''
        ice_entry_urls = []
        req_obj = json.loads(req.data)

        for result in req_obj['result']:
            path = str(os.path.join(self.__sbol_dir, result['data']['file']))

            dna = sbol_utils.read(path)
            url = req_obj['ice']['url']
            url = url[:-1] if url[-1] == '/' else url
            ice_id = sbol_writer.submit(url,
                                        req_obj['ice']['username'],
                                        req_obj['ice']['password'],
                                        dna, result['metadata'])
            ice_entry_urls.append(url + '/entry/' + str(ice_id))

        return ice_entry_urls
