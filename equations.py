import terms
from functools import partial
from itertools import product
from z3 import And, Not, simplify, Or
from collections import defaultdict

class System(object):
	def __init__(self, sexpr):
		self.variables = set()
		self.weights = {}
		self.rules = []
		self.equations = []
		self.parse(sexpr)
		self.match = partial(terms.match, is_variable=self._is_var)
		self.components = []
	def _is_var(self, t):
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
		if self._is_var(t):
			yield t
		for comp_id, c in self.components.items():
			s = self.match(c.sexpr, t)
			# if there's no match, we're done
			if s is None:
				continue
			# we don't need to solve any subproblems if there arent any
			if len(s.keys()) == 0:
				yield comp_id
				continue
			params = list(sorted(s.keys()))
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
	def _eqi(self, l, r, L):
		if l.component == r.component:
			return True
		constraints = []
		for s, t in product([l for l in L if l.type == "return"], repeat=2):
			constraints.append( And([(l.value == s.value), (r.value == t.value), self._eqo(s, t)]) )
		return Or(constraints)
	def _eqo(self, l, r, L):
		if self.components[l.component].sexpr != self.components[r.component].sexpr:
			return False
		constraints = [True]
		f, g = l.component, r.component
		arity = len(self.components[f].parameters)
		for i in range(arity):
			constraints.append(self._eqi(get_ith_input(f, i, L).value, get_ith_input(g, i, L).value))
		return And(constraints)
	def extract_equalities(self, p, L):
		eqs = defaultdict(list)
		worklist = [p]
		while worklist:
			f, *args = breakout(worklist.pop())
			for i, arg in enumerate(args):
				if self._is_var(arg):
					eqs[arg].append(get_ith_input(f, i, L))
			worklist += args
		return eqs

def breakout(term):
	if isinstance(term, list):
		return term
	else:
		return [term]

# helper functions for accessin our list of location variables appropriately
def get_output(comp_id, L):
	possibilities = [l for l in L if l.type == "return" and l.component == comp_id]
	return possibilities[0]

def get_ith_input(comp_id, i, L):
	possibilities = [l for l in L if l.parameter == "PARAM.{}".format(i) and l.component == comp_id]
	return possibilities[0]