from z3 import Implies, Not, And
from itertools import combinations, chain
from collections import defaultdict
from scope import Scope

def group(iter, key_func):
	result = defaultdict(list)
	for value in iter:
		result[key_func(value)].append(value)
	return result

def create_wfp_constraint(L, N):
	constraints = []
	# consistency constraint
	return_locations = [l.value for l in L if l.type == "return"]
	for x, y in combinations(return_locations, 2):
		constraints.append(Not(x == y))
	# acyclicity constraint
	for comp_id in set(l.component for l in L):
		output = [l.value for l in L if l.type == "return" and l.component == comp_id][0]
		for parameter in [l.value for l in L if l.type == "parameter" and l.component == comp_id]:
			constraints.append(parameter < output)
	# parameter interpretation
	for p in [l.value for l in L]:
		constraints.append(0 <= p)
		constraints.append(p < N)
	return And(constraints)

def create_lib_constraint(T, I, components):
	constraints = []
	for comp_id, variables in group(T, lambda v: v.component).items():
		component = components[comp_id]
		output = [t.value for t in variables if t.type == "return"][0]
		params = [t.value for t in variables if t.type == "parameter"]
		# need to pass I in as formal parameter scope
		formal_scope = {}
		for ps, i in zip(component.synthfun.parameters, I):
			formal_scope[ps[0]] = i.value
		constraints.append(output == component(params, output, Scope(formal_scope)))
	return And(constraints)

def create_conn_constraint(O, T, locations):
	constraints = []
	variables = chain.from_iterable([O, T])
	for x, y in combinations(variables, 2):
		x_loc, y_loc = locations[x], locations[y]
		constraints.append(Implies(x_loc == y_loc, x.value == y.value))
	return And(constraints)

def create_spec_constraint(I, O, X, constraint):
	outputs = []
	params = []
	for _, variables in group(O, lambda v: v.width).items():
		outputs.append(variables[0].value)
	for _, variables in group(I, lambda v: v.width).items():
		params.append( [v.value for v in variables] )
	return constraint(X, list(zip(params, outputs)))

def create_pattern_constraints(L, components, system):
	return system.constrain(L, components)