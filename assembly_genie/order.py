'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from assembly_genie.build import BuildGenieBase


def main(args):
    '''main method.'''
    genie = BuildGenieBase({'ice': {'url': args[0],
                                    'username': args[1],
                                    'password': args[2]},
                            'ice_ids': args[3:]})

    entries = genie.get_order()

    for entry in entries:
        print '\t'.join([str(val) if val else '' for val in entry])


if __name__ == '__main__':
    main(sys.argv[1:])
