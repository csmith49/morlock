from pyparsing import Suppress, Word, Forward, Group, delimitedList, \
	OneOrMore, ZeroOrMore, CaselessLiteral
from argparse import ArgumentParser
from z3 import Int, And, Implies, Solver, Or, unsat
from collections import defaultdict
from time import clock

# --------------------------------------------
# Parsing!
# --------------------------------------------
LPAREN, RPAREN = Suppress("("), Suppress(")")
token = Word("1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*_+-=<>~<>?[{|]}./\\")
term = Forward()
term << (token ^ Group(token + LPAREN + delimitedList(term) + RPAREN))
rule = Group(term + Suppress("->") + term)
VARS = Group(LPAREN + CaselessLiteral("VAR") + ZeroOrMore(token) + RPAREN)
RULES = Group(LPAREN + CaselessLiteral("RULES") + ZeroOrMore(rule) + RPAREN)
file = OneOrMore(VARS | RULES)

def parse_tpdb(string):
	return file.parseString(string).asList()

# --------------------------------------------
# classes for holding variables and TRS
# --------------------------------------------
class TRS(object):
	def __init__(self, sexpr = None):
		self.rules = []
		self.variables = set()
		self.functions = {}
		# leaves the option of filling in a TRS manually
		if sexpr: self._update_by_sexpr(sexpr)
	def _update_by_sexpr(self, sexpr):
		# crawl through the input file, picking up rules and variables
		for f, *args in sexpr:
			if f == "VAR":
				self.variables.update(args)
			elif f == "RULES":
				self.rules += args
			else:
				pass
		# then iterate through rules to pick out function arities
		for term in [t for rule in self.rules for t in rule]:
			worklist = [term]
			while worklist:
				f, *args = break_term(worklist.pop())
				worklist += args
				if not self.is_variable(f):
					arity = len(args)
					self.functions[f] = arity
	def is_variable(self, t):
		if isinstance(t, list): return False
		else: return t in self.variables

class WeightFunction(object):
	def __init__(self, signature):
		self._weights = {f : Int('w_{}'.format(f)) for f in signature.keys()}
		self._base = Int('w_0')
	def __getitem__(self, key):
		if isinstance(key, int) and key == 0:
			return self._base
		elif isinstance(key, str):
			return self._weights[key]
		else: raise KeyError

class Precedence(object):
	def __init__(self, signature):
		self._precedence = {f : Int('p_{}'.format(f)) for f in signature.keys()}
	def __getitem__(self, key):
		return self._precedence[key]

# --------------------------------------------
# Utility functions
# --------------------------------------------
def break_term(term):
	if isinstance(term, list):
		return term
	else:
		return [term]

def weight(term, W):
	out, worklist = 0, [term]
	while worklist:
		f, *args = break_term(worklist.pop())
		worklist += args
		try:
			out += W[f]
		except KeyError:
			out += W[0]
	return out

def eq(s, t):
	worklist = [(s, t)]
	while worklist:
		l, r =  worklist.pop()
		f, *arfs = break_term(l)
		g, *args = break_term(r)
		if f != g:
			return False
		else:
			worklist += list(zip(arfs, args))
	return True

def in_subalgebra(s, sig):
	worklist = [s]
	while worklist:
		f, *args = break_term(worklist.pop())
		if f in sig:
			worklist += args
		else:
			return False
	return True

def lex_index(s, t):
	f, *arfs = break_term(s)
	g, *args = break_term(t)
	for i, (fi, gi) in enumerate(zip(arfs, args)):
		if not eq(fi, gi):
			return i
	return None

def var_count(s, trs):
	counts = defaultdict(lambda: 0)
	worklist = [s]
	while worklist:
		cur = worklist.pop()
		if trs.is_variable(cur):
			counts[cur] += 1
		else:
			f, *args = break_term(cur)
			worklist += args
	return counts

def less_vars(s, t, trs):
	s_counts, t_counts = var_count(s, trs), var_count(t, trs)
	for x in set(list(s_counts.keys()) + list(t_counts.keys())):
		if s_counts[x] < t_counts[x]:
			return True
	return False

def kbo_base(s, t, trs):
	return trs.is_variable(s) or eq(s, t) or less_vars(s, t, trs)

def kbop_base(s, t, trs):
	if trs.is_variable(t):
		if not eq(s, t):
			sig = [f for f, arity in trs.functions.items() if arity == 1]
			sig.append(t)
			if in_subalgebra(s, sig):
				return True
	return False


# --------------------------------------------
# Recursive constraint generation functions
# --------------------------------------------

def kbo(s, t, trs, W, P):
	if kbo_base(s, t, trs):
		return False
	else:
		return Or(
			weight(s, W) > weight(t, W), 
			And(
				weight(s, W) == weight(t, W),
				kbop(s, t, trs, W, P)))

def kbop(s, t, trs, W, P):
	if kbop_base(s, t, trs):
		return True
	f, *arfs = break_term(s)
	g, *args = break_term(t)
	i = lex_index(s, t)
	if i is None:
		return False
	else:
		return Or(
			P[f] > P[g],
			And(
				P[f] == P[g],
				kbo(arfs[i], args[i], trs, W, P)))

# --------------------------------------------
# Prove termination here:
# --------------------------------------------
def check_termination(trs, DEBUG=False):
	# create the variables we're solving for
	W = WeightFunction(trs.functions)
	P = Precedence(trs.functions)
	# create solver and constraints
	solver = Solver()
	if DEBUG: print("Solver created...")
	# constraint 1: weight constraints
	solver.assert_exprs(W[0] > 0)
	for f, arity in trs.functions.items():
		solver.assert_exprs(P[f] >= 0)
		if arity == 0:
			solver.assert_exprs(W[f] >= W[0])
		elif arity == 1:
			local_constraints = []
			for g in trs.functions.keys():
				local_constraints.append(P[f] >= P[g])
			solver.assert_exprs(Implies(W[f] == 0, And(local_constraints)))
	if DEBUG: print("Weight constraints asserted...")
	# constraint 2: kbo constraint per rule
	for lhs, rhs in trs.rules:
		solver.assert_exprs(kbo(lhs, rhs, trs, W, P))
		if DEBUG: print("Rule constraint asserted...")
	if DEBUG:
		for c in solver.assertions():
			print(c.sexpr())
		print("Starting z3...")
		start_time = clock()
	if solver.check() == unsat:
		if DEBUG: print("Done - z3 ran for {} seconds.".format(clock() - start_time))
		return None
	else:
		model = solver.model()
		weights, precedence = {}, {}
		for f in trs.functions.keys():
			weights[f] = model[W[f]].as_long()
			precedence[f] = model[P[f]].as_long()
		weights[0] = model[W[0]].as_long()
		if DEBUG: print("Done - z3 ran for {} seconds.".format(clock() - start_time))
		return weights, precedence

# --------------------------------------------
# Make it a script!
# --------------------------------------------
if __name__ == '__main__':
	# construct argument parser
	parser = ArgumentParser("The man behind the curtain - KBO termination prover")
	parser.add_argument('filename', 
		help="Input file containing TRS")
	parser.add_argument('-d', 
		'--debug', action="store_true", 
		default=False, help="enables verbose output")
	arguments = parser.parse_args()
	# prove termination with provided arguments
	with open(arguments.filename, 'r') as f:
		data = f.read()
	trs = TRS(sexpr=parse_tpdb(data))
	if arguments.debug:
		print(trs.functions, trs.variables)
	ans = check_termination(trs, arguments.debug)
	if ans:
		print("terminating\nWeights: {}\nPrecedence: {}".format(*ans))
	else:
		print("nonterminating")