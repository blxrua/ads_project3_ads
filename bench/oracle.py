"""SCIP oracle for Safe Fruit.

Maximize  sum((BIGW - price[i]) * x[i])  subject to x[u] + x[v] <= 1.
BIGW is larger than the maximum possible total price, so the objective
is lexicographic: more fruits first, then lower total price.

Usage:
    py -3.12 bench/oracle.py case.in          # print "count price"
    py -3.12 bench/oracle.py --unique case.in # also check solution uniqueness
"""

import sys

BIGW = 100001


def parse(path):
    with open(path, "r", encoding="utf-8") as f:
        tokens = f.read().split()
    it = iter(tokens)
    n = int(next(it))
    m = int(next(it))
    tips = [(int(next(it)), int(next(it))) for _ in range(n)]
    fruits = [(int(next(it)), int(next(it))) for _ in range(m)]
    return tips, fruits


def build(tips, fruits):
    ids = [f[0] for f in fruits]
    price = {v: p for v, p in fruits}
    pos = {v: i for i, v in enumerate(ids)}
    edges = set()
    for a, b in tips:
        if a in pos and b in pos and a != b:
            u, v = pos[a], pos[b]
            edges.add((min(u, v), max(u, v)))
    return ids, price, pos, sorted(edges)


def solve(tips, fruits, time_limit=10.0, forbid=None):
    """Return (count, total_price, chosen_ids).  forbid is a list of ids."""
    from ortools.linear_solver import pywraplp

    ids, price, pos, edges = build(tips, fruits)
    m = len(ids)

    solver = pywraplp.Solver.CreateSolver("SCIP")
    x = [solver.BoolVar("x%d" % i) for i in range(m)]
    for u, v in edges:
        solver.Add(x[u] + x[v] <= 1)

    if forbid:
        forbid_mask = [i for i, v in enumerate(ids) if v in set(forbid)]
        solver.Add(solver.Sum(x[i] for i in forbid_mask) <= len(forbid_mask) - 1)

    solver.Maximize(solver.Sum((BIGW - price[ids[i]]) * x[i] for i in range(m)))
    # SCIP's default relative gap (1e-4) is too coarse here: the objective is
    # ~1e6 and a difference of a few price units is inside the tolerance.
    solver.SetSolverSpecificParametersAsString(
        "limits/gap = 0.0\nlimits/absgap = 0")
    solver.SetTimeLimit(int(time_limit * 1000))
    status = solver.Solve()
    if status == pywraplp.Solver.INFEASIBLE and forbid:
        return -1, -1, []
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError("oracle status: %d" % status)

    chosen = [ids[i] for i in range(m) if x[i].solution_value() > 0.5]
    count = len(chosen)
    total = sum(price[v] for v in chosen)
    return count, total, chosen


def main():
    args = sys.argv[1:]
    unique = False
    if args and args[0] == "--unique":
        unique = True
        args = args[1:]
    if len(args) != 1:
        print("usage: oracle.py [--unique] case.in", file=sys.stderr)
        return 2

    tips, fruits = parse(args[0])
    count, total, chosen = solve(tips, fruits)
    print(count, total)
    if unique:
        count2, total2, _ = solve(tips, fruits, forbid=chosen)
        print("unique" if (count2, total2) != (count, total) else "multiple")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
