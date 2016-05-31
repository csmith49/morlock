class Substitution(object):
	def __init__(self, d = None):
		self._dict = {}
		if d != None:
			self._dict.update(d)
	def __call__(self, term):
		return self._apply(term)
	def _apply(self, term):
		if isinstance(term, list):
			f, *args = term
			return [f] + [self._apply(a) for a in args]
		else:
			try:
				return self._dict[term]
			except:
				return term
	def __setitem__(self, key, value):
		self._dict[key] = value
	def __getitem__(self, key):
		return self._dict[key]
	def keys(self):
		return self._dict.keys()
	def __repr__(self):
		return repr(self._dict)

def default_is_var(t):
	return isinstance(t, int)

def match(term, pattern, is_variable = default_is_var):
	sub = Substitution()
	worklist = [(term, pattern)]
	while worklist:
		# first get the next subproblem and apply current sub
		t, p = worklist.pop()
		t, p = sub(t), sub(p)
		# case 1: both are lists, so we check f's match and same size
		if isinstance(t, list) and isinstance(p, list):
			if t[0] != p[0] or len(t) != len(p):
				return None
			# add new subproblems
			worklist += list(zip(t[1:], p[1:]))
		# if we've got a variable, add p to sub
		elif is_variable(t):
			sub[t] = p
		# otherwise we only care if t isn't p
		elif t != p:
			return None
	return sub