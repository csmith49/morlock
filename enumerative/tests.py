from parser import parse
from nodes import *
from grammars import Grammar
from system import System, Completion 
from iteration import bottom_up, top_down, metric, normalized_bottom_up
'''
print("---")
print("TESTING PARSING AND PRINTING")
term = parse("plus(square(two), exp(two, thirteen))")
pprint(term)

print("---")
print("TESTING MATCHING")
pattern = parse("plus(1, 2)")
sub = match(term, pattern)
print(sub)
pprint(apply_sub(term, sub))
pprint(apply_sub(pattern, sub))

print("---")
print("TESTING UNIFICATION")
l = parse("f(g, 1)")
r = parse("f(2, k(3))")
pprint(l)
pprint(r)
print(unify(l, r))
'''
print("---")
print("TESTING GRAMMARS")
nat = Grammar("./cfgs/naturals.cfg")
peano = Grammar("./cfgs/peano.cfg")
'''
print("---")
print("TESTING TOPDOWN")
for i, term in enumerate(top_down(peano, metric)):
    if i > 1000:
        break
print("  1000 generated")

print("---")
print("TESTING BOTTOMUP")
for i, term in enumerate(bottom_up(peano)):
    if size(term) > 10:
        break
    count, ans = i, term
print("Count: ", count)
print("Last: ", format(ans))

print("---")
print("TESTING SYSTEMS")
system = System("./cfgs/peano.cfg")
print(system)
term = parse("plus(succ(pred(succ(0))),zero)")
print("Reducing: " + format(term))
print("  " + format(system.reduce(term)))
'''
print("---")
print("TESTING NORMALITY")
test1 = set()
comp = Completion("./cfgs/peano.cfg")
for i, term in enumerate(normalized_bottom_up(peano, comp)):
    if size(term) > 10:
        break
    test1.add(format(term))
