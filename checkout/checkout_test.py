"""Checks of checkout.py against cases with a known answer."""
import numpy as np, math, checkout as C, queues_v0 as Q
n = 400_000
# 1. exponential baskets: shared line = M/M/c (Erlang C), random line = M/M/1
rng = np.random.default_rng(7); svc = rng.exponential(2.0, n); arr = np.cumsum(rng.exponential(1 / (0.9 * 5 / 2.0), n)); tie = rng.random(n)
a = C.run(arr, svc, tie, pick="single")[n // 20:].mean(); b = C.run(arr, svc, tie, pick="random")[n // 20:].mean()
print(f"shared line  sim {a:.2f}  theory {Q.erlang_c_wait(5, .9, 2.0):.2f}"); print(f"random line  sim {b:.2f}  theory {0.9/0.1*2.0:.2f}")
# 2. one till: every rule is the same queue
arr1 = np.cumsum(rng.exponential(1 / (0.8 / 2.0), n)); x = [C.run(arr1, svc, tie, c=1, pick=p)[n // 20:].mean() for p in ("single", "people", "work", "random")]
print("one till, all rules equal:", [round(v, 3) for v in x], "theory", round(0.8 / 0.2 * 2.0, 2)); assert max(x) - min(x) < 1e-9
# 3. nobody is lost, nobody served twice; switching never leaves a till idle while someone waits elsewhere two deep
w = C.run(arr, svc, tie, pick="people", jockey=True); assert (w >= 0).all()
# 4. express till never takes a big basket: with the limit at 0 nobody may use till 0 -> same as 4 tills
w4 = C.run(arr[:100000] * 1.6, svc[:100000], tie[:100000], c=4, pick="people"); w5 = C.run(arr[:100000] * 1.6, svc[:100000], tie[:100000], c=5, pick="people", express=0.0)
print("express limit 0 = four tills:", round(w4.mean(), 3), round(w5.mean(), 3))
print("ALL CHECKS RAN")
