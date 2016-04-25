from scope import Scope, get_sort
from symbols import mapping
from components import *
from formulas import *
from z3 import Solver, unsat, Not, And, Const, IntSort
from setup import DEBUG, MAX_BREADTH
from pprint import pprint
from variables import *

class Task(object):
	def __init__(self, sexpr):
		# all the appropriate scopes
		self.functions = Scope()
		self.synth_function = None
		self.variables = Scope()
		self.constraints = []
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
				self.synthesize()
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
			solution = self.synthesize_with_components(components, constraint)
			if solution:
				if DEBUG: print("Found solution.")
				return solution
			else:
				if DEBUG: print("No solution at that size.")
				breadth += 1
	def synthesize_with_components(self, components, constraint):
		# components maps unique comp_ids to component objects
		# not one-to-one, but def. onto
		# step 1: make some solvers
		synth_solver = Solver()
		verify_solver = Solver()
		# step 2: initialize examples
		S = []
		# step 3: looooooooop
		while True:
			if DEBUG: print("Looking for a model...")
			# step 4: create location variables off component list
			L = create_location_variables(components)
			# step 5: assert wfp constraint
			wfp = create_wfp_constraint(L, len(self.synth_function.parameters), len(components))
			synth_solver.assert_exprs(wfp)
			if DEBUG:
				print("WFP:")
				print(wfp.sexpr())
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
					locations = create_location_map(I_w, O_w, T_w, L)
					conn = create_conn_constraint(I_w, O_w, T_w, locations)
					synth_solver.assert_exprs(lib, conn)
					if DEBUG:
						print("LIB:")
						print(lib.sexpr())
						print("CONN:")
						print(conn.sexpr())
					I += I_w
					O += O_w
					T += T_w
				# step 8: once we've got all the I, O, we can assert the spec constraint
				spec = create_spec_constraint(I, O, X, constraint)
				if DEBUG:
					print("SPEC:")
					print(spec.sexpr())
				synth_solver.assert_exprs(spec)
			# get a model, or just bail
			if synth_solver.check() == unsat:
				if DEBUG: print("Failed to find a model.")
				return None
			model = synth_solver.model()
			curr_l = [l._replace(value=model[l.value]) for l in L]
			if DEBUG:
				print("Found model:")
				for l in curr_l:
					print(l.value.sexpr())
			# step 9: need to verify the model we just found, so we'll construct verificatio constraint
			I, O, T = [], [], []
			for w in range(constraint.width):
				# same as above, but we only have a single example
				I_w = create_input_variables(self.synth_function.parameters, 0, w)
				O_w = create_output_variables(self.synth_function.output, 0, w)
				T_w = create_temp_variables(components, 0, w)
				lib = create_lib_constraint(T_w, I_w, components)
				locations = create_location_map(I_w, O_w, T_w, curr_l)
				conn = create_conn_constraint(I_w, O_w, T_w, locations)
				verify_solver.assert_exprs(lib, conn)
				I += I_w
				O += O_w
				T += T_w
			# now we need to create variables for X so we can check our spec
			X = create_spec_variables(constraint, self.variables)
			spec = create_spec_constraint(I, O, X, constraint)
			verify_solver.assert_exprs(Not(spec))
			# now we'll try and get a model of our exectution
			if verify_solver.check() == unsat:
				if DEBUG: print("Found a solution!")
				return curr_l
			model = verify_solver.model()
			example = [x._replace(value=model[x.value]) for x in X]
			if DEBUG:
				print("Found counter-example:")
				for x in example:
					print(x.value.sexpr())
			S.append(X)
			# clear synthesizers and start anew
			synth_solver.reset()
			verify_solver.reset()

		return None
	