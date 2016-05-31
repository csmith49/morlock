import terms
from functools import partial
from itertools import product
from z3 import And, Not, simplify, Or, BoolSort, Const
from collections import defaultdict
from itertools import combinations, permutations
from setup import DEBUG

class System(object):
	def __init__(self, sexpr):
		self.variables = set()
		self.weights = {}
		self.rules = []
		self.equations = []
		self.parse(sexpr)
		# once we have our set of variables, we can get the match function for our system
		self.match = partial(terms.match, is_variable=self._is_var)
		self.components = []
	def _is_var(self, t):
		# a bit of a hack - variables are anything the configuration file says are variables
		# (which can cause problems if namespaces clash) and anything that we've formatted
		# like an input variable for our components
		if isinstance(t, str):
			if t.startswith("PARAM."):
				return True
			elif t in self.variables:
				return True
			else:
				return False
		else:
			return False
	def parse(self, sexpr):
		# simple enough, just iterate over sexpr and add the appropriate values
		for cmd, *args in sexpr:
			if cmd == "vars":
				self.variables.update(args)
			elif cmd == "rules":
				self.rules += args
			elif cmd == "eqs":
				self.equations += args
			elif cmd == "weights":
				self.weights.update(dict(args))
			else:
				pass
	def _invert(self, t):
		# we're working backwards from terms over the rules to terms over components
		# base case: we can't change variables
		if self._is_var(t):
			yield t
		# for each component, we'll try and find a match
		for comp_id, c in self.components.items():
			s = self.match(c.sexpr, t)
			# if there's no match, we're done
			if s is None:
				continue
			# we don't need to solve any subproblems if there arent any
			if len(s.keys()) == 0:
				yield comp_id
				continue
			# for each subproblem, choose a solution to get a real value
			params = list(sorted(s.keys()))
			# yeah, we should really be caching the results - this is a DP algorithm
			subproblems = [list(self._invert(s[p])) for p in params]
			for sol in product(*subproblems):
				sub = terms.Substitution(dict(list(zip(params, sol))))
				yield sub([comp_id] + params)
	def _pattern(self, pattern, L):
		# we can exit early if we have a variable
		if self._is_var(pattern):
			return True
		constraints = [True]
		f, *args = breakout(pattern)
		# now we'll recurse appropriately
		for i, arg in enumerate(args):
			constraints.append( self._connect(f, i, arg, L) )
			constraints.append( self._pattern(arg, L))
		return simplify(And(constraints))
	def _connect(self, f, i, t, L):
		if self._is_var(t):
			return True
		g, *args = breakout(t)
		return (get_output(g, L).value == get_ith_input(f, i, L).value)
	def _constrain_eq_vars(self, E, L):
		constraints = []
		for l, r in combinations(L, 2):
			if l.type == "return" and r.type == "return":
				lcomp, rcomp = self.components[l.component], self.components[r.component]
				if lcomp.sexpr != rcomp.sexpr:
					constraints.append( E[(l, r)] == False )
				else:
					local = [True]
					for i in range(len(lcomp.parameters)):
						li, ri = get_ith_input(l.component, i, L), get_ith_input(r.component, i, L)
						local.append( E[(li, ri)] )
					constraints.append( E[(l, r)] == And(local) )
			elif l.type == "parameter" and r.type == "parameter": # type is parameter
				local = [(l.value == r.value)]
				for f, g in permutations([get_output(c, L) for c, _ in self.components.items()], 2):
					local.append( And([l.value == f.value, r.value == g.value, E[(f, g)]]) )
				constraints.append( E[(l, r)] == Or(local) )
		return simplify(And(constraints))
	def _extract_equalities(self, p, L):
		# we'll iterate over the term - any time we see a variable, we record the location
		# this lets us look at the resulting dict to find when we have >= 2 occurrences of a var
		eqs = defaultdict(list)
		worklist = [p]
		while worklist:
			f, *args = breakout(worklist.pop())
			for i, arg in enumerate(args):
				if self._is_var(arg):
					eqs[arg].append(get_ith_input(f, i, L))
			worklist += args
		return eqs
	def constrain(self, L, components):
		constraints = []
		# for scoping issues
		self.components = components
		# get eq variables
		E = EqMap()
		if DEBUG: print(E)
		constraints.append(self._constrain_eq_vars(E, L))
		# now get all patterns and do the thing
		for l, _ in self.rules:
			for p in self._invert(l):
				local = []
				local.append(self._pattern(p, L))
				eqs = self._extract_equalities(p, L)
				# add eq constraints from pattern
				for k, li in eqs.items():
					for s, t in combinations(li, 2):
						local.append( E[(s, t)] )
				constraints.append( Not(And(local)) )
		return And(constraints)

class EqMap(object):
	def __init__(self):
		self._dict = {}
	def _key(self, l):
		return "{}.{}".format(l.component, l.parameter)
	def _norm(self, l, r):
		if self._key(l) <= self._key(r): return (l, r)
		else: return (r, l)
	def __getitem__(self, key):
		l, r = self._norm(*key)
		if l.type != r.type:
			return False
		elif self._key(l) == self._key(r):
			return True
		else:
			k = (self._key(l), self._key(r))
			if k not in self._dict.keys():
				c_id = "eq.{}".format(k)
				self._dict[k] = Const(c_id, BoolSort())
			return self._dict[k]
	def __repr__(self):
		return repr(self._dict.keys())

def breakout(term):
	# we're doing this anyways in pretty much every instance of recursion
	# let's us cobble together a pattern-matching deconstruction of terms
	if isinstance(term, list): return term
	else: return [term]

# helper functions for accessin our list of location variables appropriately
def get_output(comp_id, L):
	possibilities = [l for l in L if l.type == "return" and l.component == comp_id]
	return possibilities[0]

def get_ith_input(comp_id, i, L):
	possibilities = [l for l in L if l.parameter == "PARAM.{}".format(i) and l.component == comp_id]
	return possibilities[0]