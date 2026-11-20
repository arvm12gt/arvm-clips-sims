#!/usr/bin/env python3
"""EP03 aggregate batch runner.

Runs the exact model from sim.py (same parameters: 100 agents, 1 honest
+ 99 liars, 30 days) with 100 different random seeds and tallies what
happens to the honest one and to the town. The featured story run
(seed 445, sim_log.json) is NOT part of this batch.

Seeds: 1000..1099.

Winner classification for the headline stat: by the winner's STRONGEST
trait (the maximum of their five traits; ties broken in the order
skill, grit, risk, honesty, luck) — the same rule sim.strongest_trait
applies to the featured winner. Note the honest one's honesty is 1.0 by
construction, so when the honest one wins, their strongest trait is
"honesty". Raw winner-strategy tallies are also saved, so nothing is
hidden by the grouping.

Extra stats:
  - honest_one: wins / top-3 / top-10 finishes, median final rank,
    bankruptcies, median final money, median final reputation.
  - winner_had_highest_rep_runs: runs where the winner also finished
    with the town's highest reputation.
  - median_winning_money, mean lies / caught / defaults per town,
    mean final mean-reputation (the town's trust level on day 30).
"""
import json, statistics, sys
sys.path.insert(0, ".")
import sim

N_RUNS = 100
SEEDS = list(range(1000, 1000 + N_RUNS))
FEATURED_SEED = 445
assert FEATURED_SEED not in SEEDS

TRAITS = ("skill", "grit", "risk", "honesty", "luck")
STRATS = ("honest", "con artist", "hustler", "trader", "worker")

runs = []
trait_wins = {t: 0 for t in TRAITS}
strat_wins = {s: 0 for s in STRATS}
honest_wins = honest_top3 = honest_top10 = honest_bankrupt = 0
honest_ranks, honest_moneys, honest_reps = [], [], []
winner_top_rep = 0
win_moneys, lies_l, caught_l, defaults_l, mean_reps = [], [], [], [], []

for s in SEEDS:
    log = sim.run(seed=s)
    w = log["winner"]; h = log["honest_one"]
    trait_wins[w["strongest_trait"]] += 1
    strat_wins[w["strategy"]] += 1
    if h["final_rank"] == 1: honest_wins += 1
    if h["final_rank"] <= 3: honest_top3 += 1
    if h["final_rank"] <= 10: honest_top10 += 1
    if h["bankrupt"]: honest_bankrupt += 1
    honest_ranks.append(h["final_rank"]); honest_moneys.append(h["final_money"])
    honest_reps.append(h["final_rep"])
    max_rep = max(a["final_rep"] for a in log["agents"])
    if w["final_rep"] >= max_rep - 1e-9: winner_top_rep += 1
    win_moneys.append(w["final_money"])
    lies_l.append(log["total_lies"]); caught_l.append(log["total_caught"])
    defaults_l.append(log["total_defaults"]); mean_reps.append(log["final_mean_rep"])
    runs.append({
        "seed": s, "winner": w["name"], "winner_strategy": w["strategy"],
        "winner_strongest_trait": w["strongest_trait"],
        "winner_money": w["final_money"], "winner_rep": w["final_rep"],
        "honest_one": h["name"], "honest_rank": h["final_rank"],
        "honest_money": h["final_money"], "honest_rep": h["final_rep"],
        "honest_bankrupt": h["bankrupt"],
        "total_lies": log["total_lies"], "total_caught": log["total_caught"],
        "total_defaults": log["total_defaults"],
    })
    if s % 25 == 0: print(f"...{s} runs done", flush=True)

out = {
    "n_runs": N_RUNS,
    "seeds": [SEEDS[0], SEEDS[-1]],
    "model": "sim.py run(seed), identical parameters to featured run; featured seed 445 not included",
    "grouping_method": "winner classified by strongest trait (max of the five; ties in order skill, grit, risk, honesty, luck)",
    "wins_by_strongest_trait": trait_wins,
    "wins_by_strategy_raw": strat_wins,
    "honest_one": {
        "wins": honest_wins, "top3": honest_top3, "top10": honest_top10,
        "bankrupt": honest_bankrupt,
        "median_rank": statistics.median(honest_ranks),
        "median_final_money": round(statistics.median(honest_moneys)),
        "median_final_rep": round(statistics.median(honest_reps), 3),
    },
    "winner_had_highest_rep_runs": winner_top_rep,
    "median_winning_money": round(statistics.median(win_moneys)),
    "mean_lies_per_town": round(statistics.mean(lies_l)),
    "mean_caught_per_town": round(statistics.mean(caught_l)),
    "mean_defaults_per_town": round(statistics.mean(defaults_l)),
    "mean_final_mean_rep": round(statistics.mean(mean_reps), 3),
    "runs": runs,
}
with open("aggregate_log.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
