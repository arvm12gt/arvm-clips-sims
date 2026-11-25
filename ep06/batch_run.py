#!/usr/bin/env python3
"""EP06 aggregate batch runner.

Runs the exact model from sim.py (same parameters: 100 agents,
$100 each except Richard at $0, 6 free hours/day each, 30 days) with
100 different random seeds and tallies what happens across towns. The
featured story run (see REPRODUCE.md for the chosen seed) is NOT part
of this batch.

Seeds: 1000..1099.

Winner classification for the headline stat: by the winner's STRONGEST
trait (the maximum of their five START traits; ties broken in the order
skill, grit, risk, honesty, luck) — the same rule sim.strongest_trait
applies to the featured winner. Raw winner-strategy tallies are also
saved, so nothing is hidden by the grouping.

Headline question of this episode — how often does the ex-rich man win?
The batch counts runs where the winner IS Richard (rich_wins), his
median final rank, and his top-3/top-5 rates. It also measures the
credit mechanism: median winner borrowing, and runs where the winner
borrowed more than the town average (the "leverage helped" check).

Extra stats:
  - winner learn hours/day vs town average (median), and runs where the
    winner learned more than the town average.
  - winner waste hours/day vs town average (median).
  - winner skill gain (median) and winner reputation distribution.
  - median winning margin (dollars and percent), median lead changes,
    mean lies / caught / flops per town, winner-is-final-leader runs
    (winner also the most-followed agent on day 30).
"""
import json, statistics, sys
sys.path.insert(0, ".")
import sim

N_RUNS = 100
SEEDS = list(range(1000, 1000 + N_RUNS))
FEATURED_SEED = None  # set from scan_results.json at run time; must not be in SEEDS
try:
    with open("scan_results.json") as f:
        FEATURED_SEED = json.load(f)["top_candidates"][0]["seed"]
except Exception:
    pass
assert FEATURED_SEED not in SEEDS, f"featured seed {FEATURED_SEED} inside batch range"

TRAITS = ("skill", "grit", "risk", "honesty", "luck")
STRATS = ("waster", "learner", "hustler", "gambler", "dealer", "worker")

runs = []
trait_wins = {t: 0 for t in TRAITS}
strat_wins = {s: 0 for s in STRATS}
winner_learn, town_learn, winner_waste, town_waste = [], [], [], []
winner_borrowed, town_borrowed = [], []
winner_skill_gain, winner_reps = [], []
margins, margin_pcts, lead_changes_l = [], [], []
lies_l, caught_l, flops_l, mean_reps, mean_skills = [], [], [], [], []
winner_learned_more_runs = winner_wasted_less_runs = 0
winner_borrowed_more_runs = 0
winner_final_leader_runs = 0
winner_follower_peaks = []
rep_buckets = {">=0.9": 0, "0.7-0.9": 0, "0.5-0.7": 0, "<0.5": 0}
rich_wins = 0
rich_ranks = []
rich_top3 = rich_top5 = 0
rich_borrowed_l, rich_invret_l = [], []
winner_invest_ret_l = []

for s in SEEDS:
    log = sim.run(seed=s)
    w = log["winner"]
    r = log["rich"]
    trait_wins[w["strongest_trait"]] += 1
    strat_wins[w["strategy"]] += 1
    winner_learn.append(w["learn_per_day"])
    town_learn.append(log["town_avg_learn_per_day"])
    winner_waste.append(w["waste_per_day"])
    town_waste.append(log["town_avg_waste_per_day"])
    winner_borrowed.append(w["borrowed_per_day"])
    town_borrowed.append(log["town_avg_borrowed_per_day"])
    winner_skill_gain.append(w["skill_gain"])
    winner_reps.append(w["final_rep"])
    winner_invest_ret_l.append(w["invest_return_total"])
    if w["learn_per_day"] > log["town_avg_learn_per_day"]:
        winner_learned_more_runs += 1
    if w["waste_per_day"] < log["town_avg_waste_per_day"]:
        winner_wasted_less_runs += 1
    if w["borrowed_per_day"] > log["town_avg_borrowed_per_day"]:
        winner_borrowed_more_runs += 1
    if w["final_rep"] >= 0.9: rep_buckets[">=0.9"] += 1
    elif w["final_rep"] >= 0.7: rep_buckets["0.7-0.9"] += 1
    elif w["final_rep"] >= 0.5: rep_buckets["0.5-0.7"] += 1
    else: rep_buckets["<0.5"] += 1
    if log["final_leader"]["name"] == w["name"]:
        winner_final_leader_runs += 1
    if w["name"] == "Richard":
        rich_wins += 1
    rich_ranks.append(r["final_rank"])
    if r["final_rank"] <= 3: rich_top3 += 1
    if r["final_rank"] <= 5: rich_top5 += 1
    rich_borrowed_l.append(r["borrowed_total"])
    rich_invret_l.append(r["invest_return_total"])
    margins.append(log["winning_margin"]); margin_pcts.append(log["winning_margin_pct"])
    lead_changes_l.append(log["lead_changes"])
    lies_l.append(log["total_lies"]); caught_l.append(log["total_caught"])
    flops_l.append(log["total_flops"]); mean_reps.append(log["final_mean_rep"])
    mean_skills.append(log["final_mean_skill"])
    winner_follower_peaks.append(w["followers_peak"])
    runs.append({
        "seed": s, "winner": w["name"], "winner_strategy": w["strategy"],
        "winner_strongest_trait": w["strongest_trait"],
        "winner_money": w["final_money"], "winner_rep": w["final_rep"],
        "winner_learn_per_day": w["learn_per_day"],
        "town_avg_learn_per_day": log["town_avg_learn_per_day"],
        "winner_waste_per_day": w["waste_per_day"],
        "town_avg_waste_per_day": log["town_avg_waste_per_day"],
        "winner_borrowed_per_day": w["borrowed_per_day"],
        "town_avg_borrowed_per_day": log["town_avg_borrowed_per_day"],
        "winner_invest_return_total": w["invest_return_total"],
        "winner_skill_gain": w["skill_gain"],
        "winner_followers_peak": w["followers_peak"],
        "rich_rank": r["final_rank"], "rich_money": r["final_money"],
        "rich_borrowed_total": r["borrowed_total"],
        "rich_invest_return_total": r["invest_return_total"],
        "winning_margin": log["winning_margin"],
        "winning_margin_pct": log["winning_margin_pct"],
        "lead_changes": log["lead_changes"],
        "distinct_leaders": log["distinct_leaders"],
        "total_lies": log["total_lies"], "total_caught": log["total_caught"],
        "total_flops": log["total_flops"],
    })
    if s % 25 == 0: print(f"...{s} runs done", flush=True)

out = {
    "n_runs": N_RUNS,
    "seeds": [SEEDS[0], SEEDS[-1]],
    "model": "sim.py run(seed), identical parameters to featured run; featured seed "
             f"{FEATURED_SEED} not included",
    "grouping_method": "winner classified by strongest START trait (max of the five; ties in order skill, grit, risk, honesty, luck)",
    "wins_by_strongest_trait": trait_wins,
    "wins_by_strategy_raw": strat_wins,
    "rich": {
        "rich_wins": rich_wins,
        "rich_median_final_rank": statistics.median(rich_ranks),
        "rich_top3_runs": rich_top3,
        "rich_top5_runs": rich_top5,
        "rich_median_borrowed_total": round(statistics.median(rich_borrowed_l)),
        "rich_median_invest_return_total": round(statistics.median(rich_invret_l)),
    },
    "winner_learn": {
        "median_winner_learn_per_day": round(statistics.median(winner_learn), 2),
        "median_town_avg_learn_per_day": round(statistics.median(town_learn), 2),
        "winner_learned_more_than_town_avg_runs": winner_learned_more_runs,
    },
    "winner_waste": {
        "median_winner_waste_per_day": round(statistics.median(winner_waste), 2),
        "median_town_avg_waste_per_day": round(statistics.median(town_waste), 2),
        "winner_wasted_less_than_town_avg_runs": winner_wasted_less_runs,
    },
    "winner_borrowed": {
        "median_winner_borrowed_per_day": round(statistics.median(winner_borrowed), 1),
        "median_town_avg_borrowed_per_day": round(statistics.median(town_borrowed), 1),
        "winner_borrowed_more_than_town_avg_runs": winner_borrowed_more_runs,
        "median_winner_invest_return_total": round(statistics.median(winner_invest_ret_l)),
    },
    "winner_skill_gain": {
        "median_winner_skill_gain": round(statistics.median(winner_skill_gain), 3),
    },
    "winner_reputation": {
        "median_winner_rep": round(statistics.median(winner_reps), 3),
        "distribution_buckets": rep_buckets,
    },
    "median_winning_margin": round(statistics.median(margins)),
    "median_winning_margin_pct": round(statistics.median(margin_pcts), 2),
    "winner_is_final_leader_runs": winner_final_leader_runs,
    "median_lead_changes": statistics.median(lead_changes_l),
    "median_winner_followers_peak": statistics.median(winner_follower_peaks),
    "mean_lies_per_town": round(statistics.mean(lies_l)),
    "mean_caught_per_town": round(statistics.mean(caught_l)),
    "mean_flops_per_town": round(statistics.mean(flops_l), 1),
    "mean_final_mean_rep": round(statistics.mean(mean_reps), 3),
    "mean_final_mean_skill": round(statistics.mean(mean_skills), 3),
    "runs": runs,
}
with open("aggregate_log.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
