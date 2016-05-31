def parse_sexpr(string):
	# parses s-expressions into lists
	sexpr = [[]]
	word = ''
	in_str = False
	for c in string:
		if c == '(' and not in_str:
			sexpr.append([])
		elif c == ')' and not in_str:
			if word:
				sexpr[-1].append(parse_token(word))
				word = ''
			temp = sexpr.pop()
			sexpr[-1].append(temp)
		elif c in (' ', '\n', '\t') and not in_str:
			if word:
				sexpr[-1].append(parse_token(word))
			word = ''
		elif c == '"':
			in_str = not in_str
		else:
			word += c
	return sexpr[0]

def parse_token(string):
	# first try to convert it to an integer
	try:
		return ('Int', int(string))
	except: pass
	# then try to turn it into a boolean
	if string == 'true':
		return ('Bool', 1)
	elif string == 'false':
		return ('Bool', 0)
	# lastly interpret it as a bit-vector
	if string.startswith('#b'):
		bits = int(string[2:], 2)
		length = len(string) - 2
		return (['BitVec', ('Int', length)], bits)
	elif string.startswith('#x'):
		bits = int(string[2:], 16)
		length = (len(string) - 2) * 4
		return (['BitVec', ('Int', length)], bits)
	# if all else fails, just give the string back
	return string

def pre_parse_pass(string):
	# wraps string in one more layer of parentheses
	# and removes comments (denoted by ;)
	out = '('
	for line in string.split('\n'):
		out += line.split(';', 1)[0]
	return out + ')'

def load_file(filename):
	with open(filename, 'r') as f:
		return parse_sexpr(pre_parse_pass(f.read()))