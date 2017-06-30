'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from assembly_genie.assembly import AssemblyGenie


def main(args):
    '''main method.'''
    genie = AssemblyGenie({'url': args[0],
                           'username': args[1],
                           'password': args[2]},
                          args[3:])

    for entry_id, entry in genie.export_order().iteritems():
        print '\t'.join([entry_id] + [str(item) for item in entry])


if __name__ == '__main__':
    main(sys.argv[1:])
