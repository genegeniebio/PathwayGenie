'''
PathwayGenie (c) GeneGenie Bioinformatics Ltd. 2018

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from collections import defaultdict
import sys

from sbol import Document


_CDS_SO = 'http://identifiers.org/so/SO:0000316'


def _parse(filenames):
    '''Parse SBOL documents.'''
    docs = [Document() for _ in filenames]

    for doc, filename in zip(docs, filenames):
        doc.read(filename)
        print(doc)

    return docs


def _get_uniprot_docs(docs):
    '''Get uniprot docs.'''
    uniprot_docs = defaultdict(dict)

    for doc_idx, doc in enumerate(docs):
        for comp_def in doc.componentDefinitions:
            if _CDS_SO in comp_def.roles:
                uniprot_docs[comp_def.description][doc_idx] = comp_def.identity

    return uniprot_docs


def main(args):
    '''main method.'''
    docs = _parse(args)
    uniprot_docs = _get_uniprot_docs(docs)
    print(uniprot_docs)


if __name__ == '__main__':
    main(sys.argv[1:])
