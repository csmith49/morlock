
# parsetab.py
# This file is automatically generated. Do not edit.
_tabversion = '3.8'

_lr_method = 'LALR'

_lr_signature = '0C58992C9904FB78FD35BF63EAD59F2E'
    
_lr_action_items = {'NAME':([0,6,10,],[2,2,2,]),'INT':([0,6,10,],[3,3,3,]),'LPAREN':([2,],[6,]),'$end':([1,2,3,4,5,9,],[-2,-3,-4,0,-1,-5,]),'RPAREN':([1,2,3,5,7,8,9,11,],[-2,-3,-4,-1,9,-7,-5,-6,]),'COMMA':([1,2,3,5,8,9,],[-2,-3,-4,-1,10,-5,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'leaf':([0,6,10,],[1,1,1,]),'tree':([0,6,10,],[4,8,8,]),'inner':([0,6,10,],[5,5,5,]),'list':([6,10,],[7,11,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> tree","S'",1,None,None,None),
  ('tree -> inner','tree',1,'p_tree','parser.py',20),
  ('tree -> leaf','tree',1,'p_tree','parser.py',21),
  ('leaf -> NAME','leaf',1,'p_leaf','parser.py',25),
  ('leaf -> INT','leaf',1,'p_leaf','parser.py',26),
  ('inner -> NAME LPAREN list RPAREN','inner',4,'p_inner','parser.py',34),
  ('list -> tree COMMA list','list',3,'p_list','parser.py',38),
  ('list -> tree','list',1,'p_list','parser.py',39),
]
