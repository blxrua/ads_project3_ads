# Special correctness cases.
# Brute force every optimal set, then check each version outputs one of them.

import os
import subprocess

EXES = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "v%d.exe" % i)
        for i in range(1, 6)]
OUTDIR = "special"

CASES = [
    {
        # Cheapest vertex sits on a path and blocks the maximum set.
        "name": "count_primary",
        "brute": True,
        "tips": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1),
                 (6, 7), (7, 8), (8, 9), (9, 10)],
        "fruits": [(1, 10), (2, 20), (3, 30), (4, 40), (5, 50),
                   (6, 100), (7, 1), (8, 100), (9, 100), (10, 100),
                   (11, 7), (12, 8)],
    },
    {
        # Same count, same total price, different sets.
        "name": "multi_optima",
        "brute": True,
        "tips": [(1, 2), (2, 3), (3, 4), (4, 1), (5, 6),
                 (7, 8), (8, 9), (9, 7)],
        "fruits": [(1, 1), (2, 2), (3, 4), (4, 3), (5, 7),
                   (6, 7), (7, 10), (8, 10), (9, 10), (10, 9)],
    },
    {
        # Dirty input: tips outside the basket, duplicate tip, mixed prices.
        "name": "dirty_input",
        "brute": True,
        "tips": [(1, 2), (3, 4), (4, 5), (5, 3), (6, 7), (7, 8),
                 (1, 99), (100, 2), (50, 51), (1, 2)],
        "fruits": [(1, 1000), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1),
                   (7, 1000), (8, 1), (9, 1000), (10, 1), (11, 1000), (12, 1)],
    },
    {
        # Many components, every small component has tied optima.
        "name": "components_ties",
        "brute": True,
        "tips": [(1, 2), (2, 3), (3, 1),
                 (4, 5), (5, 6), (6, 4),
                 (7, 8), (8, 9), (9, 7),
                 (10, 11), (12, 13),
                 (14, 15), (15, 16), (16, 17), (17, 14)],
        "fruits": [(i, 5) for i in range(1, 14)] +
                  [(14, 1), (15, 2), (16, 3), (17, 4), (18, 2)],
    },
    {
        # Maximum size: 50 disjoint edges, one endpoint cheaper.
        "name": "max_size_edges",
        "brute": False,
        "tips": [(2 * i + 1, 2 * i + 2) for i in range(50)],
        "fruits": [(2 * i + 1, 10 * i + 1) for i in range(50)] +
                  [(2 * i + 2, 10 * i + 2) for i in range(50)],
    },
]


def prepare(c):
    ids = [x[0] for x in c["fruits"]]
    price = {x[0]: x[1] for x in c["fruits"]}
    m = len(ids)
    pos = {v: i for i, v in enumerate(ids)}
    adj = [0] * m
    for a, b in c["tips"]:
        if a in pos and b in pos and a != b:
            u, v = pos[a], pos[b]
            adj[u] |= 1 << v
            adj[v] |= 1 << u
    return ids, price, m, pos, adj


def all_optima(ids, price, m, adj):
    best = (-1, 0)
    masks = []
    for mask in range(1 << m):
        ok = True
        cnt = 0
        tot = 0
        x = mask
        while x:
            low = x & -x
            i = low.bit_length() - 1
            x ^= low
            if adj[i] & mask:
                ok = False
                break
            cnt += 1
            tot += price[ids[i]]
        if not ok:
            continue
        key = (cnt, -tot)
        if key > best:
            best = key
            masks = [mask]
        elif key == best:
            masks.append(mask)
    return best[0], -best[1], masks


def max_size_expected(ids, price, m, pos):
    chosen = []
    total = 0
    for i in range(50):
        a, b = 2 * i + 1, 2 * i + 2
        if price[a] <= price[b]:
            chosen.append(a)
            total += price[a]
        else:
            chosen.append(b)
            total += price[b]
    mask = 0
    for v in chosen:
        mask |= 1 << pos[v]
    return len(chosen), total, [mask]


def to_input(c):
    lines = ["%d %d" % (len(c["tips"]), len(c["fruits"]))]
    lines += ["%d %d" % (a, b) for a, b in c["tips"]]
    lines += ["%03d %d" % (i, p) for i, p in c["fruits"]]
    return "\n".join(lines) + "\n"


def parse(out):
    lines = out.splitlines()
    if len(lines) < 3:
        raise ValueError("output has %d lines" % len(lines))
    if lines[1] != lines[1].rstrip():
        raise ValueError("trailing space on ID line")
    ids = [int(x) for x in lines[1].split()] if lines[1].strip() else []
    return int(lines[0]), ids, int(lines[2])


def check(c, ids, price, m, pos, adj, exp_cnt, exp_price, exp_masks, out):
    cnt, out_ids, total = parse(out)
    mask = 0
    for v in out_ids:
        if v not in pos:
            return "unknown id %d" % v
        mask |= 1 << pos[v]
    if len(out_ids) != cnt:
        return "count line %d != %d ids" % (cnt, len(out_ids))
    if out_ids != sorted(set(out_ids)):
        return "ids not strictly increasing"
    for v in out_ids:
        if adj[pos[v]] & mask:
            return "conflict at id %d" % v
    if total != sum(price[v] for v in out_ids):
        return "price sum mismatch"
    if (cnt, total) != (exp_cnt, exp_price):
        return "objective %s != expected %s" % ((cnt, total), (exp_cnt, exp_price))
    if exp_masks is not None and mask not in exp_masks:
        return "optimal value but unexpected set"
    return None


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    fails = 0
    for c in CASES:
        ids, price, m, pos, adj = prepare(c)
        data = to_input(c)
        path = os.path.join(OUTDIR, c["name"] + ".in")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)

        if c["brute"]:
            exp_cnt, exp_price, masks = all_optima(ids, price, m, adj)
        else:
            exp_cnt, exp_price, masks = max_size_expected(ids, price, m, pos)

        print("=== %s (M=%d, N=%d) ===" % (c["name"], m, len(c["tips"])))
        print("    optimum: count=%d price=%d, optimal sets=%d"
              % (exp_cnt, exp_price, len(masks)))

        for exe in EXES:
            r = subprocess.run([exe], input=data.encode(),
                               capture_output=True, cwd=".")
            out = r.stdout.decode("utf-8", "replace")
            try:
                err = check(c, ids, price, m, pos, adj,
                            exp_cnt, exp_price, set(masks), out)
            except ValueError as e:
                err = str(e)
            if err:
                fails += 1
                print("    %-8s FAIL  %s" % (exe, err))
            else:
                print("    %-8s ok   %s | %s | %s"
                      % (exe, out.splitlines()[0], out.splitlines()[1],
                         out.splitlines()[2]))

    print()
    if fails:
        print("FAILED: %d checks" % fails)
        return 1
    print("ALL SPECIAL CASES PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
