"""Two more questions for the checkout video : one slow cashier, and a store twice the size.  python3 slow_cashier_and_big_store.py (run checkout.py first)"""
import numpy as np, json, checkout as C
seeds=[1,2,3,4,5]; n=200_000; out={}
def go(name, c, rho, pick, speed=None, mean_s=2.0):
    ws=[];ks=[]
    for s in seeds:
        arr,svc,tie=C.shoppers(n,c,rho,mean_s,0.8,s)
        if speed:                                   # the same number of shoppers as in the normal store: do not re-scale arrivals
            pass
        till=np.full(n,-1); w=C.run(arr,svc,tie,c=c,pick=pick,speed=speed,till_of=till); ws.append(w[n//20:]); ks.append(till[n//20:])
    w=np.concatenate(ws); k=np.concatenate(ks)
    o={"mean":float(w.mean()),"over10":float((w>10).mean()),"max":float(w.max()),"per_seed":[round(float(x.mean()),3) for x in ws]}
    if speed: o["mean_by_till"]=[float(w[k==j].mean()) for j in range(c)]; o["share_by_till"]=[float((k==j).mean()) for j in range(c)]
    out[name]=o; print(f"{name:52s} mean {o['mean']*60:6.0f} s  >10min {o['over10']*100:5.2f} %  max {o['max']:4.0f}"+(("  by till "+" ".join(f"{x*60:.0f}" for x in o['mean_by_till'])+"  share "+" ".join(f"{x*100:.0f}" for x in o['share_by_till'])) if speed else ""),flush=True)
for f in (1.25,1.5):
    SLOW=[1,1,f,1,1]
    go(f"one slow cashier ({f}x), shortest line",5,0.9,"people",SLOW)
    go(f"one slow cashier ({f}x), one shared line",5,0.9,"single",SLOW)
go("ten tills, same busyness: shortest line",10,0.9,"people")
go("ten tills, same busyness: one shared line",10,0.9,"single")
go("five tills (for comparison): shortest line",5,0.9,"people")
go("five tills (for comparison): one shared line",5,0.9,"single")
go("twenty tills, same busyness: shortest line",20,0.9,"people")
go("twenty tills, same busyness: one shared line",20,0.9,"single")
d=json.load(open("checkout_out.json")); d["extras2"]=out; json.dump(d,open("checkout_out.json","w"),indent=1)
