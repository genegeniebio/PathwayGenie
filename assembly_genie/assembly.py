'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
from _collections import defaultdict
from itertools import cycle
from shutil import rmtree
import os

from synbiochem.utils import plate_utils

from assembly_genie.build import BuildGenieBase


_AMPLIGASE = 'ampligase'
_LCR_MASTERMIX = 'lgr-mastermix'
_WATER = 'water'

_WORKLIST_COLS = ['DestinationPlateBarcode',
                  'DestinationPlateWell',
                  'SourcePlateBarcode',
                  'SourcePlateWell',
                  'Volume',
                  'ComponentName',
                  'description',
                  'ice_id',
                  'plasmid_id']


class AssemblyThread(BuildGenieBase):
    '''Class implementing AssemblyGenie algorithms.'''

    def __init__(self, query, outdir='assembly'):
        super(AssemblyThread, self).__init__(query)
        self.__rows = self._query.get('rows', 8)
        self.__cols = self._query.get('cols', 12)
        self.__outdir = outdir
        self._comp_well = {}

        if os.path.exists(self.__outdir):
            rmtree(self.__outdir)

        os.mkdir(self.__outdir)

    def _write_dom_pool_worklist(self, pools, dest_plate_id, vol):
        '''Write domino pool worklist.'''
        self._write_worklist_header(dest_plate_id)

        comp_well = {}
        worklist = []

        for dest_idx, ice_id in enumerate(sorted(pools)):
            for domino in pools[ice_id]['dominoes']:
                src_well = self._comp_well[domino[1]]

                worklist.append([dest_plate_id, dest_idx, src_well[1],
                                 src_well[0], str(vol),
                                 domino[2], domino[5], domino[1],
                                 ice_id])

            comp_well[ice_id + '_domino_pool'] = (dest_idx, dest_plate_id, [])

        self._write_comp_wells(dest_plate_id, comp_well)
        self._write_worklist(dest_plate_id, worklist)
        return comp_well

    def _get_pools(self):
        '''Get pools.'''
        pools = defaultdict(lambda: defaultdict(list))

        for ice_id in self._ice_ids:
            data = self._get_data(ice_id)

            for part in data[0].get_metadata()['linkedParts']:
                data = self._get_data(part['partId'])

                if data[4] == 'ORF':
                    pools[ice_id]['parts'].append(data)
                elif data[4] == 'DOMINO':
                    pools[ice_id]['dominoes'].append(data)
                else:
                    # Assume backbone:
                    pools[ice_id]['backbone'].append(data)

        return pools

    def _write_plate(self, plate_id, components):
        '''Write plate.'''
        comp_well = self.__get_comp_well(plate_id, components)
        self._write_comp_wells(plate_id, comp_well)
        return comp_well

    def _write_worklist_header(self, dest_plate_id):
        '''Write worklist.'''
        worklist_id = dest_plate_id + '_worklist'
        outfile = os.path.join(self.__outdir, worklist_id + '.txt')

        with open(outfile, 'a+') as out:
            out.write('\t'.join(_WORKLIST_COLS) + '\n')

    def _write_worklist(self, dest_plate_id, worklist):
        '''Write worklist.'''
        worklist_id = dest_plate_id + '_worklist'
        outfile = os.path.join(self.__outdir, worklist_id + '.txt')

        with open(outfile, 'a+') as out:
            worklist_map = defaultdict(list)

            for entry in sorted(worklist, key=lambda x: x[3]):
                worklist_map[entry[1]].append(entry)

            for idx in cycle(range(0, self.__rows * self.__cols)):
                if worklist_map[idx]:
                    entry = worklist_map[idx].pop(0)
                    out.write('\t'.join([plate_utils.get_well(val)
                                         if idx == 1 or idx == 3
                                         else str(val)
                                         for idx, val in enumerate(entry)]) +
                              '\n')

                if not sum([len(lst) for lst in worklist_map.values()]):
                    break

    def __get_comp_well(self, plate_id, components):
        '''Gets component-well map.'''
        comp_well = {}
        well_idx = 0

        for comps in components:
            if comps[0] == _WATER:
                # Special case: appears in many wells to optimise dispensing
                # efficiency:
                # Assumes water is first in components list.
                comp_well[comps[0]] = [[idx, plate_id, comps[1:]]
                                       for idx in range(len(self._ice_ids))]

                well_idx = well_idx + len(self._ice_ids)

            else:
                comp_well[comps[0]] = [well_idx, plate_id, comps[1:]]

                well_idx = well_idx + 1

        return comp_well

    def _write_comp_wells(self, plate_id, comp_wells):
        '''Write component-well map.'''
        outfile = os.path.join(self.__outdir, plate_id + '.txt')

        with open(outfile, 'a+') as out:
            for comp, wells in sorted(comp_wells.iteritems(),
                                      key=lambda (_, v): v[0]):

                if isinstance(wells[0], int):
                    self.__write_comp_well(out, wells, comp)
                else:
                    for well in wells:
                        self.__write_comp_well(out, well, comp)

    def __write_comp_well(self, out, well, comp):
        '''Write line on component-well map.'''
        outstr = '%s\t%s' % (plate_utils.get_well(well[0],
                                                  self.__rows,
                                                  self.__cols),
                             comp)
        out.write(outstr)
        out.write('\t'.join(str(val) for val in well[2]))
        out.write('\n')
