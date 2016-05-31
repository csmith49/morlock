import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os
import glob

sns.set_style('darkgrid')

LOG = "./logs/peano.logs"

def hull(X, Y):
    last_y = None
    out_x, out_y = [], []
    for x, y in zip(X, Y):
        if y != last_y:
            out_x.append(x)
            out_y.append(y)
        last_y = y
    return out_x, out_y

def extract_tag(tag, file):
    output = []
    with open(file, 'r') as f:
        for line in f:
            if line.startswith(tag):
                l = line.split(",")
                output.append([float(v) for v in l[1:]])
    return output

for tag in ["bottom", "normalized-bottom"]:
    data = extract_tag(tag, LOG)
    counts, size, time = zip(*data)
    t, s = hull(time, size)
    plt.plot(t, s, label=tag)

for tag in ["top", "normalized-top"]:
    data = extract_tag(tag, LOG)
    counts, size, frontier, time = zip(*data)
    t, s = hull(time, size)
    plt.plot(t, s, label=tag)

plt.xscale('log')
plt.legend(loc="upper left")
plt.show()
