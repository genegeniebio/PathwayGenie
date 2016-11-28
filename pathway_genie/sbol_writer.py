'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
# pylint: disable=too-many-arguments
from synbiochem.utils import ice_utils


def submit(url, username, pssword, dna, metadata):
    '''Forms SBOL document and submits to ICE.'''
    ice_client = ice_utils.ICEClient(url, username, pssword)
    ice_entry = ice_utils.ICEEntry(dna, 'PART', metadata)
    return ice_client.set_ice_entry(ice_entry)
