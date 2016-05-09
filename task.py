from scope import Scope, get_sort
from symbols import mapping
from components import *
from formulas import *
from z3 import Solver, unsat, Not, And, Const, IntSort, simplify
from setup import DEBUG, MAX_BREADTH
from pprint import pprint
from variables import *

class Task(object):
	def __init__(self):
		# all the appropriate scopes
		self.functions = Scope()
		self.synth_function = None
		self.variables = Scope()
		self.constraints = []
		self.system = None
	def add_system(self, s):
		self.system = s
	def parse(self, sexpr):
		# now let's process the file
		for cmd, *args in sexpr:
			if cmd == "set-logic":
				self.logic = args[0]
			elif cmd == "define-fun":
				func = Function(*args, self.functions.zoom())
				self.functions[func.name] = func
			elif cmd == "synth-fun":
				if self.synth_function != None:
					raise Exception("We only support a single function")
				self.synth_function = SynthFun(*args, self.functions.zoom())
			elif cmd == "declare-var":
				var = Variable(*args)
				self.variables[var.name] = var
			elif cmd == "constraint":
				self.constraints.append(args[0])
			elif cmd == "check-synth":
				return self.synthesize()
			else:
				pass
	def synthesize(self):
		# let's make some solvers
		#synth_solver = Solver()
		#verify_solver = Solver()
		# get our spec constraint
		scope = self.functions.update(mapping)
		constraint = Constraint(self.constraints, self.synth_function, self.variables, scope)
		# define some search parameters
		if DEBUG:
			print(self.constraints)
			print(constraint.constraints)
			print(constraint.input)
			input("Hit enter to start synthesis")
		breadth = 1
		while breadth < MAX_BREADTH:
			components = {}
			# create components based on breadth:
			for component in self.synth_function.components:
				for b in range(breadth):
					comp_id = "{}.{}".format(component._id, b)
					components[comp_id] = component
			if DEBUG: 
				print("Starting synthesis with breadth {}...".format(breadth))
				print("Components map:")
				pprint(components)
			# now actually synthesize
			solution = self.synthesize_with_components(components, constraint, self.system)
			if solution:
				if DEBUG: print("Found solution.")
				return self.extract_program(solution, components)
			else:
				if DEBUG: print("No solution at that size.")
				breadth += 1
	def synthesize_with_components(self, components, constraint, system):
		# components maps unique comp_ids to component objects
		# not one-to-one, but def. onto
		# step 0: some useful values
		card_I, N = len(self.synth_function.parameters), len(components)
		# step 1: make some solvers
		synth_solver = Solver()
		verify_solver = Solver()
		# step 2: initialize examples
		S = []
		# step 2b: create location variables and location constraints
		initial_constraints = []
		L = create_location_variables(components)
		if system:
			patterns = create_pattern_constraint(L, components, system)
			if DEBUG:
				print("PATTERNS")
				print(patterns.sexpr())
			initial_constraints.append(patterns)
		wfp = create_wfp_constraint(L, N)
		initial_constraints.append(wfp)
		# step 3: looooooooop
		while True:
			# step 4: assert L constraint
			synth_solver.assert_exprs(*initial_constraints)
			# step 5: start the looooop
			for i, X in enumerate(S):
				I, O, T = [], [], []
				for w in range(constraint.width):
					# step 6: create I, O, T for synth at width i
					I_w = create_input_variables(self.synth_function.parameters, i, w)
					O_w = create_output_variables(self.synth_function.output, i, w)
					T_w = create_temp_variables(components, i, w)
					# step 7: assert library and connection constraints
					lib = create_lib_constraint(T_w, I_w, components)
					# for conn constraint, need map from component_id to l value
					locations = create_location_map(O_w, T_w, L, N)
					conn = create_conn_constraint(O_w, T_w, locations)
					synth_solver.assert_exprs(lib, conn)
					I += I_w
					O += O_w
					T += T_w
				# step 8: once we've got all the I, O, we can assert the spec constraint
				conn_spec, spec = create_spec_constraint(I, O, X, constraint)
				synth_solver.assert_exprs(conn_spec, spec)
			# get a model, or just bail
			if synth_solver.check() == unsat:
				if DEBUG: print("Failed to find a model.")
				return None
			model = synth_solver.model()
			curr_l = [l._replace(value=model[l.value]) for l in L]

			# step 9: need to verify the model we just found, so we'll construct verificatio constraint
			I, O, T = [], [], []
			for w in range(constraint.width):
				# same as above, but we only have a single example
				I_w = create_input_variables(self.synth_function.parameters, 0, w)
				O_w = create_output_variables(self.synth_function.output, 0, w)
				T_w = create_temp_variables(components, 0, w)
				lib = create_lib_constraint(T_w, I_w, components)
				locations = create_location_map(O_w, T_w, curr_l, N)
				conn = create_conn_constraint(O_w, T_w, locations)
				verify_solver.assert_exprs(lib, conn)
				I += I_w
				O += O_w
				T += T_w
			# now we need to create variables for X so we can check our spec
			X = create_spec_variables(constraint, self.variables)
			conn_spec, spec = create_spec_constraint(I, O, X, constraint)
			verify_solver.assert_exprs(conn_spec, Not(spec))
			# now we'll try and get a model of our exectution
			if verify_solver.check() == unsat:
				return curr_l
			model = verify_solver.model()
			example = [x._replace(value=model[x.value]) for x in X]
			S.append(example)
			if DEBUG:
				print("Found bad solution: ", [l.value.sexpr() for l in curr_l])
			# clear synthesizers and start anew
			synth_solver.reset()
			verify_solver.reset()
		return None
	def extract_program(self, L, components):
		N = len(components)
		# we need to work our way back through the program, all the way to the params
		worklist = [N - 1]
		components_used = []
		# pick up all the components used, and in which order
		while worklist:
			cur = worklist.pop()
			source = [l for l in L if l.value.as_long() == cur and l.type == "return"][0]
			for p, s in components[source.component].parameters:
				k = [l for l in L if l.component == source.component and l.parameter == p][0]
				worklist.append(k.value.as_long())
			components_used.append(components[source.component])
		left = []
		while components_used:
			cur = components_used.pop()
			if isinstance(cur, Component):
				arity = len(cur.parameters)
				args = {}
				for i in range(arity):
					args["PARAM.{}".format(i)] = left.pop()
				left.append(cur.eval_as_sexpr(args))
			else:
				left.append(cur)
		return ['define-fun', self.synth_function.name, self.synth_function.parameters, left[0]]

	