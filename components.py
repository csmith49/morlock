from scope import Scope, evaluate_in_scope, get_value
from utilities import *

class Function(object):
	def __init__(self, name, params, output, sexpr, scope):
		self.name = name
		self.parameters = params
		self.output = output
		self.sexpr = sexpr
		self.scope = scope
	def __call__(self, *args):
		arguments = dict_params_with(self.parameters, args)
		return evaluate_in_scope(self.sexpr, self.scope.update(arguments))

class SynthFun(object):
	def __init__(self, name, params, output, grammar, scope):
		self.name = name
		self.parameters = params
		self.output = output
		self.components = []
		self.scope = scope
		# gotta make the components
		nonterms = {}
		for symbol, sort, _ in grammar:
			nonterms[symbol] = sort
		# once nonterms grabbed, call component constructor
		for symbol, sort, productions in grammar:
			for sexpr in productions:
				self.components.append(Component(self, symbol, sort, sexpr, nonterms, scope))

class Component(object):
	counter = 0
	def __init__(self, synthfun, symbol, sort, sexpr, nonterms, scope):
		# do id stuff
		self._id = Component.counter
		Component.counter += 1
		# more storage stuff
		self.synthfun = synthfun
		self.symbol = symbol
		self.output = sort
		self.scope = scope
		# we don't wanna store the straight up sexpr, because vars are really non-terminals
		fresh_sexpr = []
		self.parameters = []
		for s, a in linearize_sexpr(sexpr):
			try:
				sort = nonterms[s]
				param_id = "PARAM.{}".format(len(self.parameters))
				self.parameters.append( (param_id, sort) )
				fresh_sexpr.append( (param_id, 0) )
			except:
				fresh_sexpr.append( (s, a) )
		self.sexpr = reconstruct_linearization(fresh_sexpr)
	def __call__(self, params, output, circuit_scope):
		scope = Scope.merge(circuit_scope, self.scope)
		arguments = dict_params_with(self.parameters, params)
		return evaluate_in_scope(self.sexpr, scope.update(arguments))
	def __repr__(self):
		return repr(self.sexpr)

class Variable(object):
	def __init__(self, name, sort):
		self.name = name
		self.sort = sort

class Constraint(object):
	def __init__(self, constraints, synth_function, variables, scope):
		self.constraints = constraints
		self.synth_function = synth_function
		self.variables = variables
		self.scope = scope
		# gotta get dat width
		self.width = 0
		for c in self.constraints:
			self.width += len(filter_sexpr(c, lambda s: s == self.synth_function.name))
		self.input = []
		for c in self.constraints:
			self.input += unique(filter_sexpr(c, lambda s: s in self.variables.keys()))
	def __call__(self, X, args):
		constraints = []
		# first, we'll update scope
		variables = {}
		for x in X:
			variables[x.parameter] = x.value
		scope = self.scope.update(variables)
		# now we need to evaluate constraints
		data = list(reversed(args))
		# now we'll evaluate
		for c in self.constraints:
			left, right = [], linearize_sexpr(c)
			# mostly copied from evaluate_with_scope
			while right:
				cur, arity = right.pop()
				if isinstance(cur, tuple):
					left.append(get_value(cur))
				elif arity != 0:
					args = []
					for i in range(arity):
						args.append(left.pop())
					if cur == self.synth_function.name:
						params, out = data.pop()
						left.append(out)
						for p, a in zip(params, args):
							constraints.append(p == a)
					else:
						op = scope[cur]
						left.append( op(*args) )
				else:
					left.append( scope[cur] )
			constraints.append(left[0])
		return And(constraints)
