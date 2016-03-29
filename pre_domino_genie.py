'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import os
import sys

from synbiochem.utils import sbol_utils, ice_utils
from synbiochem.utils.ice_utils import ICEClient, ICEEntry
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


def _write_results(seq_source, pair_oligos, filename):
    '''Writes bridging oligos to file in Excel (tabbed) format.'''
    result_file = open(filename, 'w+')

    oligo_pairs = {}

    for pair, oligo in pair_oligos.iteritems():
        result_line = '\t'.join(list(pair) + oligo)
        print result_line
        result_file.write(result_line + '\n')

        if oligo[4] not in oligo_pairs:
            oligo_pairs[oligo[4]] = [list(pair)]
        else:
            oligo_pairs[oligo[4]].append(list(pair))

    result_file.write('\n')

    for oligo, pairs in oligo_pairs.iteritems():
        name = seq_source.get_name(
            pairs[0][0]) + '_' + seq_source.get_name(pairs[0][1])
        pairs_str = [pair[0] + '_' + pair[1] for pair in pairs]
        result_file.write('\t'.join([name] + [oligo] + pairs_str) + '\n')

    result_file.close()


def main(args):
    '''main method.'''
    ice_client = ICEClient(args[2], args[3], args[4])

    for filename in args[5:]:
        designs = get_designs(filename)
        design_id_plasmid, design_id_dominioes = get_dominoes(ice_client,
                                                              designs,
                                                              float(args[0]),
                                                              args[1])

        for design_id, plasmid in design_id_plasmid.iteritems():
            metadata = {'id': ice_utils.get_ice_number(design_id),
                        'status': 'complete'}
            ice_entry = ICEEntry(plasmid, 'PLASMID', metadata)
            plasmid.write(
                '/Users/neilswainston/Downloads/' + design_id + '.xml')
            ice_client.set_ice_entry(ice_entry)
            print design_id

        # _write_results(ice_client, pair_oligos,
        #               os.path.splitext(filename)[0] + '_dominoes.xls')

if __name__ == '__main__':
    main(sys.argv[1:])
