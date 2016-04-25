from collections import namedtuple
from z3 import Int, Const, IntSort
from scope import get_sort

Location = namedtuple("Location", "type parameter component value")
Input = namedtuple("Input", "example width parameter value")
Output = namedtuple("Output", "example width value")
Temp = namedtuple("Temp", "type parameter component example width value")
Spec = namedtuple("Spec", "parameter value")

def create_location_variables(components):
	L = []
	for comp_id, component in components.items():
		for param, sort in component.parameters:
			l_id = "l.{}.{}.{}".format("parameter", param, comp_id)
			l = Location("parameter", param, comp_id, Const(l_id, IntSort()))
			L.append(l)
		l_id = "l.{}.{}.{}".format("return", None, comp_id)
		l = Location("return", None, comp_id, Const(l_id, IntSort()) )
		L.append(l)
	return L

def create_input_variables(params, example, width):
	I = []
	for p, s in params:
		i_id = "i.{}.{}.{}".format(example, width, p)
		i = Input(example, width, p, Const(i_id, get_sort(s)))
		I.append(i)
	return I

def create_output_variables(return_sort, example, width):
	o_id = "o.{}.{}".format(example, width)
	o = Output(example, width, Const(o_id, get_sort(return_sort)))
	return [o]

def create_temp_variables(components, example, width):
	T = []
	for comp_id, component in components.items():
		for p, s in component.parameters:
			t_id = "t.{}.{}.{}.{}.{}".format("parameter", p, comp_id, example, width)
			t = Temp("parameter", p, comp_id, example, width, Const(t_id, get_sort(s)))
			T.append(t)
		t_id = "t.{}.{}.{}.{}.{}".format("return", None, comp_id, example, width)
		t = Temp("return", None, comp_id, example, width, Const(t_id, get_sort(component.output)))
		T.append(t)
	return T

def create_spec_variables(constraint, variables):
	X = []
	for p in constraint.input:
		x_id = "x.{}".format(p)
		X.append( Spec(p, Const(x_id, get_sort(variables[p].sort))) )
	return X

def create_location_map(I, O, T, L, card_I, N):
	locations = {}
	for index, i in enumerate(I):
		locations[i] = index
	locations[O[0]] = card_I + N - 1
	for t in T:
		locations[t] = [l.value for l in L if l.component == t.component and l.parameter == t.parameter][0]
	return locations


