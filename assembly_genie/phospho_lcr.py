'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
import sys

from assembly_genie.assembly import AssemblyThread, _AMPLIGASE, \
    _LCR_MASTERMIX, _WATER

_PNK = 'pnk'
_PNK_MASTERMIX = 'pnk-mastermix'


class PhosphoLcrThread(AssemblyThread):
    '''Class implementing AssemblyGenie algorithms.'''

    def run(self):
        '''Exports recipes.'''
        self.__init_query()
        pools = self._get_pools()

        # Write plates:
        self._comp_well.update(self._write_plate('MastermixTrough',
                                                 [[_WATER],
                                                  [_LCR_MASTERMIX],
                                                  [_PNK_MASTERMIX]]))

        self._comp_well.update(self._write_plate('components',
                                                 self.get_order()
                                                 + [[_AMPLIGASE],
                                                    [_PNK]]))

        # Write domino pools worklist:
        self._comp_well.update(
            self._write_dom_pool_worklist(
                pools,
                self._query['plate_ids']['domino_pools'],
                self._query['vols']['domino']))

        # Write LCR worklist:
        self.__write_lcr_worklist(self._query['plate_ids']['lcr'], pools)

    def __init_query(self):
        '''Initialises query.'''
        if 'plate_ids' not in self._query:
            self._query['plate_ids'] = {'domino_pools': 'domino_pools',
                                        'phospho': 'phospho',
                                        'lcr': 'lcr'}

        if 'def_reagents' not in self._query:
            self._query['def_reagents'] = {_LCR_MASTERMIX: 7.0,
                                           _AMPLIGASE: 1.5}

        if 'vols' not in self._query:
            self._query['vols'] = {'backbone': 1,
                                   'parts': 1,
                                   'dom_pool': 1,
                                   'domino': 3,
                                   'total': 25}

    def __write_lcr_worklist(self, dest_plate_id, pools):
        '''Writes LCR worklist.'''
        self._write_worklist_header(dest_plate_id)

        # Write water (special case: appears in many wells to optimise
        # dispensing efficiency):
        self.__write_water_worklist(dest_plate_id, pools)
        self.__write_parts_worklist(dest_plate_id, pools)
        self.__write_dom_pools_worklist(dest_plate_id)
        self.__write_default_reag_worklist(dest_plate_id)

    def __write_water_worklist(self, dest_plate_id, pools):
        '''Write water worklist.'''
        worklist = []

        for dest_idx, ice_id in enumerate(self._ice_ids):
            well = self._comp_well[_WATER][dest_idx]

            h2o_vol = self._query['vols']['total'] - \
                sum(self._query['def_reagents'].values()) - \
                len(pools[ice_id]['backbone']) * \
                self._query['vols']['backbone'] - \
                len(pools[ice_id]['parts']) * self._query['vols']['parts'] - \
                self._query['vols']['dom_pool']

            # Write water:
            worklist.append([dest_plate_id, dest_idx, well[1],
                             well[0], str(h2o_vol),
                             _WATER, _WATER, '',
                             ice_id])

        self._write_worklist(dest_plate_id, worklist)

    def __write_parts_worklist(self, dest_plate_id, pools):
        '''Write parts worklist.'''
        worklist = []

        for dest_idx, ice_id in enumerate(self._ice_ids):
            # Write backbone:
            for comp in pools[ice_id]['backbone']:
                well = self._comp_well[comp[1]]

                worklist.append([dest_plate_id, dest_idx, well[1],
                                 well[0], str(self._query['vols']['backbone']),
                                 comp[2], comp[5], comp[1],
                                 ice_id])

            # Write parts:
            for comp in pools[ice_id]['parts']:
                well = self._comp_well[comp[1]]

                worklist.append([dest_plate_id, dest_idx, well[1],
                                 well[0], str(self._query['vols']['parts']),
                                 comp[2], comp[5], comp[1],
                                 ice_id])

        self._write_worklist(dest_plate_id, worklist)

    def __write_dom_pools_worklist(self, dest_plate_id):
        '''Write domino pools worklist.'''
        worklist = []

        for dest_idx, ice_id in enumerate(self._ice_ids):
            well = self._comp_well[ice_id + '_domino_pool']

            worklist.append([dest_plate_id, dest_idx, well[1],
                             well[0], str(self._query['vols']['dom_pool']),
                             'domino pool', 'domino pool', '',
                             ice_id])

        self._write_worklist(dest_plate_id, worklist)

    def __write_default_reag_worklist(self, dest_plate_id):
        '''Write default reagents worklist.'''
        worklist = []

        for dest_idx, ice_id in enumerate(self._ice_ids):
            for reagent, vol in self._query['def_reagents'].iteritems():
                well = self._comp_well[reagent]

                worklist.append([dest_plate_id, dest_idx, well[1],
                                 well[0], str(vol),
                                 reagent, reagent, '',
                                 ice_id])

        self._write_worklist(dest_plate_id, worklist)


def main(args):
    '''main method.'''
    thread = PhosphoLcrThread({'ice': {'url': args[0],
                                       'username': args[1],
                                       'password': args[2]},
                               'ice_ids': args[3:]})

    thread.run()


if __name__ == '__main__':
    main(sys.argv[1:])
