from collections import defaultdict
from nodes import *
from parser import parse

# class for representing our grammar
# describes regular tree languages
# provide filename containing lines of the form
# NONTERMINAL -> RULE | RULE | ... | RULE
class Grammar(object):
    def __init__(self, filename):
        self.nonterminals = set()
        self.rules = defaultdict(list)
        with open(filename, 'r') as f:
            for line in f:
                if line and "->" in line:
                    n, r = line.split("->")
                    n = n.strip()
                    self.nonterminals.add(n)
                    for term in r.split("|"):
                        rule = parse(term.strip())
                        self.rules[n].append(rule)
        self.start = Node("S", [])
    def __repr__(self):
        output = "Grammar +---------> \n"
        output += "Nonterms:\n  " + repr(self.nonterminals) + "\n"
        output += "Rules:"
        for non in self.rules.keys():
            for rule in self.rules[non]:
                output += "\n  " + non + " -> " + format(rule)
        return output
    # given term with non-terminals, applies arbitrary expansion rules to
    # the left-most possible spot
    def refine(self, node):
        def expand(n):
            if n.val in self.nonterminals:
                return self.rules[n.val]
            else:
                return None
        C, possibilities = create_context(node, expand)
        if not possibilities:
            return None
        return [insert_into(p, C) for p in possibilities]
    # turn rule into term with vars, include map from vars to nonterms
    def convert_to_vars(self, node):
        nonterms = []
        left, right = [node], []
        while left:
            cur = left.pop()
            if cur.val in self.nonterminals:
                right.append( (len(nonterms), 0) )
                nonterms.append(cur.val)
            else:
                right.append( (cur.val, len(cur.kids)) )
            for k in reversed(cur.kids):
                left.append(k)
        while right:
            val, arity = right.pop()
            kids = []
            for i in range(arity):
                kids.append(left.pop())          
            left.append(Node(val, kids))
        return left[0], nonterms

if __name__ == "__main__":
    gram = Grammar("./cfgs/peano.cfg")
    print(gram)