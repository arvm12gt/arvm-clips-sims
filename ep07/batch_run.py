#!/usr/bin/env python3
"""EP07 aggregate batch runner.

Runs the exact model from sim.py (same parameters: 100 agents,
$100 each, 6 free hours/day each, 30 days, granary 3,000 units losing
10% every morning, food price = 4*2000/stock capped at $60) with 100
different random seeds and tallies what happens across towns. The
featured story run (see REPRODUCE.md for the chosen seed) is NOT part
of this batch.

Seeds: 1000..1099.

Winner classification for the headline stat: by the winner's STRONGEST
trait (the maximum of their five START traits; ties broken in the order
skill, grit, risk, honesty, luck) — the same rule sim.strongest_trait
applies to the featured winner. Raw winner-strategy tallies are also
saved, so nothing is hidden by the grouping.

Headline question of this episode — hoard or share? The batch counts
wins by strategy (hoarder vs sharer vs producer), how often the winner
ate from a stockpile, how often the winner donated, and how often the
granary actually ran dry (stock below 500 / below 100 at day 30).
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
STRATS = ("hoarder", "sharer", "producer", "trader", "schemer", "worker")

runs = []
trait_wins = {t: 0 for t in TRAITS}
strat_wins = {s: 0 for s in STRATS}
winner_learn, town_learn, winner_waste, town_waste = [], [], [], []
winner_produced, town_produced = [], []
winner_food_spent, town_food_spent = [], []
winner_hungry, winner_ate_free, winner_donated, winner_hoarded = [], [], [], []
winner_skill_gain, winner_reps = [], []
margins, margin_pcts, lead_changes_l = [], [], []
lies_l, caught_l, flops_l, mean_reps, mean_skills = [], [], [], [], []
winner_learned_more_runs = winner_wasted_less_runs = 0
winner_produced_more_runs = winner_never_hungry_runs = 0
winner_ate_free_runs = winner_donated_runs = 0
winner_final_leader_runs = 0
winner_follower_peaks = []
rep_buckets = {">=0.9": 0, "0.7-0.9": 0, "0.5-0.7": 0, "<0.5": 0}
stock_d30_l, price_d30_l, starved_l, bankrupt_l = [], [], [], []
day_below_1000_l, day_below_500_l = [], []
stock_below_500_runs = stock_below_100_runs = 0

for s in SEEDS:
    log = sim.run(seed=s)
    w = log["winner"]
    trait_wins[w["strongest_trait"]] += 1
    strat_wins[w["strategy"]] += 1
    winner_learn.append(w["learn_per_day"])
    town_learn.append(log["town_avg_learn_per_day"])
    winner_waste.append(w["waste_per_day"])
    town_waste.append(log["town_avg_waste_per_day"])
    winner_produced.append(w["produced_per_day"])
    town_produced.append(log["town_avg_produced_per_day"])
    winner_food_spent.append(w["food_spent_total"] / 30.0)
    town_food_spent.append(log["total_food_spent"] / (30.0 * 100))
    winner_hungry.append(w["hungry_days"])
    winner_ate_free.append(w["ate_free_days"])
    winner_donated.append(w["donated_total"])
    winner_hoarded.append(w["hoarded_total"])
    winner_skill_gain.append(w["skill_gain"])
    winner_reps.append(w["final_rep"])
    if w["learn_per_day"] > log["town_avg_learn_per_day"]:
        winner_learned_more_runs += 1
    if w["waste_per_day"] < log["town_avg_waste_per_day"]:
        winner_wasted_less_runs += 1
    if w["produced_per_day"] > log["town_avg_produced_per_day"]:
        winner_produced_more_runs += 1
    if w["hungry_days"] == 0:
        winner_never_hungry_runs += 1
    if w["ate_free_days"] > 0:
        winner_ate_free_runs += 1
    if w["donated_total"] > 0:
        winner_donated_runs += 1
    if w["final_rep"] >= 0.9: rep_buckets[">=0.9"] += 1
    elif w["final_rep"] >= 0.7: rep_buckets["0.7-0.9"] += 1
    elif w["final_rep"] >= 0.5: rep_buckets["0.5-0.7"] += 1
    else: rep_buckets["<0.5"] += 1
    if log["final_leader"]["name"] == w["name"]:
        winner_final_leader_runs += 1
    margins.append(log["winning_margin"]); margin_pcts.append(log["winning_margin_pct"])
    lead_changes_l.append(log["lead_changes"])
    lies_l.append(log["total_lies"]); caught_l.append(log["total_caught"])
    flops_l.append(log["total_flops"]); mean_reps.append(log["final_mean_rep"])
    mean_skills.append(log["final_mean_skill"])
    winner_follower_peaks.append(w["followers_peak"])
    stock_d30_l.append(log["stock_day30"]); price_d30_l.append(log["price_day30"])
    starved_l.append(log["total_starved"]); bankrupt_l.append(log["total_bankrupt"])
    day_below_1000_l.append(log["day_stock_below_1000"])
    day_below_500_l.append(log["day_stock_below_500"])
    if log["stock_day30"] < 500:
        stock_below_500_runs += 1
    if log["stock_day30"] < 100:
        stock_below_100_runs += 1
    runs.append({
        "seed": s, "winner": w["name"], "winner_strategy": w["strategy"],
        "winner_strongest_trait": w["strongest_trait"],
        "winner_money": w["final_money"], "winner_rep": w["final_rep"],
        "winner_learn_per_day": w["learn_per_day"],
        "town_avg_learn_per_day": log["town_avg_learn_per_day"],
        "winner_waste_per_day": w["waste_per_day"],
        "town_avg_waste_per_day": log["town_avg_waste_per_day"],
        "winner_produced_per_day": w["produced_per_day"],
        "town_avg_produced_per_day": log["town_avg_produced_per_day"],
        "winner_food_spent_per_day": round(w["food_spent_total"] / 30.0, 1),
        "winner_hungry_days": w["hungry_days"],
        "winner_ate_free_days": w["ate_free_days"],
        "winner_donated_total": w["donated_total"],
        "winner_hoarded_total": w["hoarded_total"],
        "winner_skill_gain": w["skill_gain"],
        "winner_followers_peak": w["followers_peak"],
        "winning_margin": log["winning_margin"],
        "winning_margin_pct": log["winning_margin_pct"],
        "lead_changes": log["lead_changes"],
        "distinct_leaders": log["distinct_leaders"],
        "total_lies": log["total_lies"], "total_caught": log["total_caught"],
        "total_flops": log["total_flops"],
        "total_starved": log["total_starved"],
        "total_bankrupt": log["total_bankrupt"],
        "stock_day30": log["stock_day30"],
        "price_day30": log["price_day30"],
        "day_stock_below_1000": log["day_stock_below_1000"],
        "day_stock_below_500": log["day_stock_below_500"],
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
    "winner_produced": {
        "median_winner_produced_per_day": round(statistics.median(winner_produced), 2),
        "median_town_avg_produced_per_day": round(statistics.median(town_produced), 2),
        "winner_produced_more_than_town_avg_runs": winner_produced_more_runs,
    },
    "winner_food": {
        "median_winner_food_spent_per_day": round(statistics.median(winner_food_spent), 1),
        "median_town_avg_food_spent_per_day": round(statistics.median(town_food_spent), 1),
    },
    "winner_hunger": {
        "median_winner_hungry_days": statistics.median(winner_hungry),
        "winner_never_hungry_runs": winner_never_hungry_runs,
        "winner_ate_from_pile_runs": winner_ate_free_runs,
        "median_winner_ate_free_days": statistics.median(winner_ate_free),
        "winner_donated_runs": winner_donated_runs,
        "median_winner_donated_total": statistics.median(winner_donated),
        "median_winner_hoarded_total": statistics.median(winner_hoarded),
    },
    "winner_skill_gain": {
        "median_winner_skill_gain": round(statistics.median(winner_skill_gain), 3),
    },
    "winner_reputation": {
        "median_winner_rep": round(statistics.median(winner_reps), 3),
        "distribution_buckets": rep_buckets,
    },
    "granary": {
        "median_stock_day30": round(statistics.median(stock_d30_l), 1),
        "median_price_day30": round(statistics.median(price_d30_l), 2),
        "median_day_stock_below_1000": statistics.median([d for d in day_below_1000_l if d is not None]) if any(d is not None for d in day_below_1000_l) else None,
        "median_day_stock_below_500": statistics.median([d for d in day_below_500_l if d is not None]) if any(d is not None for d in day_below_500_l) else None,
        "stock_below_500_at_day30_runs": stock_below_500_runs,
        "stock_below_100_at_day30_runs": stock_below_100_runs,
        "median_starved_per_town": statistics.median(starved_l),
        "median_bankrupt_per_town": statistics.median(bankrupt_l),
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
