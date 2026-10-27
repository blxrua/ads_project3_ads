"""Generate the light benchmark set and label every instance with the CP-SAT optimum.

Output:
    bench/instances/<family>/<name>.in
    bench/manifest.json
"""

import json
import os
import random

from oracle import solve

HERE = os.path.dirname(os.path.abspath(__file__))
INST = os.path.join(HERE, "instances")

SIZES = [30, 60, 90, 100]
MODES = ["uniform", "equal", "narrow"]
SEEDS = [0, 1, 2, 3, 4]


def prices(mode, m, rng):
    if mode == "uniform":
        return [rng.randint(1, 1000) for _ in range(m)]
    if mode == "equal":
        return [500] * m
    return [rng.randint(1, 5) for _ in range(m)]


def path_edges(m):
    return [(i, i + 1) for i in range(m - 1)]


def cycle_edges(m):
    return [(i, (i + 1) % m) for i in range(m)]


def star_edges(m):
    return [(0, i) for i in range(1, m)]


def tree_edges(m, rng):
    return [(rng.randrange(v), v) for v in range(1, m)]


def add_random_edges(edges, m, target, rng):
    s = set((min(u, v), max(u, v)) for u, v in edges)
    limit = m * (m - 1) // 2
    target = min(target, limit)
    while len(s) < target:
        u = rng.randrange(m)
        v = rng.randrange(m)
        if u == v:
            continue
        s.add((min(u, v), max(u, v)))
    return sorted(s)


def sparse_edges(m, rng):
    return add_random_edges(tree_edges(m, rng), m, 100, rng)


def components_edges(m):
    """Ten disjoint cycles, as equal in size as possible."""
    k = 10
    edges = set()
    start = 0
    for c in range(k):
        size = m // k + (1 if c < m % k else 0)
        verts = list(range(start, start + size))
        start += size
        if size < 2:
            continue
        for i in range(size):
            u = verts[i]
            v = verts[(i + 1) % size]
            edges.add((min(u, v), max(u, v)))
    return sorted(edges)


FAMILIES = [
    ("path", lambda m, rng: path_edges(m)),
    ("cycle", lambda m, rng: cycle_edges(m)),
    ("star", lambda m, rng: star_edges(m)),
    ("tree", tree_edges),
    ("sparse100", sparse_edges),
    ("components", lambda m, rng: components_edges(m)),
]

EXTRA = [
    ("bipartite", 20,
     lambda rng: [(i, 10 + j) for i in range(10) for j in range(10)]),
    ("isolated", 100, lambda rng: []),
]


def input_text(m, edges, price):
    lines = ["%d %d" % (len(edges), m)]
    for u, v in edges:
        lines.append("%03d %03d" % (u + 1, v + 1))
    for i in range(m):
        lines.append("%03d %d" % (i + 1, price[i]))
    return "\n".join(lines) + "\n"


def make_case(family, m, mode, seed, edge_fn):
    rng = random.Random("%s|%d|%s|%d" % (family, m, mode, seed))
    edges = edge_fn(m, rng)
    price = prices(mode, m, rng)
    name = "%s_m%d_%s_s%d" % (family, m, mode, seed)
    text = input_text(m, edges, price)

    sub = os.path.join(INST, family)
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, name + ".in")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    tips = [(u + 1, v + 1) for u, v in edges]
    fruits = [(i + 1, price[i]) for i in range(m)]
    cnt, total, chosen = solve(tips, fruits)

    return {
        "name": name,
        "family": family,
        "size": m,
        "mode": mode,
        "seed": seed,
        "M": m,
        "E": len(edges),
        "price_sum": sum(price),
        "path": os.path.relpath(path, os.path.dirname(HERE)).replace("\\", "/"),
        "opt_count": cnt,
        "opt_price": total,
    }


def main():
    entries = []

    for family, edge_fn in FAMILIES:
        for m in SIZES:
            for mode in MODES:
                for seed in SEEDS:
                    entries.append(make_case(family, m, mode, seed, edge_fn))
                    print(".", end="", flush=True)
    for family, m, edge_fn in EXTRA:
        for mode in MODES:
            for seed in SEEDS:
                entries.append(make_case(family, m, mode, seed,
                                        lambda _m, rng, fn=edge_fn: fn(rng)))
                print(".", end="", flush=True)

    manifest = {
        "note": "light benchmark set, optimum from CP-SAT oracle",
        "instances": entries,
    }
    with open(os.path.join(HERE, "manifest.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")

    print("\n%d instances" % len(entries))


if __name__ == "__main__":
    main()
