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
import pandas as pd


def write(in_filename, out_filename,
          ice_url, ice_username, ice_password,
          typ, comp_columns, group_name):
    '''Write.'''
    df = pd.read_csv(in_filename)
    ice_client = ice_utils.ICEClient(ice_url, ice_username, ice_password)
    output = []

    for _, row in df.iterrows():
        comp1 = ice_client.get_ice_entry(row[comp_columns[0]])
        comp2 = ice_client.get_ice_entry(row[comp_columns[1]])

        name = comp1.get_metadata()['name'] + \
            ' (' + comp2.get_metadata()['name'] + ')'

        product = ice_utils.ICEEntry(typ=typ)
        product.set_values({'name': name[:127], 'shortDescription': name})

        taxonomy = comp1.get_parameter('Taxonomy')

        if taxonomy:
            product.set_parameter('Taxonomy', taxonomy)

        ice_client.set_ice_entry(product)
        ice_client.add_link(product.get_ice_id(), comp1.get_ice_id())
        ice_client.add_link(product.get_ice_id(), comp2.get_ice_id())
        ice_client.set_ice_entry(product)

        if group_name:
            groups = ice_client.get_groups()
            ice_client.add_permission(product.get_ice_id(),
                                      groups[group_name])

        output.append({typ: product.get_ice_id(),
                       comp_columns[0] + '_seq': comp1.get_seq(),
                       comp_columns[1] + '_seq': comp2.get_seq()})

    # Update dataframe:
    df = df.join(pd.DataFrame(output, index=df.index))

    df.to_csv(out_filename, index=False)
