from argparse import ArgumentParser
from parser import load_file
import z3printer

# all code here is intended to be executed on import

# set up config parser
parser = ArgumentParser(description="Symbolic Synthesizer")
parser.add_argument('filename', help='SyGuS-formatted input file')
parser.add_argument('-d', '--debug', action='store_true', help='turns on debug output')
parser.add_argument('-b', '--breadth', type=int, default=10)
arguments = parser.parse_args()
# store results in variables we can access after import
DEBUG = arguments.debug
FILENAME = arguments.filename
MAX_BREADTH = arguments.breadth
# setup the z3 printer
z3printer._Formatter.max_depth = 10000
z3printer._Formatter.max_args = 100000
z3printer._Formatter.max_visited = 1000000
z3printer._PP.max_width = 200
z3printer._PP.bounded = False
z3printer._PP.max_lines = 100000000