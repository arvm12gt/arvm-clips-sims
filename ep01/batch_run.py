#!/usr/bin/env python3
"""EP01 v4 aggregate batch runner.

Runs the exact model from sim.py (same parameters: 100 agents, $10,000 start,
30 days) with 100 different random seeds and tallies who wins. The featured
story run (seed 20261120, sim_log.json) is NOT part of this batch.

Seeds: 1..100.

Winner archetype classification (documented, applied in this priority order —
an agent is classified by their most extreme defining trait first):
  1. "genius"        : winner.skill >= 0.90          (top-decile skill)
  2. "workhorse"     : winner.work_ethic >= 0.90     (top-decile effort)
  3. "gambler"       : winner.strategy == "gambler"  (risk_appetite > 0.78 in sim.py)
  4. "quiet_builder" : winner.strategy == "builder"  (business owner — Ann's path)
  5. "other"         : everyone else (worker / lender / thief strategies
                       without an extreme trait above)
Raw winner-strategy tallies are also saved, so nothing is hidden by the
archetype mapping.

Extra stats:
  - most_skilled_bankrupt_runs: runs where the single highest-skill agent in
    that town finished with money <= 0 (the model's bankrupt condition).
  - median_winning_wealth: median of the 100 winners' final money.
  - winner_was_most_skilled_runs: runs where the winner IS the most-skilled agent.
  - very_lucky_winner_runs: runs where the winner's luck >= 0.85.
"""
import json, statistics, sys
sys.path.insert(0, ".")
import sim

N_RUNS = 100
SEEDS = list(range(1, N_RUNS + 1))

def archetype(winner):
    t = winner["traits"]
    if t["skill"] >= 0.90: return "genius"
    if t["work_ethic"] >= 0.90: return "workhorse"
    if winner["strategy"] == "gambler": return "gambler"
    if winner["strategy"] == "builder": return "quiet_builder"
    return "other"

runs = []
arch = {k: 0 for k in ("genius", "workhorse", "gambler", "quiet_builder", "other")}
strat = {k: 0 for k in ("worker", "builder", "gambler", "lender", "thief")}
ms_bankrupt = 0
winner_was_ms = 0
very_lucky = 0
win_money = []

for s in SEEDS:
    log = sim.run(seed=s)
    w = log["winner"]
    a = archetype(w)
    arch[a] += 1
    strat[w["strategy"]] += 1
    ms = log["most_skilled"]
    ms_broke = ms["final_money"] <= 0
    if ms_broke: ms_bankrupt += 1
    if w["name"] == ms["name"]: winner_was_ms += 1
    if w["traits"]["luck"] >= 0.85: very_lucky += 1
    win_money.append(w["money"])
    runs.append({
        "seed": s, "winner": w["name"], "winner_strategy": w["strategy"],
        "winner_archetype": a, "winner_money": w["money"],
        "winner_traits": w["traits"],
        "most_skilled": ms["name"], "most_skilled_final_money": ms["final_money"],
        "most_skilled_bankrupt": ms_broke,
        "total_bankrupt": log["total_bankrupt"],
    })
    if s % 25 == 0: print(f"...{s} runs done", flush=True)

out = {
    "n_runs": N_RUNS,
    "seeds": [SEEDS[0], SEEDS[-1]],
    "model": "sim.py run(seed), identical parameters to featured run; featured seed 20261120 not included",
    "archetype_method": ("priority order: genius (skill>=0.90) > workhorse (work_ethic>=0.90) "
                         "> gambler (strategy==gambler) > quiet_builder (strategy==builder) > other"),
    "wins_per_archetype": arch,
    "wins_per_strategy_raw": strat,
    "most_skilled_bankrupt_runs": ms_bankrupt,
    "winner_was_most_skilled_runs": winner_was_ms,
    "very_lucky_winner_runs": very_lucky,
    "median_winning_wealth": round(statistics.median(win_money)),
    "mean_winning_wealth": round(statistics.mean(win_money)),
    "min_winning_wealth": min(win_money),
    "max_winning_wealth": max(win_money),
    "runs": runs,
}
with open("aggregate_log.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
