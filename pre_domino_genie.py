'''
PathwayGenie (c) University of Manchester 2015

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
import json
import sys

from synbiochem.utils import pairwise, seq_utils, dna_utils
from synbiochem.utils.ice_utils import ICEClient, ICEEntry
import doe
import dominogenie


class DominoManager(object):
    '''Class to manage domino design and interfacing with ICE.'''

    def __init__(self, ice_client):
        self.__ice_client = ice_client

    def get_dominoes(self, designs, melt_temp, restricts=None):
        '''Designs dominoes (bridging oligos) for LCR.'''

        for design in designs:
            design['dna'] = [self.__ice_client.get_dna(ice_id)
                             for ice_id in design['design']]
            design['name'] = ' - '.join([dna.name for dna in design['dna']])

            # Apply restriction site digestion to PARTs not PLASMIDs.
            # (Assumes PLASMID at positions 1 and -1 - first and last).
            if restricts is not None:
                design['dna'] = [design['dna'][0]] + \
                    [_apply_restricts(dna, restricts)
                     for dna in design['dna'][1:-1]] + \
                    [design['dna'][-1]]

            # Generate plasmid DNA object:
            design['plasmid'] = dna_utils.concat(design['dna'][:-1])

            # Generate domino sequences:
            design['seqs'] = [dna.seq for dna in design['dna']]
            oligos = dominogenie.get_dominoes(melt_temp, design['seqs'])
            pairs = [pair for pair in pairwise(design['design'])]
            design['dominoes'] = zip(pairs, oligos)

            # Analyse sequences for similarity:
            ids_seqs = dict(zip(design['design'], design['seqs']))
            design['analysis'] = seq_utils.do_blast(ids_seqs, ids_seqs)

    def write_dominoes(self, design):
        '''Writes plasmids and dominoes to ICE.'''
        self.__write_plasmids(design)
        # self.__write_dominoes(design)

    def __write_plasmids(self, designs):
        '''Writes plasmids to ICE.'''
        for design in designs:
            ice_entry = ICEEntry(typ='PLASMID')
            self.__ice_client.set_ice_entry(ice_entry)
            design_id = ice_entry.get_ice_id()

            _set_metadata(ice_entry,
                          design['name'],
                          'Construct: ' + ' '.join(design['design']))

            ice_entry.set_dna(design['plasmid'])
            self.__ice_client.set_ice_entry(ice_entry)
            print '\t'.join([design_id] + design['design'][:-1])

    def __write_dominoes(self, designs):
        '''Writes dominoes to ICE, or retrieves them if pre-existing.'''
        seq_entries = {}

        for design_id, design in designs.iteritems():
            for domino in design['dominoes']:
                seq = domino[1][0][0] + domino[1][1][0]

                if seq in seq_entries:
                    ice_entry = seq_entries[seq]
                else:
                    ice_entries = self.__ice_client.get_ice_entries_by_seq(seq)

                    if len(ice_entries) == 0:
                        dna = _get_domino_dna('name', seq, domino[1][0][0],
                                              domino[1][1][0])
                        ice_entry = ICEEntry(dna, 'PART')
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


def _apply_restricts(dna, restricts):
    '''Cleave off prefix and suffix, according to restriction sites.'''
    restrict_dnas = dna_utils.apply_restricts(dna, restricts)

    # This is a bit fudgy...
    # Essentially, return the longest fragment remaining after digestion.
    # Assumes prefix and suffix are short sequences that are cleaved off.
    restrict_dnas.sort(key=lambda x: len(x.seq), reverse=True)
    return restrict_dnas[0]


def _get_domino_dna(name, seq, left_subseq, right_subseq):
    '''Creates a DNA object representing a domino.'''
    dna = dna_utils.Dna(name=name, seq=seq)

    # Add annotations:
    _write_subcomp(dna, left_subseq, 1, 'Left')
    _write_subcomp(dna, right_subseq, len(left_subseq) + 1, 'Right')

    return dna


def _write_subcomp(dna, seq, start, name):
    '''Adds a subcomponent to the domino SBOL Document.'''
    feature = dna_utils.Dna(name=name, start=start, end=start + len(seq) - 1,
                            forward=True)
    dna.add_feature(feature)


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
