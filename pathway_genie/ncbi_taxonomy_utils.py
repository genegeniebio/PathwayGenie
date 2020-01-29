'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=invalid-name
from collections import defaultdict
import os
import sys
import tarfile
import tempfile
import requests


def get_taxonomy_ids(parent_id, out_dir):
    '''Get taxonomy ids.'''
    tree = _load(out_dir)

    child_ids = []
    _get_child_ids(tree, parent_id, child_ids)
    return child_ids


def _load(out_dir):
    '''Loads NCBI Taxonomy data.'''
    nodes_filename = _get_ncbi_taxonomy_files(out_dir)
    return _parse_nodes(nodes_filename)


def _get_child_ids(tree, parent_id, child_ids):
    '''Get child ids.'''
    child_ids.extend(tree[parent_id])

    for child_id in tree[parent_id]:
        _get_child_ids(tree, child_id, child_ids)


def _get_ncbi_taxonomy_files(out_dir):
    '''Downloads and extracts NCBI Taxonomy files.'''
    with tarfile.open(_get_file(out_dir), 'r:gz') as tr:
        temp_dir = tempfile.gettempdir()
        tr.extractall(temp_dir)

    return os.path.join(temp_dir, 'nodes.dmp')


def _get_file(out_dir):
    '''Get file.'''
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    filename = 'taxdump.tar.gz'
    path = os.path.join(out_dir, filename)

    if not os.path.exists(path):
        url_dir = 'ftp://ftp.ncbi.nih.gov/pub/taxonomy/'

        resp = requests.get('%s%s' % (url_dir, filename), allow_redirects=True)

        with open(path, 'w') as target_file:
            target_file.write_bytes(resp.content)

    return path


def _parse_nodes(filename):
    '''Parses nodes file.'''
    tree = defaultdict(list)

    with open(filename, 'r') as textfile:
        for line in textfile:
            tokens = [x.strip() for x in line.split('|')]
            tree[tokens[1]].append(tokens[0])

    return tree


def main(argv):
    '''main method'''
    get_taxonomy_ids(*argv)


if __name__ == "__main__":
    main(sys.argv[1:])
