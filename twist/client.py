'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
import random
import sys
import time
import uuid
import requests


_APITOKEN = '''
    eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjI2Y2QzNmU3LTBiNWEtNGUwMC1h
    NTc5LWE5ZWYxYzMxOGJiNiIsInVzZXJfaWQiOiJhZmQ0MTdhNi02YjUwLTQ3ODEtYWNjMC00M
    mJlNjhiYmEyZGYiLCJ1c2VybmFtZSI6Im1hbmNoZXN0ZXJfdW5pX2FwaSIsImV4cCI6MTYxMT
    QxMzUwNH0.WtfTiuBhWWxxQCgqzk5v8uoY3bbWKYoAfKlobDw9gvs
    '''

_EUTOKEN = '''
    eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6ImE0azBtMDAwMDAwOFJFYUFBTSIs
    ImVtYWlsIjoibmVpbC5zd2FpbnN0b25AbWFuY2hlc3Rlci5hYy51ayIsImFjY291bnQiOiIwM
    DEzMTAwMDAxY1NDRVRBQTQiLCJhY2NvdW50X2FkbWluIjp0cnVlLCJyZWFkIjp0cnVlLCJ3cm
    l0ZSI6dHJ1ZSwiZXhwIjoxNjAyNzczNzM0fQ.Ix1BMjpfufnqXMd8VXotm4Pimq10IBk9sZgA
    N-29bBo
    '''

_HOST = 'https://twist-api.twistbioscience-staging.com/'


class TwistClient(object):
    '''Class to define client for the Twist API.'''

    def __init__(self, email, password, username='manchester_uni_api'):
        self.__password = password
        self.__email = email
        self.__username = username
        self.__session = requests.Session()
        self.__session.headers.update(
            {'Authorization': 'JWT ' + ''.join(_APITOKEN.split()),
             'X-End-User-Token': ''.join(_EUTOKEN.split()),
             'Accept-Encoding': 'json'})

    def get_accounts(self):
        '''Get accounts.'''
        return self.__get(self.__get_email_url('v1/accounts/'))

    def get_prices(self):
        '''Get prices.'''
        return self.__get('v1/prices/')

    def get_user_data(self):
        '''Get user data.'''
        return self.__get(self.__get_email_url('v1/users/{}/'))

    def get_addresses(self):
        '''Get addresses.'''
        return self.__get(self.__get_email_url('v1/users/{}/addresses/'))

    def get_payments(self):
        '''Get payments.'''
        return self.__get(self.__get_email_url('v1/users/{}/payments/'))

    def get_vectors(self):
        '''Get vectors.'''
        return self.get_user_data()['vectors']

    def submit_constructs(self, sequences, names, typ='NON_CLONED_GENE'):
        '''Submit constructs.'''
        constructs = _get_constructs(sequences, names, typ)

        return self.__post(self.__get_email_url('v1/users/{}/constructs/'),
                           constructs, target=201)

    def get_scores(self, ids, max_errors=8):
        '''Get scores.'''
        resp = None
        errors = 0

        while True:
            url = self.__get_email_url('v1/users/{}/constructs/describe/')

            try:
                resp = self.__get(url, {'scored': 'True',
                                        'id__in': ','.join(ids)})

                if set([datum['id'] for datum in resp]) == set(ids):
                    break
            except TwistError, exc:
                errors += 1

                if errors == max_errors:
                    raise exc

            time.sleep(1)

        return resp

    def get_quote(self, construct_ids, external_id, address_id,
                  typ='96_WELL_PLATE', fill_method='VERTICAL',
                  shipment_method='MULTIPLE_SHIPMENTS',
                  vectors=None, cloning_strategies=None):
        '''Get quote.'''
        json = {'external_id': external_id,
                'containers': [{'constructs': [
                    {'index': index, 'id': id_}
                    for index, id_ in enumerate(construct_ids)],
                    'type': typ,
                    'fill_method': fill_method}],
                'shipment': {'recipient_address_id': address_id,
                             'preferences': {
                                 'shipment_method': shipment_method}},
                'vectors': vectors or [],
                'cloning_strategies': cloning_strategies or [],
                'advanced_options': {}}

        url = self.__get_email_url('v1/users/{}/quotes/')
        resp = self.__post(url, json=json, target=201)

        return resp['id']

    def check_quote(self, quote_id):
        '''Check quote.'''
        resp = None

        while True:
            url = self.__get_email_url('v1/users/{}/quotes/%s/') % quote_id
            resp = self.__get(url)

            if resp['status_info']['status'] != 'PENDING':
                break

            time.sleep(100)

        if resp['status_info']['status'] == 'SUCCESS':
            return resp

        raise ValueError(resp['status_info']['status'])

    def submit_order(self, quote_id, payment_id):
        '''Submit order.'''
        return self.__post(self.__get_email_url('v1/users/{}/orders/'),
                           json={'quote_id': quote_id,
                                 'payment_method_id': payment_id})

    def __get_token(self):
        '''Get token.'''
        json = self.__post('/api-token-auth/',
                           {'username': self.__username,
                            'password': self.__password})

        return json['token']

    def __get_email_url(self, url):
        '''Get email URL.'''
        return url.format(self.__email)

    def __get(self, url, params=None):
        '''GET method.'''
        if not params:
            params = {}

        resp = self.__session.get(_HOST + url, params=params)
        return check_response(resp, 200)

    def __post(self, url, json, target=200):
        '''POST method.'''
        resp = self.__session.post(_HOST + url, json=json)
        return check_response(resp, target)


class TwistError(Exception):
    '''Class to represent a TwistException.'''

    def __init__(self, message, status_code):
        Exception.__init__(self, '{}: {}'.format(message, status_code))


def check_response(resp, target):
    '''Check response.'''
    if not resp.status_code == target:
        raise TwistError(resp.content, resp.status_code)

    return resp.json()


def _get_constructs(sequences, names, typ='NON_CLONED_GENE'):
    '''Get constructs.'''
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

    return constructs


def main(args):
    '''''main method.'''
    client = TwistClient(args[0], args[1])

    addresses = client.get_addresses()
    payments = client.get_payments()

    print 'Accounts\t' + str(client.get_accounts())
    print 'Prices\t' + str(client.get_prices())
    print 'User data\t' + str(client.get_user_data())
    print 'Addresses\t' + str(addresses)
    print 'Payments\t' + str(payments)
    print 'Vectors\t' + str(client.get_vectors())

    # Produce dummy order:
    sequences = []
    names = []

    for i in range(0, 5):
        sequences.append(''.join(
            [random.choice('ACTG')
             for _ in range(0, random.randint(300, 1800))]))

        names.append('seq{}'.format(i + 1))

    resp = client.submit_constructs(sequences, names)
    ids = [i['id'] for i in resp]
    print 'Scores\t' + str(client.get_scores(ids))

    quote_id = client.get_quote(ids,
                                external_id=str(uuid.uuid4()),
                                address_id=addresses[0]['id'])

    print 'Quote\t' + str(client.check_quote(quote_id))

    if payments:
        print 'Submission\t' + \
            str(client.submit_order(quote_id, payments[0]['id']))


if __name__ == '__main__':
    main(sys.argv[1:])
