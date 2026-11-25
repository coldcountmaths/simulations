"""CHECKOUT LINES. Which rule makes a shopper wait least?  (All of It, Explained)
Event-driven simulation: c tills, Poisson arrivals, each shopper has a basket (= service time).
Wait = minutes from joining a line to the start of scanning. Same random shoppers for every rule (same seeds).

Scenario switches:
  pick     "random" | "people" (fewest people in line) | "work" (least minutes of baskets ahead) | "single" (one shared line)
  jockey   True: when a till's line is shorter by 2 or more, the LAST person of the longest line moves over
  express  minutes or None: till 0 only takes baskets up to this size; small baskets may use any till
  slow     share of shoppers who take 5x longer than their basket says (price check, coupons, lost card)
  speed    list, one number per till: 1.5 = this cashier needs 1.5x as long for every basket (slow_cashier_and_big_store.py)
"""
import heapq, math, json, sys
from collections import deque
import numpy as np

def shoppers(n, c, rho, mean_s, cv, seed, slow=0.0):
    rng = np.random.default_rng(seed)
    s2 = math.log(1 + cv * cv); svc = rng.lognormal(math.log(mean_s) - s2 / 2, math.sqrt(s2), n)
    if slow: svc = np.where(rng.random(n) < slow, svc * 5, svc)
    lam = rho * c / svc.mean()                       # the store is equally busy in every scenario
    arr = np.cumsum(rng.exponential(1 / lam, n))
    return arr, svc, rng.random(n)

def run(arr, svc, tie, c=5, pick="people", jockey=False, express=None, speed=None, till_of=None):
    n = len(arr); wait = np.full(n, -1.0); sp = speed or [1.0] * c
    if pick == "single":
        free = [(0.0, k) for k in range(c)]; heapq.heapify(free)
        for i in range(n):
            f, k = heapq.heappop(free); st = max(arr[i], f); wait[i] = st - arr[i]; heapq.heappush(free, (st + svc[i] * sp[k], k))
            if till_of is not None: till_of[i] = k
        return wait
    line = [deque() for _ in range(c)]               # waiting shoppers (not the one being served)
    busy = [None] * c                                # shopper at the till
    work = [0.0] * c                                 # minutes of baskets waiting in the line
    done = [0.0] * c                                 # when the till finishes its current shopper
    ev = []                                          # (time, till) departures
    def start(k, i, t):
        busy[k] = i; wait[i] = t - arr[i]; done[k] = t + svc[i] * sp[k]; heapq.heappush(ev, (done[k], k))
        if till_of is not None: till_of[i] = k
    def people(k): return len(line[k]) + (busy[k] is not None)
    def rebalance(t):
        while True:
            ks = [k for k in range(c)]
            hi = max(ks, key=people); cand = [k for k in ks if people(hi) - people(k) >= 2 and line[hi]]
            if express is not None and line[hi] and svc[line[hi][-1]] > express: cand = [k for k in cand if k != 0]
            if not cand: return
            lo = min(cand, key=people); i = line[hi].pop(); work[hi] -= svc[i]
            if busy[lo] is None: start(lo, i, t)
            else: line[lo].append(i); work[lo] += svc[i]
    def leave(t):
        while ev and ev[0][0] <= t:
            td, k = heapq.heappop(ev); busy[k] = None
            if line[k]:
                i = line[k].popleft(); work[k] -= svc[i]; start(k, i, td)
            if jockey: rebalance(td)
    for i in range(n):
        t = arr[i]; leave(t)
        ok = range(c) if (express is None or svc[i] <= express) else range(1, c)
        if pick == "random": k = ok[int(tie[i] * len(ok))]
        elif pick == "people": k = min(ok, key=lambda j: (people(j), (tie[i] * (j + 3)) % 1))
        else: k = min(ok, key=lambda j: (work[j] + max(done[j] - t, 0.0) if busy[j] is not None else 0.0, (tie[i] * (j + 3)) % 1))
        if busy[k] is None: start(k, i, t)
        else: line[k].append(i); work[k] += svc[i]
    leave(float("inf"))
    return wait

def stats(w, svc=None, express=None):
    o = {"mean": float(w.mean()), "median": float(np.median(w)), "p95": float(np.quantile(w, .95)), "over10": float((w > 10).mean()), "max": float(w.max())}
    if svc is not None and express is not None:
        sm = svc <= express; o["mean_small"] = float(w[sm].mean()); o["mean_big"] = float(w[~sm].mean()); o["share_small"] = float(sm.mean())
    return o

def scenario(name, seeds, n, c=5, rho=0.9, mean_s=2.0, cv=0.8, slow=0.0, **kw):
    ws, ss = [], []
    for s in seeds:
        arr, svc, tie = shoppers(n, c, rho, mean_s, cv, s, slow); w = run(arr, svc, tie, c=c, **kw)
        assert (w >= 0).all(); ws.append(w[n // 20:]); ss.append(svc[n // 20:])
    w = np.concatenate(ws); sv = np.concatenate(ss)
    o = stats(w, sv, kw.get("express")); o.update(name=name, shoppers=int(len(w)), per_seed_mean=[round(float(x.mean()), 3) for x in ws]); return o

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000; seeds = [1, 2, 3, 4, 5]
    out = {"params": {"tills": 5, "busy": 0.9, "mean_basket_min": 2.0, "cv": 0.8, "shoppers_per_scenario": n * len(seeds), "seeds": seeds}, "runs": []}
    S = [("random line", dict(pick="random")), ("shortest line (count people)", dict(pick="people")), ("one shared line", dict(pick="single")),
         ("shortest line + switching", dict(pick="people", jockey=True)), ("least items ahead", dict(pick="work")),
         ("express till (baskets up to 1.5 min, about half the shoppers)", dict(pick="people", express=1.5)), ("express till TOO STRICT (up to 1 min): the other four tills cannot keep up, lines grow without end", dict(pick="people", express=1.0)),
         ("slow shoppers 3 %: shortest line", dict(pick="people", slow=0.03)), ("slow shoppers 3 %: one shared line", dict(pick="single", slow=0.03)),
         ("a sixth till opens (same shoppers): shortest line", dict(pick="people", c=6, rho=0.75)), ("quiet store 70 %: shortest line", dict(pick="people", rho=0.7)), ("quiet store 70 %: one shared line", dict(pick="single", rho=0.7))]
    for name, kw in S:
        o = scenario(name, seeds, n, **kw); out["runs"].append(o)
        print(f"{name[:44]:44s} mean {o['mean']*60:6.0f} s  median {o['median']*60:5.0f} s  p95 {o['p95']:5.1f} min  >10min {o['over10']*100:5.2f} %  max {o['max']:5.0f}" + (f"  small {o['mean_small']*60:.0f}s big {o['mean_big']*60:.0f}s ({o['share_small']*100:.0f}% small)" if 'mean_small' in o else ""), flush=True)
    json.dump(out, open("checkout_out.json", "w"), indent=1)
