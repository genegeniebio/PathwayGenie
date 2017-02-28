'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from _collections import defaultdict
import sys

from synbiochem.utils import plate_utils
from synbiochem.utils.ice_utils import ICEClient

_WORKLIST_COLS = ['DestinationPlateBarcode',
                  'DestinationPlateWell',
                  'SourcePlateBarcode',
                  'SourcePlateWell',
                  'Volume',
                  'component',
                  'plasmid_id']


def export_order(url, username, password, ice_ids):
    '''Exports a plasmids constituent parts for ordering.'''
    ice_client = ICEClient(url, username, password)
    entries = {}

    for ice_id in ice_ids:
        data = _get_data(ice_client, ice_id)

        for part in data[0].get_metadata()['linkedParts']:
            data = _get_data(ice_client, part['partId'])
            entries[data[1]] = data[2:]

    for entry_id, entry in entries.iteritems():
        print '\t'.join([entry_id] + [str(item) for item in entry])


class AssemblyGenie(object):
    '''Class implementing AssemblyGenie algorithms.'''

    def __init__(self, url, username, password, ice_ids, src_filenames):
        self.__ice_client = ICEClient(url, username, password)
        self.__ice_ids = ice_ids
        self.__comp_well = _get_src_comp_well(src_filenames)

    def export_lcr_recipe(self,
                          dom_pool_plate_id='domino_pools', domino_vol=3,
                          lcr_plate_id='lcr', def_reagents=None,
                          backbone_vol=1, comp_vol=1, dom_pool_vol=1,
                          total_vol=25):
        '''Exports LCR recipes.'''
        if def_reagents is None:
            def_reagents = {'mastermix': 7.5, 'ampligase': 1.5}

        pools = defaultdict(lambda: defaultdict(list))

        for ice_id in self.__ice_ids:
            data = _get_data(self.__ice_client, ice_id)

            for part in data[0].get_metadata()['linkedParts']:
                data = _get_data(self.__ice_client, part['partId'])

                if data[4] == 'ORF':
                    pools[ice_id]['parts'].append(data)
                elif data[4] == 'DOMINO':
                    pools[ice_id]['dominoes'].append(data)
                else:
                    # Assume backbone:
                    pools[ice_id]['backbone'].append(data)

        self.__output_lcr_recipe(pools, dom_pool_plate_id, domino_vol,
                                 lcr_plate_id, def_reagents,
                                 backbone_vol, comp_vol, dom_pool_vol,
                                 total_vol)

    def __output_lcr_recipe(self, pools, dom_pool_plate_id, domino_vol,
                            lcr_plate_id, def_reagents,
                            backbone_vol, comp_vol, dom_pool_vol, total_vol):
        '''Outputs recipes.'''
        # Write domino pools worklist:
        self.__write_dom_pool_worklist(pools, dom_pool_plate_id, domino_vol)

        print ''

        # Write LCR worklist:
        self.__write_lcr_worklist(lcr_plate_id, pools, def_reagents,
                                  backbone_vol, comp_vol, dom_pool_vol,
                                  total_vol)

    def __write_dom_pool_worklist(self, pools, dest_plate_id, vol):
        '''Write domino pool worklist.'''
        print '\t'.join(_WORKLIST_COLS)

        for idx, ice_id in enumerate(pools):
            dest_well = plate_utils.get_well(idx)

            for domino in pools[ice_id]['dominoes']:
                src_well = self.__comp_well[domino[1]]
                print '\t'.join([dest_plate_id, dest_well, src_well[1],
                                 src_well[0], str(vol), domino[2], ice_id])

            self.__comp_well[ice_id + '_domino_pool'] = \
                (dest_well, dest_plate_id)

    def __write_lcr_worklist(self, dest_plate_id, pools, def_reagents,
                             backbone_vol, comp_vol, dom_pool_vol, total_vol):
        '''Writes LCR worklist.'''
        print '\t'.join(_WORKLIST_COLS)

        for idx, ice_id in enumerate(self.__ice_ids):
            curr_vol = 0
            dest_well = plate_utils.get_well(idx)

            # Write backbone:
            for comp in pools[ice_id]['backbone']:
                well = self.__comp_well[comp[1]]

                print '\t'.join([dest_plate_id, dest_well, well[1],
                                 well[0], str(backbone_vol), comp[2],
                                 ice_id])
                curr_vol += backbone_vol

            # Write parts:
            for comp in pools[ice_id]['parts']:
                well = self.__comp_well[comp[1]]

                print '\t'.join([dest_plate_id, dest_well, well[1],
                                 well[0], str(comp_vol), comp[2],
                                 ice_id])
                curr_vol += backbone_vol

            # Write domino pools:
            well = self.__comp_well[ice_id + '_domino_pool']

            print '\t'.join([dest_plate_id, dest_well, well[1],
                             well[0], str(dom_pool_vol), 'domino pool',
                             ice_id])
            curr_vol += dom_pool_vol

            # Write default reagents:
            for reagent, vol in def_reagents.iteritems():
                well = self.__comp_well[reagent]
                print '\t'.join([dest_plate_id, dest_well, well[1],
                                 well[0], str(vol), reagent, ice_id])
                curr_vol += vol

            # Write water:
            well = self.__comp_well['H2O']
            print '\t'.join([dest_plate_id, dest_well, well[1],
                             well[0], str(total_vol - curr_vol), 'H2O',
                             ice_id])


def _get_data(ice_client, ice_id):
    '''Gets data from ICE entry.'''
    ice_entry = ice_client.get_ice_entry(ice_id)
    metadata = ice_entry.get_metadata()

    return ice_entry, \
        metadata['partId'], \
        metadata['name'], \
        metadata['type'], \
        ice_entry.get_parameter('Type'), \
        ice_entry.get_seq()


def _get_src_comp_well(src_filenames):
    '''Gets components to well / plate mappings.'''
    comp_well = {}

    for src_filename in src_filenames:
        with open(src_filename) as fle:
            plate_id = src_filename[:src_filename.find('.')]

            for line in fle:
                terms = line.split()
                comp_well[terms[1]] = (terms[0], plate_id)

    return comp_well


def main(args):
    '''main method.'''
    genie = AssemblyGenie(args[0], args[1], args[2], args[4:],
                          args[3].split(','))
    genie.export_lcr_recipe()


if __name__ == '__main__':
    main(sys.argv[1:])
