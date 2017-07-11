'''
Created on 10 Jul 2017

@author: neilswainston
'''
from collections import defaultdict
from random import randint, sample
import re

from synbiochem.utils import plate_utils

from sbclearn.optimisation import gen_alg


def get_dest_comps(designs=12, rows=8, columns=12, all_comps=22, max_comps=5):
    '''Gets dest_comps.'''
    dest_comps = []

    for idx in range(designs):
        dest_well = plate_utils.get_well(idx, rows, columns)
        comps = sorted(sample(range(all_comps), randint(1, max_comps)))
        dest_comps.append([dest_well, comps])

    return dest_comps


def optimise(comps_dest, rows=8, columns=12):
    '''Optimise component layout.'''
    alg = AssemblyGeneticAlgorithm(100, comps_dest, rows, columns)
    return alg.run(1000)


class AssemblyGeneticAlgorithm(gen_alg.GeneticAlgorithm):
    '''Class to run a genetic algorithm to optimise LCR assembly.'''

    def __init__(self, pop_size, comps_dest, rows=8, cols=12,
                 retain=0.2, random_select=0.5, mutate=0.3,
                 verbose=True):
        self.__comps_dest = comps_dest
        self.__rows = rows
        self.__cols = cols
        args = {key: None for key in comps_dest}
        super(AssemblyGeneticAlgorithm, self).__init__(
            pop_size, args,
            retain=retain, random_select=random_select, mutate=mutate,
            verbose=verbose)

    def _get_individual(self):
        '''Create a member of the population.'''
        rnd = [plate_utils.get_well(idx, self.__rows, self.__cols)
               for idx in sample(range(self.__rows * self.__cols),
                                 len(self._args))]

        return dict(zip(self._args, rnd))

    def _get_arg(self, key, individual):
        '''Gets a random argument.'''
        curr_well = individual[key]
        curr_ords = _get_ords(curr_well)

        while True:
            new_ords = [(curr_ords[0] + randint(1, self.__rows)) %
                        self.__rows + 1,
                        (curr_ords[1] + randint(1, self.__cols)) %
                        self.__cols + 1]

            new_well = chr(new_ords[0] + ord('A')) + str(new_ords[1])

            curr_comp = None

            for comp, well in individual.iteritems():
                if well == new_well:
                    curr_comp = comp
                    break

            if curr_comp is not None:
                individual[curr_comp] = curr_well

            return new_well

    def _procreate(self, male, female):
        '''Procreate.'''
        pos = randint(0, len(male))

        child = male.copy()

        for idx, key in enumerate(female.keys()):
            if idx >= pos and female[key] not in child.values():
                child[key] = female[key]

        return child

    def _fitness(self, individual):
        '''Determine the fitness of an individual.'''
        dists = []

        for comp, well in individual.iteritems():
            for dest_well in self.__comps_dest[comp]:
                dists.append(sum(abs(e - s)
                                 for s, e in zip(_get_ords(well),
                                                 _get_ords(dest_well))))

        return sum(dists)


def _get_ords(well):
    vals = re.split('(\d+)', well)
    return [ord(vals[0]) - ord('A'), int(vals[1])]


def main():
    '''main method.'''
    comps_dest = defaultdict(list)
    dest_comps = get_dest_comps()

    for dest_comp in dest_comps:
        for comp in dest_comp[1]:
            comps_dest[comp].append(dest_comp[0])

    result, _ = optimise(comps_dest)

    print

    for dest_comp in dest_comps:
        print dest_comp[0] + ': ' + str(dest_comp[1])

    print

    for comp, dest_wells in comps_dest.iteritems():
        print str(comp) + ': ' + str(dest_wells)

    print

    for comp, well in result.iteritems():
        print str(comp) + ': ' + str(well)


if __name__ == '__main__':
    main()
