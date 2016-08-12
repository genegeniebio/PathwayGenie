'''
synbiochem (c) University of Manchester 2016

synbiochem is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''


def get_designs(filename):
    '''Reads design file from DOE.'''
    designs = {}
    with open(filename) as designfile:
        for line in designfile.read().split('\r'):
            tokens = line.split()
            designs[tokens[0]] = {'design': tokens[1:] + [tokens[1]]}
    return designs
