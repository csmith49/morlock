import terms
from functools import partial
from z3 import And, Not, simplify, Or, Bool, Int, Implies
from collections import defaultdict
from itertools import combinations, permutations, product, count
from setup import DEBUG
from utilities import breakout, get_output, get_ith_input, div

class IntMap(object):
	def __init__(self, id):
		self._id = id
		self._dict = {}
	def _key(self, l):
		return "{}.{}".format(l.component, l.parameter)
	def __getitem__(self, key):
		k = self._key(key)
		if k not in self._dict.keys():
			c_id = "{}.{}".format(self._id, k)
			self._dict[k] = Int(c_id)
		return self._dict[k]
	def __repr__(self):
		return repr(self._dict.keys())

#------------------------------------------------------------------------------
# System contains all the information we need to extend the default encoding
#------------------------------------------------------------------------------

class System(object):
	def __init__(self, sexpr):
		self.term_variables = set()
		self.func_weights = {}
		self.var_weight = 1
		self.func_prec = {}
		self.rules = []
		self.equations = []
		self.parse(sexpr)
		self.match = partial(terms.match, is_variable=self._is_var)
		self.components = []
		self.comp_weights = {}
		self.comp_prec = {}
	def _is_var(self, t):
		if isinstance(t, str):
			if t.startswith("PARAM"):
				return True
			return t in self.term_variables
		return False
	def parse(self, sexpr):
		# we're just picking things up from the input file at this point
		for cmd, *args in sexpr:
			if cmd == "vars":
				self.term_variables.update(args)
			elif cmd == "rules":
				self.rules += args
			elif cmd == "eqs":
				self.equations += args
			elif cmd == "weights":
				for f, a in args:
					self.func_weights[f] = a[1]
			elif cmd == "prec":
				for f, a in args:
					self.func_prec[f] = a[1]
			else:
				pass

	#--------------------------------------------------------------------------
	# Functions for creating rules over components and turning them into 
	# patterns to avoid
	#--------------------------------------------------------------------------

	def _invert_term(self, t):
		# we're turning term t from term over rule symbols to term over components
		# base case: can't touch variables
		if self._is_var(t):
			yield t
		# for each component, see if there's a match
		for comp_id, c in self.components.items():
			s = self.match(c.sexpr, t)
			# if there's no match here, the component isn't compatible
			if s is None:
				continue
			# don't have to solve subproblem if there aren't any!
			if len(s.keys()) == 0:
				yield comp_id
				continue
			# otherwise, we have to look over all possible solutions and yield results
			params = list(sorted(s.keys()))
			# yeah, probs cache this
			subproblems = [list(self._invert_term(s[p])) for p in params]
			for solution in product(*subproblems):
				sub = terms.Substitution(dict(list(zip(params, solution))))
				yield sub([comp_id] + params)
	def _pattern(self, pattern, L):
		# if our pattern is just a variable, we can quit
		if self._is_var(pattern):
			return True
		constraints = [True]
		f, *args = breakout(pattern)
		# now we recurse
		for i, arg in enumerate(args):
			constraints.append( self._connect(f, i, arg, L) )
			constraints.append( self._pattern(arg, L) )
		return And(constraints)
	def _connect(self, f, i, t, L):
		if self._is_var(t):
			return True
		g, *args = breakout(t)
		return (get_output(g, L).value == get_ith_input(f, i, L).value)

	#--------------------------------------------------------------------------
	# Functions for constraining non-linear and conditional rules 
	#--------------------------------------------------------------------------
	
	def _kappa(self, t, L, K, subs=None):
		# if our substitutions don't exist, fix that
		if subs is None:
			subs = {}
		# pull off the head
		f, *args = breakout(t)
		# start recursive computation
		total = (self.M ** self.N) * self.comp_prec[f]
		current = self.comp_weights[f]
		for i, arg in enumerate(args):
			# when it comes time to recurse, we handle variables differently
			if self._is_var(arg):
				# if we've already seen the variable, reference the original instead
				try:
					ks_i = subs[arg]
				# otherwise make a note and get the appropriate K var
				except KeyError:
					ks_i = K[get_ith_input(f, i, L)]
					subs[arg] = ks_i
			# of course, our recursive calls now introduce subs
			else:
				ks_i, s = self._kappa(arg, L, K, subs)
				subs.update(s)
			total += div(ks_i, self.M ** i)
			current += div(ks_i, self.P * (self.M ** self.N))
		total += self.P * (self.M ** self.N) * current
		return total, subs
	def _gather_equalities(self, t, L, K):
		variables = defaultdict(list)
		worklist = [t]
		while worklist:
			f, *args = breakout(worklist.pop())
			for i, arg in enumerate(args):
				if self._is_var(arg):
					variables[arg].append(get_ith_input(f, i, L))
				else:
					worklist.append(arg)
		constraints = []
		for var, instances in variables.items():
			for x, y in combinations(instances, 2):
				constraints.append( K[x] == K[y] )
		return And(constraints)
	def constrain_rule(self, rule, L, K, conditional=False):
		constraints = []
		l, r = rule
		constraints.append( self._pattern(l, L) )
		constraints.append( self._gather_equalities(l, L, K) )
		if conditional:
			kappa_l, record = self._kappa(l, L, K)
			kappa_r, _ = self._kappa(r, L, K, subs=record)
			constraints.append( kappa_l > kappa_r )
		return Not(And(constraints))

	#--------------------------------------------------------------------------
	# Methods for creating constraints over the weights and kappa variables 
	#--------------------------------------------------------------------------

	def constrain_weights(self, L, W):
		constraints = []
		for comp_id, comp in self.components.items():
			total = self.comp_weights[comp_id]
			total += sum([get_ith_input(comp_id, i, L).value for i in range(comp.arity)])
			constraints.append( W[get_output(comp_id, L)] == total )
		return And(constraints)
	def constrain_connections(self, L, W, K):
		constraints = []
		for x, y in combinations(L, 2):
			constraints.append( Implies(x.value == y.value, And(W[x] == W[y], K[x] == K[y])) )
		return And(constraints)
	def constrain_kappas(self, L, K):
		constraints = []
		for comp_id, comp in self.components.items():
			total = (self.M ** self.N) * self.comp_prec[comp_id]
			current = self.comp_weights[comp_id]
			for i in range(comp.arity):
				ks_i = K[get_ith_input(comp_id, i, L)]
				total += div(ks_i, self.M ** i)
				current += div(ks_i, self.P * (self.M ** self.N))
			total += self.P * (self.M ** self.N) * current
			constraints.append( K[get_output(comp_id, L)] == total )
		return And(constraints)

	#--------------------------------------------------------------------------
	# Let's make a formula!
	#--------------------------------------------------------------------------

	def constrain(self, L, components):
		constraints = []
		# for scoping purposes
		self.components = components
		# still need to update self.comp_weights and self.comp_prec
		for comp_id, comp in components.items():
			f, *args = breakout(comp.sexpr)
			# need to handle the case when f is a program input, or not in rules
			try:
				self.comp_weights[comp_id] = self.func_weights[f]
				self.comp_prec[comp_id] = self.func_prec[f]
			except KeyError:
				self.comp_weights[comp_id] = 1 + self.var_weight
				for i in count():
					if i not in self.comp_prec.values():
						self.comp_prec[comp_id] = i
						break
		self.M = max(self.comp_weights.values()) * len(self.components) + 1
		self.N = len(self.components)
		self.P = max(self.comp_prec.values()) + 1
		# now we make all our variables
		K = IntMap('kappa')
		W = IntMap('w')
		# and add the constraints defining eq and kbo and all that jazz
		constraints.append( self.constrain_weights(L, W) )
		constraints.append( self.constrain_connections(L, W, K) )
		constraints.append( self.constrain_kappas(L, K) )
		# now, look over rules and equations to pick up constrainst
		# uh...
		# and enforce that patterns never show up
		for l, r in self.rules:
			for p in self._invert_term(l):
				constraints.append( self.constrain_rule((p, None), L, K) )
		for l, r in self.equations:
			for p, q in product(self._invert_term(l), self._invert_term(r)):
				constraints.append( self.constrain_rule((p, q), L, K, conditional=True))
		return And(constraints)
