'''
PathwayGenie (c) University of Manchester 2017

PathwayGenie is licensed under the MIT License.

To view a copy of this license, visit <http://opensource.org/licenses/MIT/>.

@author:  neilswainston
'''
from __future__ import division

from tempfile import NamedTemporaryFile

from neo4j.v1 import GraphDatabase
from synbiochem.utils.job import JobThread
import pymzml


class MetabolomicsThread(JobThread):
    '''Runs a MetabolomicsGenie job.'''

    def __init__(self, query):
        JobThread.__init__(self)

        self.__query = query
        self.__results = []

    def run(self):
        '''Runs MetabolomicsGenie job.'''
        iteration = 0

        self.__fire_event('running', 'Parsing spectra...')

        spec_file = NamedTemporaryFile(delete=False)

        with open(spec_file.name, 'w') as fle:
            fle.write(self.__query['spectra'])

        spectra = pymzml.run.Reader(spec_file.name)

        for spectrum in spectra:
            if spectrum['ms level'] == 2:
                hits = self.__analyse_spec(spectrum)

                if len(hits):
                    spectrum['peaks'] = spectrum.peaks
                    self.__results.append({'spectrum': spectrum,
                                           'hits': [hits[0]]})

            iteration += 1
            self.__fire_event('running', 'Identifying spectra...')

            if iteration == 5:
                break

        if self._cancelled:
            self.__fire_event('cancelled', 'Job cancelled')
        else:
            self.__fire_event('finished', 'Job completed')

    def __analyse_spec(self, spectrum):
        '''Analyse a given spectra.'''
        prec_mz = spectrum['selected ion m/z']
        prec_charge = spectrum.get('charge state', 1.0)
        prec_mass = (prec_mz - 1.00728) * prec_charge

        tolerance = self.__query['tol'] \
            if self.__query['tol_unit'] == 'Da' \
            else prec_mass * self.__query['tol'] / 1e6

        hits = []

        for result in _get_cand_spec(prec_mass, tolerance):
            chem = result[0]
            spec = result[1]
            cand_spec = pymzml.spec.Spectrum(measuredPrecision=1e-6)
            cand_spec.peaks = zip(spec['m/z'],
                                  spec['intensity'])

            spec.properties.pop('m/z')
            spec.properties.pop('intensity')
            spec.properties['peaks'] = cand_spec.peaks

            hits.append({'chemical': chem.properties,
                         'spectrum': spec.properties,
                         'score': spectrum.similarityTo(cand_spec)})

        hits.sort(key=lambda x: x['score'], reverse=True)

        return hits

    def __fire_event(self, status, message=''):
        '''Fires an event.'''
        event = {'update': {'status': status,
                            'message': message,
                            'progress': 0,
                            'iteration': 0,
                            'max_iter': 0},
                 }

        if status == 'finished':
            event['result'] = self.__results

        self._fire_event(event)


def _get_cand_spec(mass, tol):
    '''Gets candidate spectra.'''
    cand_spec = []
    query = 'MATCH (s:Spectrum)-[]-(c:Chemical)' + \
        ' WHERE c.monoisotopic_mass > {start_mass}' + \
        ' AND c.monoisotopic_mass < {end_mass}' + \
        ' RETURN c, s'

    driver = GraphDatabase.driver("bolt://localhost")
    session = driver.session()

    result = session.run(query, {'start_mass': mass - tol,
                                 'end_mass': mass + tol})

    for record in result:
        cand_spec.append([record['c'], record['s']])

    return cand_spec


def main():
    '''main method.'''
    with open('Bl21(DE3)_1_WIJ6756_pos_small.mzml') as fle:
        mzml = fle.read()
    query = {'spectra': mzml, 'tol': 0.2, 'tol_unit': 'Da'}
    thread = MetabolomicsThread(query)
    thread.start()

if __name__ == '__main__':
    main()
