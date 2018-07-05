'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import random
import sys
import time

import requests


_APITOKEN = '''
    eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjQwMDc4OGU1LWI1MDUtNGVmNC05
    NTQ4LThmNmIxZDgwYTMzNiIsInVzZXJfaWQiOiIzM2JlYTFkZC0yYjYzLTQ5ZGMtYTgwMy0zN
    jYzMTM4OWU3YTUiLCJ1c2VybmFtZSI6ImdpbmtnbyIsImV4cCI6MTYwODI4OTQ1M30.w6JiWO
    1937Ewv21orXEJKwPvGSftgPNxPRnq1pkno1w
    '''

_EUTOKEN = '''
    eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImE0aTB4MDAwMDAwMDFHNUFBSSIs
    ImVtYWlsIjoibmtyYWtvd3NraUB0d2lzdGJpb3NjaWVuY2UuY29tIiwiYWNjb3VudCI6IjAwM
    TMxMDAwMDFwNVVZcEFBTSIsImFjY291bnRfYWRtaW4iOnRydWUsInJlYWQiOnRydWUsIndyaX
    RlIjp0cnVlLCJleHAiOjE2MDgzMTA4NjV9.eBH4t4uQCaJ3hRSHbT6QsZVFfMNy56nIjPKpp4
    Zg-jw
    '''

_HOST = 'https://twist-api.twistbioscience-staging.com'


class TwistClient(object):
    '''Class to define client for the Twist API.'''

    def __init__(self, email):
        self.__email = email
        self.__session = requests.Session()
        self.__session.headers.update(
            {'Authorization': 'JWT ' + ''.join(_APITOKEN.split()),
             'X-End-User-Token': ''.join(_EUTOKEN.split()),
             'Accept-Encoding': 'json'})

        self.__user_data = self.__get('{}/v1/users/{}/')

        return self.__user_data

    def get_addresses(self):
        '''Get addresses.'''
        return self.__get('{}/v1/users/{}/addresses/')

    def get_payments(self):
        '''Get payments.'''
        return self.__get('{}/v1/users/{}/payments/')

    def get_accounts(self):
        '''Get accounts.'''
        return self.__get('{}/v1/users/{}/accounts/')

    def get_vectors(self):
        '''Get vectors.'''
        return self.__user_data['vectors']

    def submit_constructs(self, constructs):
        '''Submit constructs.'''
        resp = self.__get('{}/v1/users/{}/constructs/',
                          json=constructs)

        return self.__get_scores([i['id'] for i in resp.json()])

    def get_scores(self, ids):
        '''Get scores.'''
        data = []

        while set([datum['id'] for datum in data]) != set(ids):
            data = self.__get('{}/v1/users/{}/constructs/describe/',
                              params={'scored': True,
                                      'id__in': ','.join(ids)})
            time.sleep(100)

        return data

    def get_quote(self, construct_ids, external_id, address_id):
        '''Get quote.'''
        json = {'external_id': external_id,
                'containers': [{'constructs': [
                    {'id': id_, 'index': index}
                    for id_, index in enumerate(construct_ids)],
                    'type': '96_WELL_PLATE',
                    'fill_method': 'VERTICAL'}],
                'shipment': {'recipient_address_id': address_id,
                             'preferences': {
                                 'shipment_method': 'MULTIPLE_SHIPMENTS'}},
                'vectors': [],
                'cloning_strategies': [],
                'advanced_options': {}}

        resp = self.__.post('{}/v1/users/{}/quotes/', json=json)

        return resp.json()['id']

    def check_quote(self, quote_id):
        '''Check quote.'''
        data = None

        while not data or data['status_info']['status'] == 'PENDING':
            resp = self.__get('{}/v1/users/{}/quotes/%s/') % quote_id
            quote_data = resp.json()
            time.sleep(100)

        if quote_data['status_info']['status'] == 'SUCCESS':
            return quote_data['status_info']['status']

        raise ValueError(quote_data['status_info']['status'])

    def submit_order(self, quote_id):
        '''Submit order.'''
        payments = self.__get_payments()

        if payments:
            return self.__post('{}/v1/users/{}/orders/',
                               json={'quote_id': quote_id,
                                     'payment_method_id': payments[0]['id']})
        else:
            raise ValueError('No payment data available.')

    def get_constructs_file(self, sequences, names, filename,
                            typ='NON_CLONED_GENE'):
        '''Get constructs file.'''
        constructs = []

        for idx, (seq, name) in enumerate(zip(sequences, names)):
            construct = {'sequences': seq,
                         'name': name,
                         'type': typ,
                         'insertion_point_mes_uid': 'na',
                         'vector_mes_uid': 'na',
                         'column': idx / 8,
                         'row': idx % 8,
                         'plate': idx / 96}

            constructs.append(construct)

        with open(filename, 'w+') as fle:
            fle.write(json.dumps(constructs))

    def __get(self, url, **kwargs):
        '''GET method.'''
        resp = self.__session.get(url.format(_HOST, self.__email), **kwargs)
        return check_response(resp, 200)

    def __post(self, url, **kwargs):
        '''POST method.'''
        resp = self.__session.post(url.format(_HOST, self.__email), **kwargs)
        return check_response(resp, 200)


def check_response(resp, target):
    '''Check response.'''
    if not resp.status_code == target:
        raise Exception('{}: {}'.format(resp.content, resp.status_code))

    return resp.json()


def main(argv):
    '''''main method.'''
    client = TwistClient(argv[0])

    if argv[1] == '-d':
        print client.get_addresses()

    elif argv[1] == '-p':
        print client.get_payments()

    elif argv[1] == '-g':
        sequences = []
        names = []

        for i in range(0, 5):
            sequences.append(''.join(
                [random.choice('ACTG')
                 for _ in range(0, random.randint(150, 1500))]))

            names.append('seq{}'.format(i))

        client.get_constructs_file(sequences, names, argv[2])

    elif argv[1] == '-a':
        print client.get_accounts()

    elif argv[1] == '-v':
        return client.get_vectors()

    elif argv[1] == '-c':
        with open(argv[2]) as fle:
            resp = client.submit_constructs(json.loads(fle).read())

        if len(argv) > 3 and argv[3] == '-q':
            quote_id = client.get_quote(resp['ids'])
            print client.check_quote(quote_id)

            if len(argv) > 4 and argv[4] == '-o':
                print client.submit_order(quote_id)

    elif argv[1] == '-m':
        print client.submit_order(argv[2])


if __name__ == '__main__':
    main(sys.argv[1:])
