from PreflibUtils import read_election_file
from DomainRestriction import is_single_peaked
from itertools import permutations, chain, product
from sys import argv
from math import factorial

def print_conflicts_wcnf(conflicts, election):
    # the sum of violated soft clauses is smaller than the number of votes
    top = election[3] + 1
    weights = election[2]
    number_of_variables = len(weights)
    number_of_clauses = len(conflicts) + number_of_variables

    parameter_line =  "p wcnf "
    parameter_line += str(number_of_variables) + " "
    parameter_line += str(number_of_clauses) + " " + str(top)

    print(parameter_line)

    for i in conflicts:
        hard_clause = str(top) + " "
        for j in i:
            hard_clause += str(j) + " "
        hard_clause += "0"
        print(hard_clause)

    for i,w in enumerate(weights,1):
        soft_clause = str(w) + " -" + str(i) + " 0"
        print(soft_clause)

class Configuration:
    def __init__(self, tuples, unique_assignments):
        self.unique_assignments = unique_assignments
        self.tuples = tuples
        #this is not MAGIC!
        self.numvars = max(chain(*chain(*tuples)))
        self.numconds = len(tuples)

    def generate_mappings(self, candidates):
        if self.unique_assignments:
            return permutations(candidates,self.numvars)
        else:
            return product(candidates, repeat=self.numvars)

    def count_assignments(self, candidates):
        l = len(candidates)
        if self.unique_assignments:
            return math.factorial(l)/math.factorial(l - self.numvars)
        else:
            return pow(l, self.numvars)

    def is_match(self, mapping, vote, iv, matches):
        for ic, condition in enumerate(self.tuples):
            match = True
            for ineq in condition:
                # small numbers mean preferred candidates, therefore <
                if vote[mapping[ineq[0]-1]] < vote[mapping[ineq[1]-1]]:
                    continue
                else:
                    match = False
                    break
            if match:
                matches[ic].append((iv, vote))

filename = argv[1]
election = read_election_file(open(filename))

candidates = election[0]
votes = election[1]

# List of list of tuples. An inner list corresponds to a condition in a
# configuration. The tuples represent strict greater-than inequalities 
# (a,b) means a > b. The inequalities are conjoined.
# TODO: implement disjunction.
alpha = Configuration([[(1,2), (2,3), (4,2)], [(3,2), (2,1), (4,2)]], unique_assignments=True)
worst_diverse = Configuration([[(1,3), (2,3)], [(1,2), (3,2)], [(2,1), (3,1)]], unique_assignments=True)

configurations = [alpha,worst_diverse]

# Function used to print the conflicts as encoding
print_conflicts = print_conflicts_wcnf

hits = [list() for _ in configurations]
conflicts = set()

for icf, configuration in enumerate(configurations):
    mappings = configuration.generate_mappings(candidates.keys())
    for mapping in mappings:
        matches = [[] for _ in range(configuration.numconds)]
        for iv, vote in enumerate(votes, 1):
            configuration.is_match(mapping, vote, iv,matches)
        matched_votes = sorted([sorted([y[0] for y in u]) for u in matches])
        if all(matched_votes): 
            combinations = product(*matched_votes)
            for combination in combinations:
                conflicts.add(combination)

print_conflicts(conflicts, election)
