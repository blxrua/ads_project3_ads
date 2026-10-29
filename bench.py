"""
Performance comparison of the five Safe Fruit versions on large sparse graphs.

Every case has M <= 100 fruits and N <= 100 tips (the limits of the problem).
The script regenerates all cases in memory, times each executable and checks
that all five versions agree on (count, total price).

Usage:  python bench.py
"""

import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXES = ["v1.exe", "v2.exe", "v3.exe", "v4.exe", "v5.exe"]
rng = random.Random(20261028)


def make_input(M, edges, prices):
    lines = ["%d %d" % (len(edges), M)]
    for u, v in edges:
        lines.append("%03d %03d" % (u, v))
    for i in range(M):
        lines.append("%03d %d" % (i, prices[i]))
    return ("\n".join(lines) + "\n").encode("ascii")


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


def prices_random(M):
    return [rng.randint(1, 1000) for _ in range(M)]


def prices_equal(M):
    return [500] * M


def build_cases():
    cases = []

    path100 = [(i, i + 1) for i in range(99)]
    cycle100 = [(i, (i + 1) % 100) for i in range(100)]
    star99 = [(0, i) for i in range(1, 100)]
    binary = [((i - 1) // 2, i) for i in range(1, 100)]

    cases.append(("path100  random prices", 100, path100, prices_random(100)))
    cases.append(("path100  equal prices ", 100, path100, prices_equal(100)))
    cases.append(("cycle100 random prices", 100, cycle100, prices_random(100)))
    cases.append(("cycle100 equal prices ", 100, cycle100, prices_equal(100)))
    cases.append(("binom-tree100 random  ", 100, binary, prices_random(100)))
    cases.append(("binom-tree100 equal   ", 100, binary, prices_equal(100)))
    cases.append(("star99   random prices ", 100, star99, prices_random(100)))
    cases.append(("rand tree100           ", 100, sorted(rand_tree(100)),
                  prices_random(100)))

    pairs = [(i, j) for i in range(50) for j in range(i + 1, 50)]
    rng.shuffle(pairs)
    cases.append(("50v, 100e              ", 100, pairs[:100], prices_random(100)))

    for V in [99, 95, 90, 80, 70, 60, 51]:
        cases.append(("V=%-3d E=100 (r=%-2d)   " % (V, 100 - V + 1),
                      100, rand_connected(V, 100), prices_random(100)))
    return cases


def run(exe, data):
    t0 = time.perf_counter()
    p = subprocess.run([os.path.join(HERE, exe)], input=data,
                       capture_output=True, timeout=30)
    dt = time.perf_counter() - t0
    if p.returncode != 0:
        raise RuntimeError("%s exited with %d" % (exe, p.returncode))
    out = p.stdout.decode("ascii", "replace").splitlines()
    return dt, int(out[0]), int(out[2])


def main():
    print("%-24s %s   count  price" %
          ("case", " ".join("%9s" % exe for exe in EXES)))
    for name, M, edges, prices in build_cases():
        data = make_input(M, edges, prices)
        row = []
        answers = set()
        for exe in EXES:
            dt, cnt, price = run(exe, data)
            row.append(dt)
            answers.add((cnt, price))
        if len(answers) != 1:
            print("MISMATCH on %s: %r" % (name, answers))
            sys.exit(1)
        cnt, price = answers.pop()
        print("%-24s %s   %-5d  %d" %
              (name, " ".join("%8.3fs" % t for t in row), cnt, price))
    print("\nAll five versions agree on every case.")


if __name__ == "__main__":
    main()
