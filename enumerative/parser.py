import ply.lex as lex
import ply.yacc as yacc
from nodes import Node, pprint

tokens = ("NAME", "LPAREN", "RPAREN", "COMMA", "INT")

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_NAME = r'[a-zA-Z]+'
t_INT = r'[0-9]+'
t_ignore = " \t"
def t_error(t):
    print("Illegal char '%s'" % t.value[0])
    t.lexer.skip(1)
    
lexer = lex.lex()

def p_tree(p):
    '''tree : inner
            | leaf'''
    p[0] = p[1]

def p_leaf(p):
    '''leaf : NAME
            | INT'''
    try:
        val = int(p[1])
    except:
        val = p[1]
    p[0] = Node(val, [])
    
def p_inner(p):
    '''inner : NAME LPAREN list RPAREN'''
    p[0] = Node(p[1], p[3])

def p_list(p):
    '''list : tree COMMA list
            | tree'''
    if len(p) > 2:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]
        
parser = yacc.yacc()

def parse(string):
    return parser.parse(string)

if __name__ == "__main__":
    while True:
        try:
            s = input('node> ')
        except EOFError:
            break
        pprint(parser.parse(s))