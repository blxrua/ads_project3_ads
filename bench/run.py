"""Run the light benchmark: four versions, in-program timer, oracle labels.

Builds v1..v4 with -DBENCH, runs each instance BENCH_REPEAT times, checks
every answer against bench/manifest.json, and writes:

    bench/results_light.csv   per instance / version
    bench/summary_light.csv   per family / size / version

Timing comes from QueryPerformanceCounter inside the program, so process
startup is not counted.  The median, p95 and worst of the per-instance
medians are reported, plus the DFS node count.

Usage:
    py -3.12 bench/run.py [--repeat N] [--no-build] [--filter TEXT]
"""

import argparse
import csv
import json
import os
import statistics
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIN = os.path.join(HERE, "bin")
MANIFEST = os.path.join(HERE, "manifest.json")

SOURCES = {
    1: "v1_steps123.c",
    2: "v2_full.c",
    3: "v3_ablate_step4.c",
    4: "v4_ablate_step5.c",
}
VERSIONS = [1, 2, 3, 4]


def build():
    os.makedirs(BIN, exist_ok=True)
    exes = {}
    for v, src in SOURCES.items():
        exe = os.path.join(BIN, "v%d.exe" % v)
        cmd = ["gcc", "-O2", "-std=c99", "-DBENCH", "-o", exe,
               os.path.join(ROOT, src)]
        subprocess.run(cmd, check=True)
        exes[v] = exe
    return exes


def parse_input(path):
    with open(path, "r", encoding="utf-8") as f:
        tok = f.read().split()
    it = iter(tok)
    n = int(next(it))
    m = int(next(it))
    tips = [(int(next(it)), int(next(it))) for _ in range(n)]
    fruits = [(int(next(it)), int(next(it))) for _ in range(m)]
    price = {i: p for i, p in fruits}
    edges = set()
    for a, b in tips:
        if a in price and b in price and a != b:
            edges.add((min(a, b), max(a, b)))
    return price, edges


def check(stdout, price, edges, opt_count, opt_price):
    lines = stdout.splitlines()
    if len(lines) < 3:
        return False, "short output"
    try:
        count = int(lines[0])
        ids = [int(t) for t in lines[1].split()]
        total = int(lines[2])
    except ValueError:
        return False, "bad number"

    if count != len(ids):
        return False, "count mismatch"
    if ids != sorted(set(ids)):
        return False, "ids not sorted/unique"
    for v in ids:
        if v not in price:
            return False, "id %03d not in basket" % v
    if sum(price[v] for v in ids) != total:
        return False, "price sum wrong"
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if (ids[i], ids[j]) in edges:
                return False, "conflict %03d %03d" % (ids[i], ids[j])
    if count != opt_count or total != opt_price:
        return False, "not optimal (got %d/%d want %d/%d)" % (
            count, total, opt_count, opt_price)
    return True, ""


def run_one(exe, case, repeat, timeout):
    env = dict(os.environ)
    env["BENCH_REPEAT"] = str(repeat)
    with open(case["abspath"], "rb") as f:
        try:
            proc = subprocess.run([exe], stdin=f,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "", [], 0, True
    out = proc.stdout.decode("ascii", "replace")
    err = proc.stderr.decode("ascii", "replace")
    times = []
    nodes = 0
    for line in err.splitlines():
        if line.startswith("BENCH "):
            parts = line.split()
            times.append(float(parts[1]))
            nodes = int(float(parts[2]))
    if len(times) != repeat:
        raise RuntimeError("%s: %d BENCH lines, want %d"
                           % (exe, len(times), repeat))
    return out, times, nodes, False


def p95(values):
    s = sorted(values)
    k = max(0, min(len(s) - 1, int(0.95 * len(s) + 0.9999) - 1))
    return s[k]


def measure(exe, case, args):
    """One run; repeat it only when the first solve was fast."""
    out, times, nodes, killed = run_one(exe, case, 1, args.timeout)
    if not killed and args.repeat > 1 and times[0] < args.threshold:
        out2, times2, nodes2, killed2 = run_one(exe, case, args.repeat,
                                                args.timeout)
        if not killed2:
            return out2, times2, nodes2, False
    return out, times, nodes, killed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", type=int, default=5,
                    help="repeats for fast instances")
    ap.add_argument("--threshold", type=float, default=10.0,
                    help="repeat only if the first solve is below this (ms)")
    ap.add_argument("--timeout", type=float, default=5.0,
                    help="kill one run after this many seconds (censored)")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--filter", default="")
    args = ap.parse_args()

    if args.no_build:
        exes = {v: os.path.join(BIN, "v%d.exe" % v) for v in VERSIONS}
        for exe in exes.values():
            if not os.path.exists(exe):
                sys.exit("missing %s (run without --no-build)" % exe)
    else:
        print("building ...")
        exes = build()

    with open(MANIFEST, "r", encoding="utf-8") as f:
        cases = json.load(f)["instances"]
    if args.filter:
        cases = [c for c in cases if args.filter in c["name"]]
    print("%d instances x %d versions x %d repeats"
          % (len(cases), len(VERSIONS), args.repeat))

    rows = []
    summary = {}
    wrong = 0
    timeouts = 0

    for idx, case in enumerate(cases, 1):
        case["abspath"] = os.path.join(HERE, case["path"].replace(
            "bench/", "", 1))
        price, edges = parse_input(case["abspath"])
        for v in VERSIONS:
            out, times, nodes, killed = measure(exes[v], case, args)
            if killed:
                ok, why = False, "timeout > %.1fs" % args.timeout
                med = max_ms = args.timeout * 1000.0
            else:
                ok, why = check(out, price, edges,
                                case["opt_count"], case["opt_price"])
                med = statistics.median(times)
                max_ms = max(times)
            if not ok:
                if killed:
                    timeouts += 1
                else:
                    wrong += 1
                    print("WRONG %s v%d: %s" % (case["name"], v, why))
            rows.append({
                "family": case["family"],
                "size": case["size"],
                "mode": case["mode"],
                "seed": case["seed"],
                "version": v,
                "median_ms": "%.6f" % med,
                "max_ms": "%.6f" % max_ms,
                "nodes": nodes,
                "ok": int(ok),
                "timed_out": int(killed),
            })
            key = (case["family"], case["size"], v)
            summary.setdefault(key, []).append((med, max_ms, nodes, killed))
        if idx % 10 == 0 or idx == len(cases):
            print("  %d/%d %s" % (idx, len(cases), case["name"]), flush=True)

    with open(os.path.join(HERE, "results_light.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    with open(os.path.join(HERE, "summary_light.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["family", "size", "version", "instances",
                    "median_ms", "p95_ms", "max_ms", "median_nodes",
                    "timeouts"])
        for key in sorted(summary):
            vals = summary[key]
            meds = [x[0] for x in vals]
            maxs = [x[1] for x in vals]
            nodes = [x[2] for x in vals]
            to = sum(1 for x in vals if x[3])
            w.writerow([key[0], key[1], key[2], len(vals),
                        "%.6f" % statistics.median(meds),
                        "%.6f" % p95(meds),
                        "%.6f" % max(maxs),
                        statistics.median(nodes), to])

    print("\nsummary (median of per-instance medians, ms; to = timeouts)")
    print("%-12s %4s %3s %10s %10s %10s %4s"
          % ("family", "size", "ver", "median", "p95", "max", "to"))
    for key in sorted(summary):
        vals = summary[key]
        meds = [x[0] for x in vals]
        print("%-12s %4d %3d %10.4f %10.4f %10.4f %4d"
              % (key[0], key[1], key[2], statistics.median(meds),
                 p95(meds), max(x[1] for x in vals),
                 sum(1 for x in vals if x[3])))

    if wrong:
        print("\n%d WRONG ANSWERS" % wrong)
        return 1
    print("\nALL %d ANSWERS MATCH THE ORACLE (%d timeouts recorded)"
          % (len(rows) - timeouts, timeouts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
