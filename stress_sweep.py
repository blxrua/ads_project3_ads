"""Random large-instance sweep for v2.exe (the full version).

Generates many M=100, N<=100 sparse graphs (trees, unicyclic, connected
graphs with a given number of extra edges) and reports the slowest run.
"""

import os
import random
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "v2.exe")
rng = random.Random(424242)


def rand_tree(V):
    edges = set()
    for v in range(1, V):
        u = rng.randrange(v)
        edges.add((min(u, v), max(u, v)))
    return edges


def rand_connected(V, E):
    edges = rand_tree(V)
    while len(edges) < E:
        u = rng.randrange(V)
        v = rng.randrange(V)
        if u == v:
            continue
        e = (min(u, v), max(u, v))
        if e in edges:
            continue
        edges.add(e)
    return sorted(edges)


def make_input(edges, prices):
    M = 100
    lines = ["%d %d" % (len(edges), M)]
    for u, v in edges:
        lines.append("%03d %03d" % (u, v))
    for i in range(M):
        lines.append("%03d %d" % (i, prices[i]))
    return ("\n".join(lines) + "\n").encode("ascii")


def main():
    worst = (0.0, "")
    total = 0
    for t in range(60):
        V = rng.randint(50, 100)
        kind = rng.choice(["tree", "unicyclic", "connected"])
        if kind == "tree":
            edges = sorted(rand_tree(V))
        elif kind == "unicyclic":
            edges = rand_connected(V, V) if V <= 100 else rand_connected(V, V)
        else:
            edges = rand_connected(V, 100)
        if len(edges) > 100:
            edges = edges[:100]
        mode = rng.choice(["random", "equal", "twovalues"])
        if mode == "random":
            prices = [rng.randint(1, 1000) for _ in range(100)]
        elif mode == "equal":
            prices = [500] * 100
        else:
            prices = [rng.choice([1, 1000]) for _ in range(100)]
        data = make_input(edges, prices)
        t0 = time.perf_counter()
        p = subprocess.run([EXE], input=data, capture_output=True, timeout=30)
        dt = time.perf_counter() - t0
        if p.returncode != 0:
            raise RuntimeError("v2 failed on case %d" % t)
        total += 1
        if dt > worst[0]:
            worst = (dt, "case %d: %s V=%d E=%d %s prices"
                     % (t, kind, V, len(edges), mode))
        if dt > 2.0:
            print("SLOW:", worst)
    print("ran %d cases, worst %.3f s (%s)" % (total, worst[0], worst[1]))


if __name__ == "__main__":
    main()
