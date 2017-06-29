'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''


def get_designs(filename):
    '''Reads design file from DOE.'''
    designs = []
    with open(filename) as designfile:
        for line in designfile.read().split('\r'):
            tokens = line.split()
            designs.append({'design': tokens + [tokens[0]]})
    return designs
