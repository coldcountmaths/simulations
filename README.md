# All of It, Explained: the simulations

The code behind the videos. Every number said in a video comes out of one of these files.
Run it, change it, tell me where I'm wrong.

You need Python 3 and numpy (`pip install numpy`).

## checkout/ : which supermarket line is fastest?

```
cd checkout
python3 checkout.py                      # the main rules, about 2 minutes
python3 slow_cashier_and_big_store.py    # one slow cashier; 10 and 20 checkouts
python3 checkout_test.py                 # checks against cases with a known answer
```

The store: 5 checkouts, every cashier busy 9 minutes out of 10, an average basket takes 2 minutes
(most are small, a few are huge). One million shoppers per rule, the same shoppers for every rule.
"Wait" is the time from joining a line until your first item is scanned.

| rule | average wait |
|---|---|
| nobody looks, everyone picks a line at random | 14:30 |
| everyone joins the line with the fewest people | 2:53 |
| the last person may jump to a line 2 people shorter | 2:31 |
| everyone joins the line with the least groceries ahead | 2:31 |
| one shared line for all checkouts | 2:31 |
| one express checkout (baskets up to 1.5 min) | 3:32 |
| one cashier needs 25 % longer per basket | 5:08 |
| a sixth checkout, same shoppers | 0:42 |

What the shoppers in this model do not do: they never give up and leave, in each run all of them
follow the same rule, and nobody opens a new checkout when it gets busy. Your exact seconds will differ.

Things to try: change the number of checkouts (`c`), how busy the store is (`rho`), how uneven the
baskets are (`cv`), or write your own rule in `run()`.
