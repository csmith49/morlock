from time import clock
from pprint import pprint
from setup import DEBUG, FILENAME, load_file, EQ_FILENAME
from task import Task
from equations import System

if __name__ == "__main__":
	# record starting time for bm purposes
	start_time = clock()
	# load data and run through sexpr parser
	task = load_file(FILENAME)[0]
	if DEBUG:
		print("FILE ------------------>")
		pprint(task)
	# now we need to process the file to define our search space and stuff
	# set number of copies of each component to use
	breadth = 1
	# we'll be using two solvers
	t = Task()
	if EQ_FILENAME:
		system = load_file(EQ_FILENAME)[0]
		s = System(system)
		t.add_system(s)
	# get a solution
	pprint(t.parse(task))
	print("Ran for {} seconds".format(clock() - start_time))