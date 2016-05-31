import argparse
from parser import parse
from nodes import *
from grammars import Grammar
from system import System, Completion 
from iteration import bottom_up, top_down, metric, normalized_bottom_up, normalized_top_down
import logging

parser = argparse.ArgumentParser(description="Benchmarking script for normalization")
parser.add_argument("config", help="config file in .cfg format")
parser.add_argument("output", help="location for output file")
parser.add_argument("--max", type=int, default=10, help="depth to iterate to")
args = parser.parse_args()

logging.basicConfig(format="%(message)s",filename=args.output,level=logging.INFO)

print("Loading files...")
grammar = Grammar(args.config)
equations = Completion(args.config)

print("Top-down iteration...")
for term in top_down(grammar, metric):
    pass

print("Bottom-up iteration...")
for term in bottom_up(grammar):
    pass

print("Normalized top-down iteration...")
for term in normalized_top_down(grammar, metric, equations):
    pass

print("Normalized bottom-up iteration...")
for term in normalized_bottom_up(grammar, equations):
    pass
