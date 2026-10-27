"""Generate benchmark suites and label every instance with the SCIP optimum.

Suites
    light : the original 390-instance set (canonical families, aligned labels).
    full  : 10 sizes x 10 seeds x 3 price modes x (6 canonical + 4 mechanism
            families), plus the two extras, with every instance's IDs, fruit
            lines and tip lines shuffled.  The full suite is meant to show
            behaviour on less idealised graph shapes and on arbitrary labels.

Output
    bench/instances/<family>/<name>.in          light
    bench/manifest.json
    bench/instances_full/<family>/<name>.in     full
    bench/manifest_full.json

The light generator is unchanged: re-running it must reproduce the committed
files byte for byte.
"""

import json
import math
import os
import random

from oracle import solve

HERE = os.path.dirname(os.path.abspath(__file__))
INST = os.path.join(HERE, "instances")
INST_FULL = os.path.join(HERE, "instances_full")
ROOT = os.path.dirname(HERE)

SIZES = [30, 60, 90, 100]
FULL_SIZES = list(range(10, 101, 10))
MECH_SIZES = [20, 40, 60, 80, 100]
MODES = ["uniform", "equal", "narrow"]
SEEDS = [0, 1, 2, 3, 4]
FULL_SEEDS = list(range(10))


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


# ---------------------------------------------------------------------------
# Mechanism generators.  All cap the edge count at `budget` (<= 100).
# ---------------------------------------------------------------------------

def _add_group(edges, verts, target, rng):
    pairs = [(verts[i], verts[j])
             for i in range(len(verts)) for j in range(i + 1, len(verts))]
    rng.shuffle(pairs)
    for u, v in pairs:
        if len(edges) >= target:
            break
        edges.add((min(u, v), max(u, v)))


def groups_edges(m, rng, budget=100):
    """Overlapping cliques ("forbidden groups"): a few small dense groups."""
    edges = set()
    target = min(budget, m * (m - 1) // 2)
    for _ in range(60):
        if len(edges) >= target:
            break
        size = rng.randint(3, min(10, m))
        verts = rng.sample(range(m), size)
        _add_group(edges, verts, target, rng)
    return sorted(edges)


def _fill_random(edges, m, target, rng):
    while len(edges) < target:
        u = rng.randrange(m)
        v = rng.randrange(m)
        if u != v:
            edges.add((min(u, v), max(u, v)))


def _take(cands, quota, chosen, target, rng):
    rng.shuffle(cands)
    for e in cands:
        if len(chosen) >= target or quota <= 0:
            break
        if e not in chosen:
            chosen.add(e)
            quota -= 1


def sbm_edges(m, rng, budget=100):
    """Two-level communities: dense leaves, medium parent, sparse cross links."""
    target = min(budget, m * (m - 1) // 2)
    nsuper = 2 if m >= 8 else 1
    for _ in range(20):
        super_of = [rng.randrange(nsuper) for _ in range(m)]
        counts = [super_of.count(s) for s in range(nsuper)]
        if min(counts) >= 2 or m < 4:
            break

    leaf_of = [0] * m
    for s in range(nsuper):
        verts = [v for v in range(m) if super_of[v] == s]
        rng.shuffle(verts)
        leaves = rng.randint(2, 3)
        for i, v in enumerate(verts):
            leaf_of[v] = s * 10 + (i % leaves)

    leaf, mid, cross = [], [], []
    for u in range(m):
        for v in range(u + 1, m):
            e = (u, v)
            if leaf_of[u] == leaf_of[v]:
                leaf.append(e)
            elif super_of[u] == super_of[v]:
                mid.append(e)
            else:
                cross.append(e)

    chosen = set()
    q_leaf = int(round(0.70 * target))
    q_mid = int(round(0.20 * target))
    _take(leaf, q_leaf, chosen, target, rng)
    _take(mid, q_mid, chosen, target, rng)
    _take(cross, target - len(chosen), chosen, target, rng)
    if len(chosen) < target:
        rest = leaf + mid + cross
        rng.shuffle(rest)
        for e in rest:
            if len(chosen) >= target:
                break
            chosen.add(e)
    return sorted(chosen)


def coreper_edges(m, rng, budget=100):
    """A small dense core, every other vertex attached to 1-3 core vertices."""
    target = min(budget, m * (m - 1) // 2)
    c = max(3, min(10, m // 4))
    core = sorted(rng.sample(range(m), c))
    edges = set()
    for i, u in enumerate(core):
        for v in core[i + 1:]:
            edges.add((u, v))
    for v in range(m):
        if v in core:
            continue
        k = rng.randint(1, min(3, c))
        for u in rng.sample(core, k):
            if len(edges) >= target:
                break
            edges.add((min(u, v), max(u, v)))
    _fill_random(edges, m, target, rng)
    return sorted(edges)


def banded_edges(m, rng, budget=100):
    """Nearest-neighbour band first, then a few long-range shortcuts."""
    target = min(budget, m * (m - 1) // 2)
    edges = set()
    for d in range(1, m):
        for i in range(m - d):
            if len(edges) >= target:
                break
            edges.add((i, i + d))
        if len(edges) >= target:
            break
    _fill_random(edges, m, target, rng)
    return sorted(edges)


FAMILIES = [
    ("path", lambda m, rng: path_edges(m)),
    ("cycle", lambda m, rng: cycle_edges(m)),
    ("star", lambda m, rng: star_edges(m)),
    ("tree", tree_edges),
    ("sparse100", sparse_edges),
    ("components", lambda m, rng: components_edges(m)),
]

MECH_FAMILIES = [
    ("groups", groups_edges),
    ("sbm", sbm_edges),
    ("coreper", coreper_edges),
    ("banded", banded_edges),
]

EXTRA = [
    ("bipartite", 20,
     lambda rng: [(i, 10 + j) for i in range(10) for j in range(10)]),
    ("isolated", 100, lambda rng: []),
]


# ---------------------------------------------------------------------------
# Input layout and graph features
# ---------------------------------------------------------------------------

def prepare(m, edges, price, rng, shuffle):
    """Return (tips, fruit_lines), optionally with permuted IDs and order.

    fruit_lines is a list of (public_id, price, original_vertex).  The line
    order is also the vertex index order the solver sees.
    """
    if not shuffle:
        tips = [(u + 1, v + 1) for u, v in edges]
        lines = [(i + 1, price[i], i) for i in range(m)]
        return tips, lines

    perm = list(range(m))
    rng.shuffle(perm)
    tips = [(perm[u] + 1, perm[v] + 1) for u, v in edges]
    rng.shuffle(tips)
    tips = [(a, b) if rng.random() < 0.5 else (b, a) for a, b in tips]
    lines = [(perm[v] + 1, price[v], v) for v in range(m)]
    rng.shuffle(lines)
    return tips, lines


def input_text(m, tips, lines):
    out = ["%d %d" % (len(tips), m)]
    for a, b in tips:
        out.append("%03d %03d" % (a, b))
    for vid, p, _ in lines:
        out.append("%03d %d" % (vid, p))
    return "\n".join(out) + "\n"


def _corr(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / math.sqrt(vx * vy)


def graph_features(m, edges, price, line_order):
    adj = [[] for _ in range(m)]
    deg = [0] * m
    eset = set()
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
        deg[u] += 1
        deg[v] += 1
        eset.add((min(u, v), max(u, v)))

    seen = [False] * m
    comps = []
    for s in range(m):
        if seen[s]:
            continue
        seen[s] = True
        stack = [s]
        size = 0
        while stack:
            v = stack.pop()
            size += 1
            for w in adj[v]:
                if not seen[w]:
                    seen[w] = True
                    stack.append(w)
        comps.append(size)

    clus = 0.0
    nclus = 0
    for v in range(m):
        d = deg[v]
        if d < 2:
            continue
        links = 0
        nb = adj[v]
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                a, b = nb[i], nb[j]
                if (a, b) in eset or (b, a) in eset:
                    links += 1
        clus += 2.0 * links / (d * (d - 1))
        nclus += 1

    positions = list(range(m))
    pos_deg = [deg[v] for v in line_order]
    pos_price = [price[v] for v in line_order]
    return {
        "max_deg": max(deg) if deg else 0,
        "mean_deg": round(2.0 * len(edges) / m, 4) if m else 0.0,
        "components": len(comps),
        "largest_comp": max(comps) if comps else 0,
        "clustering": round(clus / nclus, 4) if nclus else 0.0,
        "cyclomatic": len(edges) - m + len(comps),
        "label_deg_corr": round(_corr(positions, pos_deg), 4),
        "price_deg_corr": round(_corr(pos_price, pos_deg), 4),
    }


def make_case(family, m, mode, seed, edge_fn, inst_root, shuffle,
              suite, layout, with_features):
    rng = random.Random("%s|%d|%s|%d" % (family, m, mode, seed))
    edges = edge_fn(m, rng)
    price = prices(mode, m, rng)
    tips, lines = prepare(m, edges, price, rng, shuffle)

    name = "%s_m%d_%s_s%d" % (family, m, mode, seed)
    sub = os.path.join(inst_root, family)
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, name + ".in")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(input_text(m, tips, lines))

    fruits = [(vid, p) for vid, p, _ in lines]
    cnt, total, chosen = solve(tips, fruits)

    entry = {
        "name": name,
        "family": family,
        "size": m,
        "mode": mode,
        "seed": seed,
        "M": m,
        "E": len(edges),
        "price_sum": sum(price),
        "path": os.path.relpath(path, ROOT).replace("\\", "/"),
        "opt_count": cnt,
        "opt_price": total,
        "suite": suite,
        "layout": layout,
    }
    if with_features:
        entry["features"] = graph_features(m, edges, price,
                                           [old for _, _, old in lines])
    return entry


def _emit(entries, family, sizes, seeds, edge_fn, inst_root):
    for m in sizes:
        for mode in MODES:
            for seed in seeds:
                entries.append(make_case(
                    family, m, mode, seed, edge_fn, inst_root,
                    True, "full", "shuffled", True))
                if len(entries) % 50 == 0:
                    print("  %d" % len(entries), flush=True)


def gen_light():
    entries = []
    for family, edge_fn in FAMILIES:
        for m in SIZES:
            for mode in MODES:
                for seed in SEEDS:
                    entries.append(make_case(
                        family, m, mode, seed, edge_fn, INST,
                        False, "light", "aligned", False))
                    print(".", end="", flush=True)
    for family, m, edge_fn in EXTRA:
        for mode in MODES:
            for seed in SEEDS:
                entries.append(make_case(
                    family, m, mode, seed,
                    lambda _m, rng, fn=edge_fn: fn(rng), INST,
                    False, "light", "aligned", False))
                print(".", end="", flush=True)

    manifest = {
        "note": "light benchmark set, optimum from SCIP oracle (zero gap)",
        "instances": entries,
    }
    with open(os.path.join(HERE, "manifest.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print("\n%d instances" % len(entries))


def gen_full():
    entries = []
    print("canonical families ...")
    for family, edge_fn in FAMILIES:
        _emit(entries, family, FULL_SIZES, FULL_SEEDS, edge_fn, INST_FULL)
    print("mechanism families ...")
    for family, edge_fn in MECH_FAMILIES:
        _emit(entries, family, MECH_SIZES, FULL_SEEDS, edge_fn, INST_FULL)
    print("extras ...")
    for family, m, edge_fn in EXTRA:
        for mode in MODES:
            for seed in FULL_SEEDS:
                entries.append(make_case(
                    family, m, mode, seed,
                    lambda _m, rng, fn=edge_fn: fn(rng), INST_FULL,
                    True, "full", "shuffled", True))

    manifest = {
        "note": ("full generator suite: canonical + mechanism families, "
                 "shuffled IDs/line order, SCIP optimum (zero gap)"),
        "instances": entries,
    }
    with open(os.path.join(HERE, "manifest_full.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print("%d instances" % len(entries))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["light", "full"], default="light")
    args = ap.parse_args()
    if args.suite == "light":
        gen_light()
    else:
        gen_full()


if __name__ == "__main__":
    main()
