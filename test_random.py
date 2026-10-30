"""
Differential tester for the eight Safe Fruit versions.

For every generated case:
  * brute force (enumerate all subsets) computes the optimal (count, price);
  * each version is run and its output is validated:
      - IDs sorted / unique / in basket;
      - selected IDs form an independent set;
      - reported count / total price match the brute-force optimum.

Usage:  python test_random.py
(the eight .exe files must be in the same directory)
"""

import os
import random
import subprocess
import sys

EXES = ["v1.exe", "v2.exe", "v3.exe", "v4.exe", "v5.exe", "v6.exe", "v7.exe", "v8.exe"]
HERE = os.path.dirname(os.path.abspath(__file__))


def build_input(M, ids, prices, edges):
    """edges: list of (u, v) internal indices."""
    tip_ids = [(ids[u], ids[v]) for (u, v) in edges]
    lines = ["%d %d" % (len(tip_ids), M)]
    for a, b in tip_ids:
        lines.append("%03d %03d" % (a, b))
    for i in range(M):
        lines.append("%03d %d" % (ids[i], prices[i]))
    return "\n".join(lines) + "\n"


def gen_case(rng, max_m):
    M = rng.randint(1, max_m)
    ids = rng.sample(range(0, 1000), M)
    prices = [rng.randint(1, 1000) for _ in range(M)]

    all_pairs = [(i, j) for i in range(M) for j in range(i + 1, M)]
    rng.shuffle(all_pairs)
    limit = min(len(all_pairs), rng.choice([0, 1, 2, 3, 4, 6, 8, 10]))
    N = rng.randint(0, limit)
    used = all_pairs[:N]

    text = build_input(M, ids, prices, used)

    # Occasionally append a tip referring to a fruit outside the basket.
    if rng.random() < 0.35:
        outside = rng.choice([x for x in range(1000) if x not in set(ids)])
        i = rng.randrange(M)
        lines = text.splitlines()
        lines[0] = "%d %d" % (len(used) + 1, M)
        lines.insert(1 + len(used), "%03d %03d" % (ids[i], outside))
        text = "\n".join(lines) + "\n"

    return text, M, ids, prices, used


def brute(M, prices, edges):
    best_key = None
    best = (0, 0)
    for mask in range(1 << M):
        ok = True
        for u, v in edges:
            if ((mask >> u) & 1) and ((mask >> v) & 1):
                ok = False
                break
        if not ok:
            continue
        cnt = bin(mask).count("1")
        price = sum(prices[i] for i in range(M) if (mask >> i) & 1)
        key = (cnt, -price)
        if best_key is None or key > best_key:
            best_key = key
            best = (cnt, price)
    return best


def run(exe, inp):
    p = subprocess.run(
        [os.path.join(HERE, exe)],
        input=inp,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if p.returncode != 0:
        raise RuntimeError("%s exited with %d, stderr=%s"
                           % (exe, p.returncode, p.stderr))
    return p.stdout


def check(out, M, ids, prices, edges):
    lines = out.strip("\n").split("\n")
    if len(lines) < 3:
        raise AssertionError("fewer than 3 output lines: %r" % out)

    cnt = int(lines[0].strip())
    tokens = lines[1].split()
    if len(tokens) != cnt:
        raise AssertionError("count line says %d but %d ids listed"
                             % (cnt, len(tokens)))

    sel = [int(t) for t in tokens]
    if sel != sorted(sel):
        raise AssertionError("ids not in increasing order: %r" % sel)
    if len(set(sel)) != len(sel):
        raise AssertionError("duplicate ids selected")

    id2i = {ids[i]: i for i in range(M)}
    mask = 0
    for x in sel:
        if x not in id2i:
            raise AssertionError("id %03d is not in the basket" % x)
        mask |= 1 << id2i[x]
    for u, v in edges:
        if ((mask >> u) & 1) and ((mask >> v) & 1):
            raise AssertionError("conflicting pair selected: %03d %03d"
                                 % (ids[u], ids[v]))

    total = int(lines[2].strip())
    expect = sum(prices[id2i[x]] for x in sel)
    if total != expect:
        raise AssertionError("total price %d, expected %d" % (total, expect))
    return cnt, total


def run_case(text, M, ids, prices, edges, label):
    opt = brute(M, prices, edges)
    results = {}
    for exe in EXES:
        got = check(run(exe, text), M, ids, prices, edges)
        if got != opt:
            raise AssertionError(
                "%s: got (count, price)=%r, optimum=%r\ninput:\n%s"
                % (label, got, opt, text))
        results[exe] = got
    return results


def main():
    rng = random.Random(20261028)

    fixed = [
        # (M, ids, prices, edges)
        (1, [7], [500], []),
        (6, [10, 20, 30, 40, 50, 60], [1, 2, 3, 4, 5, 6],
         [(i, j) for i in range(6) for j in range(i + 1, 6)]),          # K6
        (8, list(range(1, 9)), [9, 8, 7, 6, 5, 4, 3, 2],
         [(i, (i + 1) % 8) for i in range(8)]),                         # C8
        (7, list(range(10, 17)), [100, 1, 100, 1, 100, 1, 100],
         [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]),             # path P7
        (5, list(range(100, 105)), [3, 4, 5, 6, 7], []),                # no conflicts
    ]
    total = 0

    for idx, (M, ids, prices, edges) in enumerate(fixed):
        text = build_input(M, ids, prices, edges)
        run_case(text, M, ids, prices, edges, "fixed#%d" % idx)
        total += 1

    rounds = 220
    for t in range(rounds):
        max_m = rng.choice([6, 8, 10, 11, 12])
        text, M, ids, prices, edges = gen_case(rng, max_m)
        run_case(text, M, ids, prices, edges, "random#%d" % t)
        total += 1
        if (t + 1) % 20 == 0:
            print("  ... %d/%d random cases ok" % (t + 1, rounds))
            sys.stdout.flush()

    print("ALL PASS: %d cases, %d executables each." % (total, len(EXES)))


if __name__ == "__main__":
    main()
