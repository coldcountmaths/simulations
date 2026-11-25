"""Checkout lines: which rule makes customers wait least?  (All of It, Explained, sample 2026-11-24)
c tills, Poisson arrivals, service times lognormal (or exponential for the check against theory).
Rules:  random   = pick any line and stay
        shortest = join the line with the fewest people (ties at random) and stay
        single   = one shared line, the next free till takes the first in line
Wait = time from arrival to the start of service. Deterministic for a given seed."""
import heapq, math, sys, json
import numpy as np

def simulate(rule, n, c=5, rho=0.9, mean_s=2.0, cv=0.8, seed=1, expo=False):
    rng = np.random.default_rng(seed)
    lam = rho * c / mean_s
    arr = np.cumsum(rng.exponential(1 / lam, n))
    if expo:
        svc = rng.exponential(mean_s, n)
    else:
        s2 = math.log(1 + cv * cv); svc = rng.lognormal(math.log(mean_s) - s2 / 2, math.sqrt(s2), n)
    wait = np.empty(n)
    if rule == "single":
        free = [0.0] * c; heapq.heapify(free)          # times at which each till becomes free (FIFO order holds)
        for i in range(n):
            f = heapq.heappop(free); st = max(arr[i], f); wait[i] = st - arr[i]; heapq.heappush(free, st + svc[i])
    else:
        last = [0.0] * c                                # when the last person in each line will be done
        dep = [[] for _ in range(c)]                    # departure times of the people still in each line
        pick = rng.integers(0, c, n); tie = rng.random((n, c))
        for i in range(n):
            t = arr[i]
            if rule == "random":
                k = pick[i]
            else:
                best, k = None, 0
                for j in range(c):
                    d = dep[j]
                    while d and d[0] <= t: d.pop(0)
                    key = (len(d), tie[i, j])
                    if best is None or key < best: best, k = key, j
            st = max(t, last[k]); wait[i] = st - t; last[k] = st + svc[i]
            if rule != "random": dep[k].append(last[k])
    w = wait[n // 20:]                                   # drop the warm-up
    return {"rule": rule, "n": int(len(w)), "mean": float(w.mean()), "median": float(np.median(w)), "p95": float(np.quantile(w, .95)),
            "p99": float(np.quantile(w, .99)), "over10": float((w > 10).mean()), "max": float(w.max())}

def erlang_c_wait(c, rho, mean_s):
    a = c * rho; s = sum(a ** k / math.factorial(k) for k in range(c)); top = a ** c / math.factorial(c) / (1 - rho)
    return top / (s + top) * mean_s / (c * (1 - rho))

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    # checks against queueing theory (exponential service): M/M/c for the single line, M/M/1 for random lines
    t1 = simulate("single", n, expo=True, seed=7)["mean"]; t2 = simulate("random", n, expo=True, seed=7)["mean"]
    th1 = erlang_c_wait(5, .9, 2.0); th2 = .9 / (1 - .9) * 2.0
    print(f"CHECK single: sim {t1:.3f} theory {th1:.3f} | random: sim {t2:.3f} theory {th2:.3f}")
    out = {"checks": {"single_sim": t1, "single_theory": th1, "random_sim": t2, "random_theory": th2}, "runs": []}
    for rule in ("random", "shortest", "single"):
        r = simulate(rule, n, seed=1); out["runs"].append(r)
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    json.dump(out, open("queues_out.json", "w"), indent=1)
