'''
PartsGenie (c) University of Manchester 2017

PartsGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import sys
import time

from parts_genie.parts import PartsThread
from pathway_genie.pathway import PathwayGenie


class PartsGenieClient(object):
    '''Simple client class for running PartsGenie jobs from JSON file.'''

    def __init__(self):
        self.__event = None
        self.__pathway_genie = PathwayGenie()

    def submit(self, filename, ice_params=None):
        '''Submits PartsGenie job.'''
        self.__event = None

        results = []

        with open(filename) as fle:
            query = json.load(fle)

        # Do job in new thread, return result when completed:
        thread = PartsThread(query, verbose=True)
        thread.add_listener(self)
        thread.start()

        while len(results) < len(query['designs']):
            if self.__event:
                if self.__event['update']['status'] == 'finished':
                    results.append(self.__event['result'])
                elif self.__event['update']['status'] == 'cancelled' or \
                        self.__event['update']['status'] == 'error':
                    results.append(None)
                    raise ValueError()

            time.sleep(1)

        if ice_params is not None:
            # Saves results to ICE:
            data = {'ice': {}}
            data['ice']['url'] = ice_params[0]
            data['ice']['username'] = ice_params[1]
            data['ice']['password'] = ice_params[2]
            data['ice']['groups'] = ice_params[3]
            data['result'] = [val for result in results for val in result]
            return self.__pathway_genie.save(data)

        return results

    def event_fired(self, event):
        '''Responds to event being fired.'''
        self.__event = event


def main(args):
    '''main method.'''
    client = PartsGenieClient()
    ice_params = None if len(args) == 1 else args[1:]
    client.submit(args[0], ice_params)


if __name__ == "__main__":
    main(sys.argv[1:])
