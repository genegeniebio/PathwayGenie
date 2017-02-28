'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from _collections import defaultdict
import sys

from synbiochem.utils.ice_utils import ICEClient


class AssemblyGenie(object):
    '''Class implementing AssemblyGenie algorithms.'''

    def __init__(self, url, username, password, ice_ids):
        self.__ice_client = ICEClient(url, username, password)
        self.__ice_ids = ice_ids

    def export_order(self):
        '''Exports a plasmids constituent parts for ordering.'''

        entries = {}

        for ice_id in self.__ice_ids:
            data = self.__get_data(ice_id)

            for part in data[0].get_metadata()['linkedParts']:
                data = self.__get_data(part['partId'])
                entries[data[1]] = data[2:]

        for entry_id, entry in entries.iteritems():
            print '\t'.join([entry_id] + [str(item) for item in entry])

    def export_recipe(self, src_filenames,
                      dom_pool_plate_id='domino_pools_plate', domino_vol=3,
                      lcr_plate_id='lcr_plate', pool_vol=1):
        '''Exports recipes.'''
        comp_well = _get_src_comp_well(src_filenames)
        backbone_pools = defaultdict(list)
        parts_pools = defaultdict(list)
        domino_pools = defaultdict(list)

        for ice_id in self.__ice_ids:
            data = self.__get_data(ice_id)

            for part in data[0].get_metadata()['linkedParts']:
                data = self.__get_data(part['partId'])

                if data[4] == 'ORF':
                    parts_pools[ice_id].append(data)
                elif data[4] == 'DOMINO':
                    domino_pools[ice_id].append(data)
                else:
                    # Assume backbone:
                    backbone_pools[ice_id].append(data)

        self.__output_recipe(comp_well,
                             domino_pools, dom_pool_plate_id, domino_vol,
                             lcr_plate_id, pool_vol)

    def __get_data(self, ice_id):
        '''Gets data from ICE entry.'''
        ice_entry = self.__ice_client.get_ice_entry(ice_id)
        metadata = ice_entry.get_metadata()

        return ice_entry, \
            metadata['partId'], \
            metadata['name'], \
            metadata['type'], \
            ice_entry.get_parameter('Type'), \
            ice_entry.get_seq()

    def __output_recipe(self, comp_well,
                        domino_pools, dom_pool_plate_id, domino_vol,
                        lcr_plate_id, pool_vol):
        '''Outputs recipes.'''
        # Write domino pools worklist:
        self.__write_dom_pool_worklist(domino_pools, dom_pool_plate_id,
                                       comp_well,
                                       domino_vol)

        print ''

        # Write LCR worklist:
        self.__write_lcr_worklist(lcr_plate_id, comp_well, pool_vol)

    def __write_components(self, comp_well, components, plate_id):
        '''Writes plate.'''

        for idx, component in enumerate(components):
            well = self.__get_well(idx)
            comp_well[component[1]] = (well, plate_id)
            print '\t'.join([well, component[1]])

        return comp_well

    def __write_dom_pool_worklist(self, domino_pools, dest_plate_id, comp_well,
                                  vol):
        '''Write domino pool worklist.'''
        print '\t'.join(['DestinationPlateBarcode',
                         'DestinationPlateWell',
                         'SourcePlateBarcode',
                         'SourcePlateWell',
                         'Volume',
                         'plasmid_id'])

        for idx, ice_id in enumerate(domino_pools):
            dest_well = _get_well(idx)

            for domino in domino_pools[ice_id]:
                src_well = comp_well[domino[1]]
                print '\t'.join([dest_plate_id, dest_well, src_well[1],
                                 src_well[0], str(vol), ice_id])

            comp_well[ice_id + '_domino_pool'] = (dest_well, dest_plate_id)

    def __write_lcr_worklist(self, dest_plate_id, comp_well, pool_vol):
        '''Writes LCR worklist.'''
        print '\t'.join(['DestinationPlateBarcode',
                         'DestinationPlateWell',
                         'SourcePlateBarcode',
                         'SourcePlateWell',
                         'Volume',
                         'plasmid_id'])

        for idx, ice_id in enumerate(self.__ice_ids):
            dest_well = _get_well(idx)

            # Write water:
            print '\t'.join([dest_plate_id, dest_well, 'water_plate',
                             'A1', str('10'), ice_id])

            # Write mastermix:
            print '\t'.join([dest_plate_id, dest_well, 'mastermix_plate',
                             'A1', str('7.5'), ice_id])

            # Write domino pools:
            pool_well = comp_well[ice_id + '_domino_pool']

            print '\t'.join([dest_plate_id, dest_well, pool_well[1],
                             pool_well[0], str(pool_vol), ice_id])


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


def _get_well(idx, rows=8, columns=12):
    '''Map idx to well'''
    if idx < 0 or idx >= rows * columns:
        raise ValueError('Index %idx out of range' % idx)

    return chr(ord('A') + (idx / rows)) + str(idx % rows + 1)


def main(args):
    '''main method.'''
    genie = AssemblyGenie(args[0], args[1], args[2], args[4:])
    genie.export_recipe(args[3].split(','))


if __name__ == '__main__':
    main(sys.argv[1:])
