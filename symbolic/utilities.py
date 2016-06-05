from itertools import filterfalse
from z3 import *

def linearize_sexpr(sexpr):
	left = [sexpr]
	right = []
	while left:
		cur = left.pop()
		if isinstance(cur, list):
			op, *args = cur
			right.append( (op, len(args)) )
			left += reversed(args)
		else:
			right.append( (cur, 0) )
	return right

def reconstruct_linearization(li):
	left, right = [], list(li)
	while right:
		cur, arity = right.pop()
		if arity != 0:
			args = []
			for i in range(arity):
				args.append(left.pop())
			left.append([cur] + args)
		else:
			left.append(cur)
	return left[0]

def filter_sexpr(sexpr, f):
	flat = linearize_sexpr(sexpr)
	return [s for s, a in flat if f(s)]

def map_sexpr(sexpr, m):
	flat = linearize_sexpr(sexpr)
	data = [(m(s), a) for s, a in flat]
	return reconstruct_linearization(data)

def dict_params_with(params, li):
	output = {}
	for ps, i in zip(params, li):
		output[ps[0]] = i
	return output

def find_in_list(li, key_func):
	intermediate = [l for l in li if key_func(l)]
	return intermediate[0]

def unique(iterable, key=None):
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element

def div(x, y):
	return (x - (x % y)) / y

def breakout(term):
	if isinstance(term, list): return term
	else: return [term]

def get_output(comp_id, L):
	poss = [l for l in L if l.type == "return" and l.component == comp_id]
	return poss[0]

def get_ith_input(comp_id, i, L):
	poss = [l for l in L if l.parameter == "PARAM.{}".format(i) and l.component == comp_id]
	return poss[0]