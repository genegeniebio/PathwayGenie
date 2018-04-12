'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from pathway_genie import APP


def main(argv):
    '''main method.'''
    if argv:
        APP.run(host='0.0.0.0', threaded=True, port=int(argv[0]),
                use_reloader=False)
    else:
        APP.run(host='0.0.0.0', threaded=True, use_reloader=False)


if __name__ == '__main__':
    main(sys.argv[1:])
