'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import os
import sys

from synbiochem.utils import plate_utils, sbol_utils
from synbiochem.utils.ice_utils import ICEClient
from synbiochem.utils.net_utils import NetworkError
import doe
import dominogenie
import synbiochem.utils


def get_dominoes(sbol_source, designs, melt_temp, restricts=None):
    '''Designs dominoes (bridging oligos) for LCR.'''
    design_id_plasmid = {}
    design_id_dominoes = {}

    for design_id, design in designs.iteritems():
        ids_docs = [(val, sbol_source.get_sbol_doc(val))
                    for val in design]

        # Apply restriction site digestion to PARTs not PLASMIDs.
        # (Assumes PLASMID at positions 1 and -1 - first and last).
        if restricts is not None:
            ids_docs = [ids_docs[0]] + \
                [(item[0], _apply_restricts(item[1], restricts))
                 for item in ids_docs[1:-1]] + \
                [ids_docs[-1]]

        design_id_plasmid[design_id] = \
            sbol_utils.concat([item[1] for item in ids_docs[:-1]])

        ids_seqs = [(item[0], sbol_utils.get_seq(item[1]))
                    for item in ids_docs]

        oligos = dominogenie.get_dominoes(melt_temp, [item[1]
                                                      for item in ids_seqs])

        pairs = [pair for pair in synbiochem.utils.pairwise(design)]
        design_id_dominoes[design_id] = zip(pairs, oligos)

    return design_id_plasmid, design_id_dominoes


def _apply_restricts(sbol_doc, restricts):
    '''Gets sequence from sequence id, applying restriction site cleavage
    if necessary.'''
    restrict_docs = sbol_utils.apply_restricts(sbol_doc, restricts)

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
        except NetworkError as err:
            # Error thrown if sequence exists: deleteSequence?
            print err


def _write_dominoes(design_id_dominoes, filename):
    '''Writes dominoes (eventually to ICE), currently to file in Excel
    (tabbed) format.'''
    domino_pairs = _write_overview(design_id_dominoes, filename)

    name_well_pos = _write_dominoes_file(domino_pairs, filename)
    design_id_well_pos = _write_domino_pools_file(design_id_dominoes,
                                                  domino_pairs, name_well_pos,
                                                  filename)
    part_well_pos = _write_parts_file(design_id_dominoes, filename)
    _write_plasmids_file(design_id_dominoes, design_id_well_pos, part_well_pos,
                         filename)


def _write_overview(design_id_dominoes, filename):
    '''Writes an overview file.'''
    overview_file = open(filename + '_overview.xls', 'w+')

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

    overview_file.write(line + '\n')

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

            overview_file.write(line + '\n')

        overview_file.write('\n')

    overview_file.close()

    return domino_pairs


def _write_dominoes_file(domino_pairs, filename):
    '''Writes an order file.'''
    order_file = open(filename + '.xls', 'w+')
    order_file.write(
        '\t'.join(['Well position', 'Name', 'Sequence', 'Notes']) + '\n')

    name_well_pos = {}
    pos = 0

    for domino, pairs in domino_pairs.iteritems():
        well_pos = plate_utils.get_well_pos(pos)
        name = '_'.join(pairs[0])
        name_well_pos[name] = well_pos
        pairs_str = ', '.join(set([pair[0] + '_' + pair[1] for pair in pairs]))
        order_file.write('\t'.join([well_pos, name, domino,
                                    pairs_str]) + '\n')
        pos += 1

    order_file.close()
    return name_well_pos


def _write_domino_pools_file(design_id_dominoes, domino_pairs, name_well_pos,
                             filename, vol=1.0):
    '''Writes domino pools operation file.'''
    design_id_well_pos = {}
    domino_file = open(filename + '_domino_pools.xls', 'w+')
    domino_file.write(
        '\t'.join(['DestinationPlateBarcode',
                   'DestinationPlateWell',
                   'SourcePlateBarcode',
                   'SourcePlateWell',
                   'ComponentName',
                   'Volume']) + '\n')

    pos = 0

    for design_id, dominoes in design_id_dominoes.iteritems():
        for domino in dominoes:
            well_pos = plate_utils.get_well_pos(pos)
            seq = domino[1][0][0] + domino[1][1][0]
            domino_id = _get_domino_id(seq, list(domino[0]), domino_pairs)
            design_id_well_pos[design_id] = well_pos

            line = '\t'.join([filename.split('/')[-1] + '_domino_pools',
                              well_pos,
                              filename.split('/')[-1],
                              name_well_pos[domino_id],
                              domino_id,
                              str(vol)])

            domino_file.write(line + '\n')

        pos += 1

    domino_file.close()
    return design_id_well_pos


def _write_parts_file(design_id_dominoes, filename):
    '''Writes a parts list.'''
    parts_well_pos = {}
    parts_file = open(filename + '_parts.xls', 'w+')
    parts_file.write(
        '\t'.join(['Well', 'Part / plasmid id']) + '\n')

    pos = 0
    for dominoes in design_id_dominoes.itervalues():
        for domino in dominoes:
            for part in domino[0]:
                if part not in parts_well_pos:
                    well_pos = plate_utils.get_well_pos(pos)
                    parts_file.write('\t'.join([well_pos, part]) + '\n')
                    parts_well_pos[part] = well_pos
                    pos += 1

    parts_file.close()
    return parts_well_pos


def _write_plasmids_file(design_id_dominoes, design_id_well_pos, part_well_pos,
                         filename, vol=1.0):
    '''Writes plasmids file.'''
    plasmids_file = open(filename + '_plasmids.xls', 'w+')
    plasmids_file.write(
        '\t'.join(['DestinationPlateBarcode',
                   'DestinationPlateWell',
                   'SourcePlateBarcode',
                   'SourcePlateWell',
                   'ComponentName',
                   'Volume']) + '\n')

    pos = 0

    for design_id, dominoes in design_id_dominoes.iteritems():
        well_pos = plate_utils.get_well_pos(pos)
        parts = []
        for domino in dominoes:
            for part in list(domino[0]):
                if part not in parts:
                    line = '\t'.join([filename.split('/')[-1] + '_plasmids',
                                      well_pos,
                                      filename.split('/')[-1] + '_parts',
                                      part_well_pos[part],
                                      part,
                                      str(vol)])
                    plasmids_file.write(line + '\n')
                    parts.append(part)

        line = '\t'.join([filename.split('/')[-1] + '_plasmids',
                          well_pos,
                          filename.split('/')[-1] +
                          '_domino_pools',
                          design_id_well_pos[design_id],
                          design_id + '_domino_pool',
                          str(vol)])
        plasmids_file.write(line + '\n')

        pos += 1

    plasmids_file.close()


def _get_domino_id(seq, pair, domino_pairs):
    '''Gets a temporary domino id.'''
    if seq not in domino_pairs:
        domino_pairs[seq] = [pair]
    else:
        domino_pairs[seq].append(pair)

    return '_'.join(domino_pairs[seq][0])


def main(args):
    '''main method.'''
    ice_client = ICEClient(args[2], args[3], args[4])

    for filename in args[5:]:
        designs = doe.get_designs(filename)
        _, design_id_dominoes = get_dominoes(ice_client,
                                             designs,
                                             float(args[0]),
                                             [args[1]])

        _write_dominoes(design_id_dominoes, os.path.splitext(filename)[0])

        # _write_plasmids(ice_client, design_id_plasmids)

if __name__ == '__main__':
    main(sys.argv[1:])
