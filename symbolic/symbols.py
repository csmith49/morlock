from z3 import *

mapping = {
	'bvand'		: (lambda a, b: a & b),
	'bvor'		: (lambda a, b: a | b),
	'bvxor'		: (lambda a, b: a ^ b),
	'bvadd'		: (lambda a, b: a + b),
	'bvsub'		: (lambda a, b: a - b),
	'='			: (lambda a, b: a == b),
	'bvmul'		: (lambda a, b: a * b),
	'bvudiv'	: UDiv,
	'bvurem'	: URem,
	'bvlshr'	: LShR,
	'bvashr'	: (lambda a, b: a >> b),
	'bvshl'		: (lambda a, b: a << b),
	'bvsdiv'	: (lambda a, b: a / b),
	'bvsrem'	: SRem,
	'bvneg'		: (lambda a: -a),
	'bvnot'		: (lambda a: ~a),
	'bvugt'		: UGT,
	'bvuge'		: UGE,
	'bvule'		: ULE,
	'bvsle'		: (lambda a, b: a <= b),
	'bvult'		: ULT,
	'bvslt'		: (lambda a, b: a < b),
	'bvredor'	: (lambda a: Not(a == BitVecVal(0, a.sort().sise()))),
	'+'			: (lambda a, b: a + b),
	'-'			: (lambda a, b: a - b),
	'*'			: (lambda a, b: a * b),
	'ite'		: If,
	'and'		: And,
	'or'		: Or,
	'not'		: Not,
	'xor'		: Xor,
	'<='		: (lambda a, b: a <= b),
	'>='		: (lambda a, b: a >= b),
	'>'			: (lambda a, b: a > b),
	'<'			: (lambda a, b: a < b),
	'=>'		: Implies,
	'_ID'		: (lambda a: a),
}

def map_symbol(symbol):
	try:
		return mapping[symbol]
	except KeyError:
		raise Exception("No such symbol {}".format(symbol))