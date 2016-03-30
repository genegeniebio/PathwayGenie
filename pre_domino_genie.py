'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import os
import sys

from synbiochem.utils import sbol_utils, ice_utils
from synbiochem.utils.ice_utils import ICEClient
from synbiochem.utils.net_utils import NetworkError
import dominogenie
import synbiochem.utils


def get_designs(filename):
    '''Reads design file from DOE.'''
    designs = {}
    with open(filename) as designfile:
        for line in designfile:
            line = line.split()
            designs[line[0]] = line[1:] + [line[1]]
    return designs


def get_dominoes(sbol_source, designs, melt_temp, restrict=None):
    '''Designs dominoes (bridging oligos) for LCR.'''
    design_id_plasmid = {}
    design_id_dominoes = {}

    for design_id, design in designs.iteritems():
        ids_docs = [(val, sbol_source.get_sbol_doc(val))
                    for val in design]
        ids_seqs = [(item[0], sbol_utils.get_seq(item[1]))
                    for item in ids_docs]

        # Apply restriction site digestion to PARTs not PLASMIDs.
        # (Assumes PLASMID at positions 1 and -1 - first and last).
        if restrict is not None:
            ids_docs = [ids_docs[0]] + \
                [(item[0], _apply_restrict(item[1], restrict))
                 for item in ids_docs[1:-1]] + \
                [ids_docs[-1]]

        design_id_plasmid[design_id] = \
            sbol_utils.concat([item[1] for item in ids_docs[:-1]])

        oligos = dominogenie.get_dominoes(melt_temp, [item[1]
                                                      for item in ids_seqs])

        pairs = [pair for pair in synbiochem.utils.pairwise(design)]
        design_id_dominoes[design_id] = zip(pairs, oligos)

    return design_id_plasmid, design_id_dominoes


def _apply_restrict(sbol_doc, restrict):
    '''Gets sequence from sequence id, applying restriction site cleavage
    if necessary.'''
    restrict_docs = sbol_utils.apply_restrict(sbol_doc, restrict)

    # This is a bit fudgy...
    # If no digestion occurs, return the single, undigested Document...
    if len(restrict_docs) == 1:
        return restrict_docs[0]
    else:
        # ...else return the digested Document that contains a CDS:
        for restrict_doc in restrict_docs:
            for annot in restrict_doc.annotations:
                if annot.subcomponent.type == sbol_utils.SO_CDS or \
                        annot.subcomponent.type == sbol_utils.SO_PROM:
                    return restrict_doc

    raise ValueError('No CDS or promoter found in restriction site cleaved ' +
                     'sequence.')


def _write_plasmids(ice_client, design_id_plasmid):
    '''Writes plasmids to ICE.'''
    for design_id, plasmid in design_id_plasmid.iteritems():
        ice_entry = ice_client.get_ice_entry(design_id)
        ice_entry.set_value('status', 'Complete')
        ice_client.set_ice_entry(ice_entry)

        metadata = ice_entry.get_metadata()
        filename = '/Users/neilswainston/Downloads/' + design_id + '.xml'
        plasmid.write(filename)

        try:
            ice_client.upload_seq_file(metadata['type']['recordId'],
                                       'plasmid',
                                       filename)
            print 'OK ' + filename
        except NetworkError, err:
            # Error thrown if sequence exists: deleteSequence?
            print err


def _write_dominoes(design_id_dominoes, filename):
    '''Writes dominoes (eventually to ICE), currently to file in Excel
    (tabbed) format.'''
    recipe_file = open(filename + '_recipes.xls', 'w+')

    domino_pairs = {}

    line = '\t'.join(['Plasmid id',
                      'Part 1 id',
                      'Part 2 id',
                      'Domino id',
                      'Domino seq',
                      'Domino 1 seq',
                      'Domino 1 Tm',
                      'Domino 2 seq',
                      'Domino 2 Tm'])

    print line
    recipe_file.write(line + '\n')

    for design_id, dominoes in design_id_dominoes.iteritems():
        for domino in dominoes:
            pair = list(domino[0])
            seq = domino[1][0][0] + domino[1][1][0]
            line = '\t'.join([design_id] +
                             pair +
                             [_get_domino_id(seq, pair, domino_pairs)] +
                             [seq] +
                             [str(val) for sublist in list(domino[1])
                              for val in list(sublist)])
            print line
            recipe_file.write(line + '\n')

        recipe_file.write('\n')

    recipe_file.close()

    domino_file = open(filename + '_dominoes.xls', 'w+')
    domino_file.write('\t'.join(['Domino id', 'Domino seq', 'Pairs']) + '\n')
    for domino, pairs in domino_pairs.iteritems():
        name = '_'.join(pairs[0])
        pairs_str = ', '.join([pair[0] + '_' + pair[1] for pair in pairs])
        domino_file.write('\t'.join([name, domino, pairs_str]) + '\n')

    domino_file.close()


def _get_domino_id(seq, pair, domino_pairs):
    '''Gets a temporary domino id.'''
    if seq not in domino_pairs:
        domino_pairs[seq] = [pair]
    else:
        domino_pairs[seq].append(pair)

    return '_'.join(domino_pairs[seq][0])


def _get_ice_url(ice_id):
    '''Returns an ICE url.'''
    return 'https://ice.synbiochem.co.uk/entry/' + \
        ice_utils.get_ice_number(ice_id)


def main(args):
    '''main method.'''
    ice_client = ICEClient(args[2], args[3], args[4])

    for filename in args[5:]:
        designs = get_designs(filename)
        design_id_plasmids, design_id_dominoes = get_dominoes(ice_client,
                                                              designs,
                                                              float(args[0]),
                                                              args[1])

        _write_dominoes(design_id_dominoes, os.path.splitext(filename)[0])

        # _write_plasmids(ice_client, design_id_plasmids)

if __name__ == '__main__':
    main(sys.argv[1:])
