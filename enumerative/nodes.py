from collections import namedtuple
from enum import Enum

# data types
Node = namedtuple("Node", "val kids")

# pretty printing, done recursively
def pprint(node):
    print(format(node))

def format(n):
    out = str(n.val)
    if n.kids:
        out += "(" + ",".join([format(k) for k in n.kids]) + ")"
    return out

def size(n):
    out = 1
    if n.kids:
        out += sum(size(k) for k in n.kids)
    return out

# applies a sub to a term
def apply_sub(node, sub):
    if not sub:
        return node
    left, right = [node], []
    while left:
        cur = left.pop()
        right.append( (cur.val, len(cur.kids)) )
        for k in reversed(cur.kids):
            left.append(k)
    while right:
        val, arity = right.pop()
        kids = []
        for i in range(arity):
            kids.append(left.pop())
        if isinstance(val, int):
            try:
                left.append(sub[val])
            except KeyError:
                left.append(Node(val, kids))
        else:
            left.append(Node(val, kids))
    return left[0]
    
# one-sided unification
def match(term, pattern):
    sub = {}
    worklist = [ (term, pattern) ]
    while worklist:
        t, p = worklist.pop()
        p = apply_sub(p, sub)
        if isinstance(p.val, int):
            sub[p.val] = t
        elif t.val == p.val:
            worklist += zip(t.kids, p.kids)
        else:
            return None
    return sub

###########################
# finds variables in a term
def variables(node):
    result = set()
    worklist = [node]
    while worklist:
        v, kids = worklist.pop()
        if isinstance(v, int):
            result.add(v)
        worklist += kids
    return result

# rebases down to 0, 1, 2, ...
def rebase(node, lower = 0):
    sub = {v : Node(i + lower, []) for i, v in enumerate(variables(node))}
    return apply_sub(node, sub)

def freshen(l, r):
    l = rebase(l)
    r = rebase(r, lower=max(variables(l)))
    return l, r

# unification!
def unify(pat1, pat2):
    sub = {}
    worklist = [ (pat1, pat2) ]
    while worklist:
        l, r = worklist.pop()
        l = apply_sub(l, sub)
        r = apply_sub(r, sub)
        if l.val == r.val:
            worklist += zip(l.kids, r.kids)
        elif isinstance(l.val, int):
            if l.val in variables(r):
                return None
            else:
                sub[l.val] = r
        elif isinstance(r.val, int):
            if r.val in variables(l):
                return None
            else:
                sub[r.val] = l
        else:
            return None
    return sub
    
Context = namedtuple("Context", "terms symbols")

def insert_into(node, context):
    terms = list(context.terms) + [node]
    symbols = list(context.symbols)
    while symbols:
        val, arity = symbols.pop()
        kids = []
        for i in range(arity):
            kids.append(terms.pop())
        terms.append(Node(val, kids))
    return terms[0]
    
def create_context(node, func = lambda s : None):
    left, right = [node], []
    while left:
        n = left.pop()
        fn = func(n)
        if fn:
            return Context(left, right), fn
        right.append( (n.val, len(n.kids)) )
        left += reversed(n.kids)
    return Context(left, right), None