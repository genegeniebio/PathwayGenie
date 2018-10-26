'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import sys

from gevent import wsgi
from pathway_genie import APP


def main(argv):
    '''main method.'''
    port = int(argv[0]) if argv else 5000
    http_server = wsgi.WSGIServer(('', port), APP)
    http_server.serve_forever()


if __name__ == '__main__':
    main(sys.argv[1:])
