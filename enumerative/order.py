from nodes import *
from enum import Enum
from itertools import product

Order = Enum("Order", "LT EQ GT INC")

def homo(node, free = None):
    if not free:
        free = lambda s: isinstance(s, int)
    output, stack = [], [node]
    while stack:
        val, kids = stack.pop()
        if free(val):
            output.append(None)
        else:
            output.append(str(val))
        stack += reversed(kids)
    return tuple([size(node)] + output)
    
def linear(l, r):
    l, r = homo(l), homo(r)
    try:
        if l < r:
            return Order.LT
        elif l > r:
            return Order.GT
        else:
            return Order.EQ
    except TypeError:
        return Order.INC
        
def lt(l, r, order=linear):
    if order(l, r) == Order.LT:
        return True
    else:
        return False
        
def ngeq(l, r, order=linear):
    if order(l, r) in (Order.LT, Order.INC):
        return True
    else:
        return False