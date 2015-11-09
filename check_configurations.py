from PreflibUtils import read_election_file, write_map
from itertools import permutations, chain, product
from os import remove
from math import factorial
from locale import setlocale, getpreferredencoding, LC_ALL
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
import sys
import argparse

class Solver:
    def __init__(self, cmd):
        self.cmd = cmd

    def run_solver(self, conflicts, election, deletion_handler, outfile=None):
        if not conflicts:
            return [], 0

        self.deletion_handler = deletion_handler

        instance = self.generate_instance(conflicts, election)

        f = NamedTemporaryFile(delete=False)
        f.write(instance.encode(code))
        f.close()

        process = Popen([self.cmd, f.name], stdout=PIPE)
        out, err = process.communicate()

        conflict_variables, optimum = self.parse_instance(out)

        if outfile:
            candidates = election[0]
            votes = election[1]
            votecounts = election[2]

            votemap = self.delete_votes(votes, votecounts, conflict_variables)
            votesum = sum(votemap.values())

            write_map(candidates, votesum, votemap, open(outfile, "w"))

        #remove(f.name)
        return conflict_variables, optimum

    def votes_to_key(self, votes):
        reverse_votes = dict(map(lambda x: (x[1], x[0]), votes.items()))
        key = ""
        for i in sorted(reverse_votes.keys()):
            key += str(reverse_votes[i])+","

        return key[:-1]

    def delete_votes(self, votes, votecounts, conflict_votes):
        votemap = dict()
        tuples = list(zip(map(self.votes_to_key, votes), votecounts, range(1, len(votes)+1)))

        for key, count, index in tuples:
            if index not in conflict_votes:
                votemap[key] = count

        return votemap

    def parse_instance(self, out):
        conflict_variables = []
        optimum = None
        for line in out.decode(code).splitlines():
            if len(line) > 0:
                if line[0] == 'v':
                    for v in line[2:].split(" "):
                        if v and v[0] != '-':
                            conflict_variables.append(int(v))
                elif line[0] == 'o':
                    optimum = int(line[2:])

        return conflict_variables, optimum


    def generate_instance(self, conflicts, election):
        # the sum of violated soft clauses is smaller than the number of votes
        top = deletion_handler.get_top(election)
        weights = deletion_handler.get_weights(election)
        number_of_variables = deletion_handler.get_number_of_variables(election)
        number_of_clauses = len(conflicts) + number_of_variables

        parameter_line = "p wcnf "
        parameter_line += str(number_of_variables) + " "
        parameter_line += str(number_of_clauses) + " " + str(top)

        ret = parameter_line + "\n"

        for i in conflicts:
            hard_clause = str(top) + " "
            for j in i:
                hard_clause += str(j) + " "
            hard_clause += "0\n"
            ret += hard_clause

        for i, w in enumerate(weights, 1):
            # for some reason, there are instances with 0 weight
            # clasp complains about this (while log4j does not),
            # therefore we filter. Zero-weight-clauses won't be deleted.
            if w > 0:
                soft_clause = str(w) + " -" + str(i) + " 0\n"
                ret += soft_clause

        return ret

class VoteDeletionHandler:
    def get_number_of_variables(self, election):
        return len(self.get_weights(election))

    def get_top(self, election):
        return election[3]+1

    def get_weights(self, election):
        return election[2]

    def add_conflicts(self, mapping, configuration, matched_votes, conflicts):
        combinations = product(*matched_votes)
        for combination in combinations:
            conflicts.add(combination)

    def get_init_count(self, election):
        return election[3]

    def get_output_template(self):
        return ("deleted {delcount} of {initcount} votes "
                "({percentage:.2f}%) to ensure domain restriction: "
                "{domain_restriction}\n")

class CandidateDeletionHandler:
    def get_number_of_variables(self, election):
        return len(election[0])

    def get_top(self, election):
        return self.get_number_of_variables(election) + 1

    def get_weights(self, election):
        return self.get_number_of_variables(election) * [1]

    def add_conflicts(self, mapping, configuration, matched_votes, conflicts):
        conflicts.add(mapping[0:configuration.numvars])

    def get_init_count(self, election):
        return len(election[0])

    def get_output_template(self):
        return ("deleted {delcount} of {initcount} candidates "
                "({percentage:.2f}%) to ensure domain restriction: "
                "{domain_restriction}\n")

class Configuration:
    def __init__(self, tuples, unique_assignments):
        self.unique_assignments = unique_assignments
        self.tuples = tuples
        #this is not MAGIC!
        self.numvars = max(chain(*chain(*tuples)))
        self.numconds = len(tuples)

    def generate_mappings(self, candidates):
        if self.unique_assignments:
            return permutations(candidates, self.numvars)
        else:
            return product(candidates, repeat=self.numvars)

    def count_assignments(self, candidates):
        l = len(candidates)
        if self.unique_assignments:
            if l - self.numvars >= 0:
                return int(factorial(l)/factorial(l - self.numvars))
            else:
                return 0

        else:
            return int(pow(l, self.numvars))

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

def do_nothing(*_):
    pass

# List of list of tuples. An inner list corresponds to a condition in a
# configuration. The tuples represent strict greater-than inequalities
# (a,b) means a > b. The inequalities are conjoined.
alpha = Configuration([[(1,2), (2,3), (4,2)], [(3,2), (2,1), (4,2)]], unique_assignments=True)
anti_alpha = Configuration([[(2,1), (3,2), (2,4)], [(2,3), (1,2), (2,4)]], unique_assignments=True)
beta = Configuration([[(1,2), (2,3), (3,4)], [(2,4), (4,1), (1,3)]], unique_assignments=True)
gamma = Configuration([[(2,1), (3,4), (5,6)], [(1,2), (4,3), (5,6)], [(1,2), (3,4), (6,5)]], unique_assignments=False)
delta = Configuration([[(1,2), (3,4)], [(1,2), (4,3)], [(2,1), (3,4)], [(2,1),(4,3)]], unique_assignments=False)
best_diverse = Configuration([[(1,2), (1,3)], [(2,1), (2,3)], [(3,1), (3,2)]], unique_assignments=True)
worst_diverse = Configuration([[(1,3), (2,3)], [(1,2), (3,2)], [(2,1), (3,1)]], unique_assignments=True)

medium_diverse = []
medium_diverse_equations = zip([[(2,1), (1,3)], [(1,2), (2,3)], [(1,3), (3,2)]],
                               [[(3,1), (1,2)], [(3,2), (2,1)], [(2,3), (3,1)]])

for equations in product(*medium_diverse_equations):
    medium_diverse.append(Configuration(list(equations), unique_assignments=True))


domain_restrictions = [
    ("single-peaked", [alpha, worst_diverse]),
    ("single-caved", [anti_alpha, best_diverse]),
    ("worst-restricted", [worst_diverse]),
    ("medium-restricted", medium_diverse),
    ("group-separable", medium_diverse + [beta]),
    ("best-restricted", [best_diverse]),
    ("single-crossing", [gamma, delta])
]

domain_restriction_string = ""
domain_restriction_names = []

for i in domain_restrictions:
    domain_restriction_string += i[0] + ", "
    domain_restriction_names.append(i[0])

domain_restriction_string = domain_restriction_string[:-2]

parser = argparse.ArgumentParser()
parser.add_argument("file", action="store", metavar="FILE",
                    help="file to analyze")
parser.add_argument("-q", "--quiet", action="store_true", help="suppress ouput")
parser.add_argument("-i", "--include", action="append",
                    help="include given domain restriction (default: all) possible values: "
                    + domain_restriction_string,
                    choices=domain_restriction_names, nargs="+",
                    default=[],
                    metavar="DR")
parser.add_argument("-e", "--exclude", action="append",
                    help="exclude given domain restriction (default: none) possible values: "
                    + domain_restriction_string,
                    choices=domain_restriction_names, nargs="+",
                    default=[],
                    metavar="DR")
parser.add_argument("-v", "--vote-deletion", action="store_true",
                    help="delete votes to ensure domain restrictions (default)")
parser.add_argument("-c", "--candidate-deletion", action="store_true",
                    help="delete candidates to ensure domain restrictions")
parser.add_argument("-t", "--template", action="store",
                    help="specify custom output template (you can use '{delcount}', "
                         "'{initcount}', '{percentage}' and '{domain_restriction}' in"
                         " your template)")
parser.add_argument("-s", "--solver-command", action="store",
                    help="specify custom command that will be executed to solve the "
                         "generated SAT instance (default: clasp).")

args = vars(parser.parse_args())
includes = set(chain(*args["include"]))
excludes = set(chain(*args["exclude"]))

if includes & excludes:
    sys.stderr.write("Included and excluded domain restrictions overlap!")
    sys.exit(2)

tmp_domain_restrictions = []
if includes:
    for i in domain_restrictions:
        if i[0] in includes:
            tmp_domain_restrictions.append(i)
    domain_restrictions = tmp_domain_restrictions
elif excludes:
    for i in domain_restrictions:
        if i[0] not in excludes:
            tmp_domain_restrictions.append(i)
    domain_restrictions = tmp_domain_restrictions

myprint = sys.stdout.write
myprogress = sys.stderr.write
if args["quiet"]:
    myprint = do_nothing
    myprogress = do_nothing

if args["candidate_deletion"] and args["vote_deletion"]:
    sys.stderr.write("For now candidate deletion and vote deletion exclude one another!")
    sys.exit(2)

deletion_handler = VoteDeletionHandler()

if args["candidate_deletion"]:
    deletion_handler = CandidateDeletionHandler()

solver_command = "clasp"
if args["solver_command"]:
    solver_command = args["solver_command"]

filename = args["file"]
election = read_election_file(open(filename))

candidates = election[0]
votes = election[1]
initcount = deletion_handler.get_init_count(election)

setlocale(LC_ALL, '')
code = getpreferredencoding()

solver = Solver(solver_command)

if args["template"]:
    output_template = args["template"]
else:
    output_template = deletion_handler.get_output_template()

for name,configurations in domain_restrictions:
    myprogress("Currently solving: " + name + "\n")
    conflicts = set()
    for icf, configuration in enumerate(configurations):
        mappings = configuration.generate_mappings(candidates.keys())
        numassgs = configuration.count_assignments(candidates.keys())
        for im, mapping in enumerate(mappings, 1):
            matches = [[] for _ in range(configuration.numconds)]
            for iv, vote in enumerate(votes, 1):
                configuration.is_match(mapping, vote, iv, matches)
            matched_votes = sorted([sorted([y[0] for y in u]) for u in matches])
            if all(matched_votes):
                deletion_handler.add_conflicts(mapping, configuration, matched_votes, conflicts)
            myprogress("\r    {0}/{1} ({2:.2f}%)".format(im, numassgs, float(100*im)/numassgs))
        if numassgs > 0:
            myprogress("\n")

    conflict_vote, delcount = solver.run_solver(conflicts, election, deletion_handler)
    myprint(output_template.format(delcount=delcount, initcount=initcount,
                                   percentage=float(100*delcount)/initcount, domain_restriction=name))
