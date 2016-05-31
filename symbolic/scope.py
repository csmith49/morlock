from symbols import mapping
from z3 import BitVec, BoolSort, BitVecSort, BoolVal, BitVecVal, IntSort, IntVal

class Scope(object):
	def __init__(self, m = None):
		self._symbol_map = {}
		if m is not None:
			self._symbol_map.update(m)
	def zoom(self):
		return Scope(self._symbol_map)
	def __getitem__(self, name):
		return self._symbol_map[name]
	def __setitem__(self, name, value):
		self._symbol_map[name] = value
	def update(self, d):
		scope = {}
		scope.update(self._symbol_map)
		scope.update(d)
		return Scope(scope)
	def keys(self):
		return self._symbol_map.keys()
	@classmethod
	def merge(cls, a, b):
		scope = {}
		scope.update(a._symbol_map)
		scope.update(b._symbol_map)
		return Scope(scope)

def evaluate_in_scope(sexpr, scope):
	left, right = [sexpr], []
	while left:
		cur = left.pop()
		if isinstance(cur, list):
			op, *args = cur
			right.append( (op, len(args)) )
			left += reversed(args)
		else:
			right.append( (cur, 0) )
	while right:
		cur, arity = right.pop()
		if isinstance(cur, tuple):
			left.append(get_value(cur))
		elif arity != 0:
			args = []
			for i in range(arity):
				args.append(left.pop())
			try:
				op = scope[cur]
			except KeyError:
				op = mapping[cur]
			left.append( op(*args) )
		else:
			try:
				left.append( scope[cur] )
			except KeyError:
				left.append( mapping[cur] )
	return left[0]

def get_sort(type):
	# converts parsed type into z3 sort
	if type == 'Int':
		return IntSort()
	elif type == 'Bool':
		return BoolSort()
	elif isinstance(type, list) and type[0] == 'BitVec':
		return BitVecSort(type[1][1])
	else: raise Exception("Unsupported type {}".format(str(type)))

def get_value(const):
	# converts parsed constants into raw z3 values
	type, val = const
	sort = get_sort(type)
	if sort == IntSort():
		return IntVal(val)
	elif sort == BoolSort():
		return BoolVal(val)
	else:
		size = sort.size()
		return BitVecVal(val, size)