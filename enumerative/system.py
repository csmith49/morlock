from nodes import *
from parser import parse
from order import lt, ngeq
from collections import defaultdict

def rebase_pair(node, p):
    p_term = Node("_", p)
    var_list = variables(node)
    var_list.add(0)
    return rebase(p_term, max(var_list) + 1).kids

class System(object):
    def __init__(self, filename=None):
        self.equations = []
        if filename:
            with open(filename, 'r') as f:
                for line in f:
                    if line and "==" in line:
                        l, r = line.split("==")
                        l = parse(l.strip())
                        r = parse(r.strip())
                        self.equations.append( (l, r) )
    def __repr__(self):
        output = "System +---------->"
        for l, r in self.equations:
            output += "\n  " + format(l) + " == " + format(r)
        return output
    def apply_rule(self, node, rule):
        l, r = rebase_pair(node, rule)
        func = lambda n: match(n, l)
        C, sub = create_context(node, func)
        if sub:
            return insert_into(apply_sub(r, sub), C)
        return None
    def apply_equation(self, node, eq):
        l, r = eq
        ans = self.apply_rule(node, (l, r))
        if not ans:
            ans = self.apply_rule(node, (r, l))
        return ans
    def reduce(self, node):
        reducing = True
        ans = node
        while reducing:
            reducing = False    
            for eq in self.equations:
                red = self.apply_equation(ans, eq)
                if red and lt(red, ans):
                    ans = red
                    reducing = True
                    break
        return ans
    def is_normal(self, node):
        for eq in self.equations:
            red = self.apply_equation(node, eq)
            if red and lt(red, node):
                return False
        return True
    def reduce_equation(self, eq):
        return (self.reduce(eq[0]), self.reduce(eq[1]))
    def _ocp(self, s, t, u, v):
        C, sub = create_context(s, lambda n: match(n, u))
        if sub:
            l = apply_sub(t, sub)
            r = apply_sub(insert_into(v, C), sub)
            if lt(apply_sub(t, sub), apply_sub(s, sub)):
                if lt(apply_sub(v, sub), apply_sub(u, sub)):
                    return l, r
        else:
            return None
    def critical_pairs(self, eq):
        s, t = eq
        output = []
        for u, v in self.equations:
            u, v = rebase_pair(Node("_", eq), (u, v))
            output.append( self._ocp(s, t, u, v) )
            output.append( self._ocp(s, t, v, u) )
            output.append( self._ocp(t, s, u, v) )
            output.append( self._ocp(t, s, v, u) )
            output.append( self._ocp(u, v, s, t) )
            output.append( self._ocp(u, v, t, s) )
            output.append( self._ocp(v, u, s, t) )
            output.append( self._ocp(v, u, t, s) )
        return [o for o in output if o]
    def _optimize(self):
        rewrites = []
        for l, r in self.equations:
            if lt(r, l):
                rewrites.append( (l, r) )
            else:
                rewrites += [(l, r), (r, l)]
        self._optimized = defaultdict(list)
        for l, r in rewrites:
            self._optimized[l.val].append( (l, r) )
    def root_normal(self, node):
        for l, r in self._optimized[node.val]:
            sub = match(node, l)
            if sub and lt(apply_sub(r, sub), apply_sub(l, sub)):
                return False
        return True
        
def complete(equations):
    fresh = list(equations)
    system = System()
    while fresh:
        eq = system.reduce_equation(fresh.pop())
        l, r = eq
        if l != r:
            if (l, r) not in system.equations:
                if (r, l) not in system.equations:
                    system.equations.append(eq)
                    fresh += system.critical_pairs(eq)
    system._optimize()
    return system
    
def read_equations(filename):
    equations = []
    with open(filename, 'r') as f:
        for line in f:
            if line and "==" in line:
                l, r = line.split("==")
                l = parse(l.strip())
                r = parse(r.strip())
                equations.append( (l, r) )
    return equations
    
def Completion(filename):
    eqs = read_equations(filename)
    return complete(eqs)
    
if __name__ == "__main__":
    eqs = read_equations("./cfgs/peano.cfg")
    for l, r in eqs:
        print(format(l), format(r))
    print(complete(eqs))
