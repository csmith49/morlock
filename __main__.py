from time import clock
from pprint import pprint
from setup import DEBUG, FILENAME, load_file
from task import Task

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
	t = Task(task)
	# main loop
	while True:
		break

	# display total time
	print("Ran for {} seconds".format(clock() - start_time))