from PreflibUtils import read_election_file
from DomainRestriction import is_single_peaked
from itertools import permutations, chain
from sys import argv

filename = argv[1]

election = read_election_file(open(filename))

candidates = election[0]
votes = election[1]

if is_single_peaked(votes, candidates):
    print(filename + " SINGLE")
else:
    print(filename + " MULTI")
