'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=invalid-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
from synbiochem.utils import ice_utils

from ice.ice import write_ice_entry
import pandas as pd


def write(in_filename, out_filename,
          ice_url, ice_username, ice_password,
          typ, comp_columns, group_name, write_seq=False):
    '''Write.'''
    df = pd.read_csv(in_filename)
    ice_client = ice_utils.ICEClient(ice_url, ice_username, ice_password)
    output = []

    for _, row in df.iterrows():
        ice_id1 = row[comp_columns[0]]
        ice_id2 = row[comp_columns[1]]
        product, comp1, comp2 = write_ice_entry(ice_client, ice_id1, ice_id2,
                                                typ, write_seq, [group_name])

        output.append({typ: product.get_ice_id(),
                       comp_columns[0] + '_seq': comp1.get_seq(),
                       comp_columns[1] + '_seq': comp2.get_seq()})

    # Update dataframe:
    df = df.join(pd.DataFrame(output, index=df.index))

    df.to_csv(out_filename, index=False)
