#!/usr/bin/env python3
"""EP02 aggregate batch runner.

Runs the exact model from sim.py (same parameters: 100 agents, 10 tools,
30 days) with 100 different random seeds and tallies who thrives. The
featured story run (seed 42, sim_log.json) is NOT part of this batch.

Seeds: 1000..1099.

Winner classification for the headline stat: by the winner's STRONGEST
trait (the maximum of their five traits; ties broken in the order
skill, grit, risk, honesty, luck) — the same rule sim.strongest_trait
applies to the featured winner. Raw winner-strategy tallies are also
saved, so nothing is hidden by the grouping.

Extra stats:
  - survival_rate_by_strategy: for each strategy, the share of agents
    alive on day 30, pooled across all 100 runs (agents, not runs).
  - winner_in_group_runs: runs where the winner belonged to a camp.
  - winner_was_most_skilled_runs: runs where the winner IS the island's
    single most-skilled agent.
  - median_winning_score / mean_deaths.
"""
import json, statistics, sys
sys.path.insert(0, ".")
import sim

N_RUNS = 100
SEEDS = list(range(1000, 1000 + N_RUNS))
FEATURED_SEED = 42
assert FEATURED_SEED not in SEEDS

TRAITS = ("skill", "grit", "risk", "honesty", "luck")
STRATS = ("leader", "cooperator", "survivor", "hoarder", "loner", "thief")

runs = []
trait_wins = {t: 0 for t in TRAITS}
strat_wins = {s: 0 for s in STRATS}
surv_n = {s: 0 for s in STRATS}
surv_alive = {s: 0 for s in STRATS}
winner_in_group = 0
winner_was_ms = 0
win_scores = []
deaths = []

for s in SEEDS:
    log = sim.run(seed=s)
    w = log["winner"]
    trait_wins[w["strongest_trait"]] += 1
    strat_wins[w["strategy"]] += 1
    if w["group"] >= 0: winner_in_group += 1
    if w["name"] == log["most_skilled"]["name"]: winner_was_ms += 1
    win_scores.append(w["final_score"])
    deaths.append(log["total_deaths"])
    for strat, d in log["survival_by_strategy"].items():
        surv_n[strat] += d["n"]; surv_alive[strat] += d["alive"]
    runs.append({
        "seed": s, "winner": w["name"], "winner_strategy": w["strategy"],
        "winner_strongest_trait": w["strongest_trait"],
        "winner_score": w["final_score"], "winner_in_group": w["group"] >= 0,
        "winner_traits": w["traits"],
        "most_skilled": log["most_skilled"]["name"],
        "total_deaths": log["total_deaths"],
    })
    if s % 25 == 0: print(f"...{s} runs done", flush=True)

out = {
    "n_runs": N_RUNS,
    "seeds": [SEEDS[0], SEEDS[-1]],
    "model": "sim.py run(seed), identical parameters to featured run; featured seed 42 not included",
    "grouping_method": "winner classified by strongest trait (max of the five; ties in order skill, grit, risk, honesty, luck)",
    "wins_by_strongest_trait": trait_wins,
    "wins_by_strategy_raw": strat_wins,
    "survival_rate_by_strategy": {s: (round(surv_alive[s] / surv_n[s], 3) if surv_n[s] else None)
                                  for s in STRATS},
    "survival_counts": {s: {"agents": surv_n[s], "alive": surv_alive[s]} for s in STRATS},
    "winner_in_group_runs": winner_in_group,
    "winner_was_most_skilled_runs": winner_was_ms,
    "median_winning_score": round(statistics.median(win_scores)),
    "mean_deaths": round(statistics.mean(deaths), 1),
    "min_deaths": min(deaths), "max_deaths": max(deaths),
    "runs": runs,
}
with open("aggregate_log.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
