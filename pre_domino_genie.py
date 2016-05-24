'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import sys

from synbiochem.utils import sequence_utils, sbol_utils
from synbiochem.utils.ice_utils import ICEClient, ICEEntry
import doe
import dominogenie
import synbiochem.utils


class DominoManager(object):
    '''Class to manage domino design and interfacing with ICE.'''

    def __init__(self, ice_client):
        self.__ice_client = ice_client

    def get_dominoes(self, designs, melt_temp, restricts=None):
        '''Designs dominoes (bridging oligos) for LCR.'''

        for design in designs.values():
            design['sbol_docs'] = [self.__ice_client.get_sbol_doc(sbol_id)
                                   for sbol_id in design['design']]
            design['name'] = ' - '.join([sbol_utils.get_name(doc)
                                         for doc in design['sbol_docs']])

            # Apply restriction site digestion to PARTs not PLASMIDs.
            # (Assumes PLASMID at positions 1 and -1 - first and last).
            if restricts is not None:
                design['sbol_docs'] = [design['sbol_docs'][0]] + \
                    [_apply_restricts(doc, restricts)
                     for doc in design['sbol_docs'][1:-1]] + \
                    [design['sbol_docs'][-1]]

            # Generate plasmid SBOL document:
            design['plasmid'] = sbol_utils.concat(design['sbol_docs'][:-1])

            # Generate domino sequences:
            design['seqs'] = [sbol_utils.get_seq(doc)
                              for doc in design['sbol_docs']]
            oligos = dominogenie.get_dominoes(melt_temp, design['seqs'])
            pairs = [
                pair for pair in synbiochem.utils.pairwise(design['design'])]
            design['dominoes'] = zip(pairs, oligos)

            # Analyse sequences for similarity:
            ids_seqs = dict(zip(design['design'], design['seqs']))
            design['analysis'] = sequence_utils.do_blast(ids_seqs, ids_seqs)

    def write_dominoes(self, design):
        '''Writes plasmids and dominoes to ICE.'''
        self.__write_plasmids(design)
        self.__write_dominoes(design)

    def __write_plasmids(self, designs):
        '''Writes plasmids to ICE.'''
        for design_id, design in designs.iteritems():
            ice_entry = self.__ice_client.get_ice_entry(design_id)
            _set_metadata(ice_entry,
                          design['name'],
                          'Design: ' + design_id + '; Construct: ' +
                          ' '.join(design['design']))
            ice_entry.set_sbol_doc(design['plasmid'])
            self.__ice_client.set_ice_entry(ice_entry)

    def __write_dominoes(self, designs):
        '''Writes dominoes to ICE, or retrieves them if pre-existing.'''
        seq_entries = {}

        # print self.__ice_client.rebuild_blast()

        for design_id, design in designs.iteritems():
            for domino in design['dominoes']:
                seq = domino[1][0][0] + domino[1][1][0]

                if seq in seq_entries:
                    ice_entry = seq_entries[seq]
                else:
                    ice_entries = self.__ice_client.get_ice_entries_by_seq(seq)

                    if len(ice_entries) == 0:
                        doc = _get_sbol(seq, domino[1][0][0], domino[1][1][0])
                        ice_entry = ICEEntry(doc, 'PART')
                    else:
                        ice_entry = ice_entries[0]

                name, description = self.__get_metadata(ice_entry, design_id,
                                                        domino[0])
                _set_metadata(ice_entry, name, description)
                self.__ice_client.set_ice_entry(ice_entry)
                seq_entries[seq] = ice_entry

    def __get_metadata(self, ice_entry, design_id, part_ids):
        '''Gets metadata for a domino.'''
        metadata = ice_entry.get_metadata()

        # Set name if necessary:
        name = metadata['name'] if 'name' in metadata \
            else ' - '.join([self.__ice_client.get_ice_entry(prt_id).get_name()
                             for prt_id in part_ids])

        # Update Designs and Pairs in description:
        description = json.loads(metadata['shortDescription']) \
            if 'shortDescription' in metadata else {}
        designs = description['Designs'] if 'Designs' in description else []
        designs.append(design_id)
        pairs = description['Pairs'] if 'Pairs' in description else []
        pairs.append('_'.join(part_ids))
        description['Designs'] = list(set(designs))
        description['Pairs'] = list(set(pairs))

        return name, json.dumps(description)


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


def _get_sbol(seq, left_subseq, right_subseq):
    '''Creates an SBOL Document representing a domino.'''
    doc = sbol_utils.create_doc('Domino')
    sbol_utils.set_sequence(doc, seq)

    # Add annotations:
    _write_subcomp(doc, left_subseq, 1, 'Left')
    _write_subcomp(doc, right_subseq, len(left_subseq) + 1, 'Right')

    return doc


def _write_subcomp(document, seq, start, display_id):
    '''Adds a subcomponent to the domino SBOL Document.'''
    tag_uri = 'http://purl.obolibrary.org/obo/SO_0000807'
    sbol_utils.add_subcomponent(document, start, start + len(seq) - 1, '+',
                                display_id=display_id,
                                name=None,
                                typ=tag_uri,
                                description=None)


def _set_metadata(ice_entry, name, description):
    '''Sets key metadata values for ICE entry.'''
    ice_entry.set_value('name', name)
    ice_entry.set_value('status', 'Complete')
    ice_entry.set_value('creator', 'SYNBIOCHEM')
    ice_entry.set_value('creatorEmail', 'support@synbiochem.co.uk')
    ice_entry.set_value('principalInvestigator', 'SYNBIOCHEM')
    ice_entry.set_value(
        'principalInvestigatorEmail', 'support@synbiochem.co.uk')
    ice_entry.set_value('shortDescription', description)


def _write_analysis(designs):
    '''Write analysis results.'''
    try:
        for result_id, design in designs.iteritems():
            print result_id
            for result in design['analysis']:
                for alignment in result.alignments:
                    for hsp in alignment.hsps:
                        if result.query != alignment.hit_def:
                            print hsp
    except ValueError as err:
        print err


def main(args):
    '''main method.'''
    ice_client = ICEClient(args[2], args[3], args[4])

    for filename in args[5:]:
        designs = doe.get_designs(filename)
        dom_man = DominoManager(ice_client)
        dom_man.get_dominoes(designs, float(args[0]), [args[1]])
        dom_man.write_dominoes(designs)


if __name__ == '__main__':
    main(sys.argv[1:])
