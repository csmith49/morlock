import time
import logging
from nodes import *
import heapq
from pprint import pprint as fancy

# top-down frontier-based expansion of the grammar
# follows a metric, guaranteed to produce in increasing order
# ala "type and example directed synthesis"
def top_down(grammar, metric):
    frontier = [ (metric(grammar.start), grammar.start) ]
    count = 0
    start = time.time()
    while frontier:
        w, cur = heapq.heappop(frontier)
        kids = grammar.refine(cur)
        if kids:
            for k in kids:
                heapq.heappush(frontier, (metric(k), k))
        else:
            count += 1
            logging.info("topdown-count-size-frontier-time,{},{},{},{}".format(
                count, size(cur), len(frontier), time.time() - start))
            if time.time() - start > 300:
                raise StopIteration
            yield cur

def normalized_top_down(grammar, metric, completion):
    frontier = [ (metric(grammar.start), grammar.start) ]
    count = 0
    start = time.time()
    while frontier:
        w, cur = heapq.heappop(frontier)
        kids = grammar.refine(cur)
        if kids:
            for k in kids:
                if completion.is_normal(k):
                    heapq.heappush(frontier, (metric(k), k))
        else:
            count += 1
            logging.info("normalized-topdown-count-size-frontier-time,{},{},{},{}".format(
                count, size(cur), len(frontier), time.time() - start))
            if time.time() - start > 300:
                raise StopIteration
            yield cur
# bottom-up expansion
# ala escher
def bottom_up(grammar):
    combiners = []
    count = 0
    start = time.time()
    # we store combination rules as a tuple:
    # for each rule N -> R
    # 1. term - R, has vars so we can construct sub
    # 2. nonterminal - N
    # 3. nonterminals in R, so we can sub appropriately
    # 4. weight - so we can produce smallest first
    for non in grammar.nonterminals:
        for rule in grammar.rules[non]:
            term, nonterms = grammar.convert_to_vars(rule)
            weight = size(term) - len(nonterms)
            combiners.append( (term, non, nonterms, weight) )
    # stores expansions in dictionary
    # expansions in form (term, weight)
    subterms = {n : [] for n in grammar.nonterminals}
    current_size = 1
    while True:
        # we iterate over every combination rule, trying to find combos
        # we want new terms with size equal to current size
        # any we find that go in subterms[start] get yielded
        for term, non, nonterms, weight in combiners:
            # temp solutions stored as (budget, [terms])
            term_tuples = [(current_size - weight, [])]
            answer_len = 0
            while answer_len < len(nonterms):
                new_tuples = []
                for budget, answer in term_tuples:
                    # construct new
                    for t, w in subterms[nonterms[answer_len]]:
                        if w <= budget:
                            new_tuples.append( (budget - w, answer + [t]) )
                term_tuples = new_tuples
                answer_len += 1
            # now that we've found all the subs, apply them and add
            for sub in [dict(enumerate(p)) for budget, p in term_tuples if budget == 0]:
                new_term = apply_sub(term, sub)
                subterms[non].append( (new_term, current_size) )
                if non == grammar.start.val:
                    count += 1
                    logging.info("bottomup-count-size-time,{},{},{}".format(
                        count, current_size, time.time() - start))
                    if time.time() - start > 300:
                        raise StopIteration
                    yield new_term
        # we've found all we can, so lets try one larger
        current_size += 1
        
def normalized_bottom_up(grammar, completion):
    combiners = []
    count = 0
    start = time.time()
    # we store combination rules as a tuple:
    # for each rule N -> R
    # 1. term - R, has vars so we can construct sub
    # 2. nonterminal - N
    # 3. nonterminals in R, so we can sub appropriately
    # 4. weight - so we can produce smallest first
    for non in grammar.nonterminals:
        for rule in grammar.rules[non]:
            term, nonterms = grammar.convert_to_vars(rule)
            weight = size(term) - len(nonterms)
            combiners.append( (term, non, nonterms, weight) )    
    # stores expansions in dictionary
    # expansions in form (term, weight)
    subterms = {n : [] for n in grammar.nonterminals}
    current_size = 1
    while True:
        # we iterate over every combination rule, trying to find combos
        # we want new terms with size equal to current size
        # any we find that go in subterms[start] get yielded
        for term, non, nonterms, weight in combiners:
            # temp solutions stored as (budget, [terms])
            term_tuples = [(current_size - weight, [])]
            answer_len = 0
            while answer_len < len(nonterms):
                new_tuples = []
                for budget, answer in term_tuples:
                    # construct new
                    for t, w in subterms[nonterms[answer_len]]:
                        if w <= budget:
                            new_tuples.append( (budget - w, answer + [t]) )
                term_tuples = new_tuples
                answer_len += 1
            # now that we've found all the subs, apply them and add
            for sub in [dict(enumerate(p)) for budget, p in term_tuples if budget == 0]:
                new_term = apply_sub(term, sub)
                if completion.root_normal(new_term):
                    subterms[non].append( (new_term, current_size) )
                    if non == grammar.start.val:
                        count += 1
                        logging.info("normalized-bottomup-count-size-time,{},{},{}".format(
                            count, current_size, time.time() - start))
                        if time.time() - start > 300:
                            raise StopIteration
                        yield new_term
        # we've found all we can, so lets try one larger
        current_size += 1
    
def metric(node):
    count = getattr(metric, "count")
    output = (size(node), count)
    setattr(metric, "count", count + 1)
    return output
setattr(metric, "count", 0)
