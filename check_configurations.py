from PreflibUtils import read_election_file
from DomainRestriction import is_single_peaked
from itertools import permutations, chain, product
from sys import argv

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



filename = argv[1]
election = read_election_file(open(filename))

candidates = election[0]
votes = election[1]

# List of list of tuples. An inner list corresponds to a condition in a
# configuration. The tuples represent strict greater-than inequalities 
# (a,b) means a > b. The inequalities are conjoined.
# TODO: implement disjunction.
alpha = [[(1,2), (2,3), (4,2)], [(3,2), (2,1), (4,2)]]
worst_diverse = [[(1,3), (2,3)], [(1,2), (3,2)], [(2,1), (3,1)]]

configurations = [alpha,worst_diverse]

# Function used to print the conflicts as encoding
print_conflicts = print_conflicts_wcnf

hits = [list() for _ in configurations]
conflicts = set()

for icf, configuration in enumerate(configurations):
    #this is not MAGIC!
    numvars = max(chain(*chain(*configuration)))
    mappings = permutations(candidates.keys(),numvars)
    for mapping in mappings:
        matches = [list() for _ in configuration]
        for iv, vote in enumerate(votes, 1):
            for ic, condition in enumerate(configuration):
                match = True
                for ineq in condition:
                    # small numbers mean preferred candidates, therefore <
                    if vote[mapping[ineq[0]-1]] < vote[mapping[ineq[1]-1]]:
                        continue
                    else:
                        match = False
                        break
                if match:
                    # TODO: abstract a function which either adds votes or candidates
                    matches[ic].append((iv, vote))
        matched_votes = [[y[0] for y in u] for u in matches]
        if all(matched_votes):
            combinations = product(*matched_votes)
            for combination in combinations:
                conflicts.add(combination)

print_conflicts(conflicts, election)
