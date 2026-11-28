#!/usr/bin/env python3
"""EP09 aggregate batch runner.

Runs the exact model from sim.py (same parameters: 100 agents,
$100 each, 6 free hours/day each, 30 days, every morning the 99
forget yesterday — rep decays 90% to 0.5, follow bonds dissolve,
crowds forgotten — and ONE agent remembers everything) with 100
different random seeds and tallies what happens across towns. The
featured story run (see REPRODUCE.md for the chosen seed) is NOT part
of this batch.

Seeds: 1000..1099.

Winner classification for the headline stat: by the winner's STRONGEST
trait (the maximum of their five START traits; ties broken in the order
skill, grit, risk, honesty, luck) — the same rule sim.strongest_trait
applies to the featured winner. Raw winner-strategy tallies are also
saved, so nothing is hidden by the grouping.

Headline question of this episode — god or madman? The batch counts
how often the Rememberer wins at all, how often they make the top 3,
and — the ledger conditional — how often they win WHEN they showed up
honest (honesty >= 0.70): memory amplifies who you are, or it does not.
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
STRATS = ("gambler", "schemer", "grinder", "scholar", "trader", "worker")

runs = []
trait_wins = {t: 0 for t in TRAITS}
strat_wins = {s: 0 for s in STRATS}
winner_learn, town_learn, winner_waste, town_waste = [], [], [], []
winner_skill_gain, winner_reps = [], []
margins, margin_pcts, lead_changes_l = [], [], []
lies_l, caught_l, flops_l, mean_reps, mean_skills = [], [], [], [], []
winner_learned_more_runs = winner_wasted_less_runs = 0
winner_final_leader_runs = 0
winner_follower_peaks = []
rep_buckets = {">=0.9": 0, "0.7-0.9": 0, "0.5-0.7": 0, "<0.5": 0}
bankrupt_l = []
rem_won_runs = rem_top3_runs = 0
rem_ranks, rem_moneys, rem_honesties, rem_skill_starts = [], [], [], []
rem_spotted, rem_known = [], []
rem_honest_runs = rem_honest_won_runs = 0
rem_dishonest_runs = rem_dishonest_won_runs = 0
rem_honest_learner_runs = rem_honest_learner_won_runs = 0
schemer_won_runs = 0
biggest_liar_lies_l = []

for s in SEEDS:
    log = sim.run(seed=s)
    w = log["winner"]
    rm = log["rememberer"]
    trait_wins[w["strongest_trait"]] += 1
    strat_wins[w["strategy"]] += 1
    winner_learn.append(w["learn_per_day"])
    town_learn.append(log["town_avg_learn_per_day"])
    winner_waste.append(w["waste_per_day"])
    town_waste.append(log["town_avg_waste_per_day"])
    winner_skill_gain.append(w["skill_gain"])
    winner_reps.append(w["final_rep"])
    if w["learn_per_day"] > log["town_avg_learn_per_day"]:
        winner_learned_more_runs += 1
    if w["waste_per_day"] < log["town_avg_waste_per_day"]:
        winner_wasted_less_runs += 1
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
    bankrupt_l.append(log["total_bankrupt"])
    biggest_liar_lies_l.append(log["biggest_liar"]["lies_told"])
    if w["strategy"] == "schemer":
        schemer_won_runs += 1
    # the Rememberer, per run
    if w["name"] == rm["name"]:
        rem_won_runs += 1
    if rm["final_rank"] <= 3:
        rem_top3_runs += 1
    rem_ranks.append(rm["final_rank"])
    rem_moneys.append(rm["final_money"])
    rem_honesties.append(rm["traits"]["honesty"])
    rem_skill_starts.append(rm["skill_start"])
    rem_spotted.append(rm["lies_spotted"])
    rem_known.append(rm["known_liars"])
    if rm["traits"]["honesty"] >= 0.70:
        rem_honest_runs += 1
        if w["name"] == rm["name"]:
            rem_honest_won_runs += 1
        if rm["strategy"] in ("grinder", "scholar"):
            rem_honest_learner_runs += 1
            if w["name"] == rm["name"]:
                rem_honest_learner_won_runs += 1
    if rm["traits"]["honesty"] < 0.50:
        rem_dishonest_runs += 1
        if w["name"] == rm["name"]:
            rem_dishonest_won_runs += 1
    runs.append({
        "seed": s, "winner": w["name"], "winner_strategy": w["strategy"],
        "winner_strongest_trait": w["strongest_trait"],
        "winner_money": w["final_money"], "winner_rep": w["final_rep"],
        "winner_learn_per_day": w["learn_per_day"],
        "town_avg_learn_per_day": log["town_avg_learn_per_day"],
        "winner_waste_per_day": w["waste_per_day"],
        "town_avg_waste_per_day": log["town_avg_waste_per_day"],
        "winner_skill_gain": w["skill_gain"],
        "winner_followers_peak": w["followers_peak"],
        "rememberer": rm["name"], "rememberer_strategy": rm["strategy"],
        "rememberer_rank": rm["final_rank"], "rememberer_money": rm["final_money"],
        "rememberer_rep": rm["final_rep"],
        "rememberer_honesty": rm["traits"]["honesty"],
        "rememberer_skill_start": rm["skill_start"],
        "rememberer_lies_spotted": rm["lies_spotted"],
        "rememberer_known_liars": rm["known_liars"],
        "rememberer_won": w["name"] == rm["name"],
        "winning_margin": log["winning_margin"],
        "winning_margin_pct": log["winning_margin_pct"],
        "lead_changes": log["lead_changes"],
        "distinct_leaders": log["distinct_leaders"],
        "total_lies": log["total_lies"], "total_caught": log["total_caught"],
        "total_flops": log["total_flops"],
        "total_bankrupt": log["total_bankrupt"],
        "biggest_liar_lies": log["biggest_liar"]["lies_told"],
        "biggest_liar_rank": log["biggest_liar"]["final_rank"],
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
    "rememberer": {
        "won_runs": rem_won_runs,
        "top3_runs": rem_top3_runs,
        "median_rank": statistics.median(rem_ranks),
        "median_money": round(statistics.median(rem_moneys)),
        "median_honesty": round(statistics.median(rem_honesties), 2),
        "median_skill_start": round(statistics.median(rem_skill_starts), 2),
        "median_lies_spotted": statistics.median(rem_spotted),
        "median_known_liars": statistics.median(rem_known),
        "honest_runs": rem_honest_runs,
        "honest_won_runs": rem_honest_won_runs,
        "dishonest_runs": rem_dishonest_runs,
        "dishonest_won_runs": rem_dishonest_won_runs,
        "honest_learner_runs": rem_honest_learner_runs,
        "honest_learner_won_runs": rem_honest_learner_won_runs,
    },
    "schemer_won_runs": schemer_won_runs,
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
    "median_bankrupt_per_town": statistics.median(bankrupt_l),
    "mean_lies_per_town": round(statistics.mean(lies_l)),
    "mean_caught_per_town": round(statistics.mean(caught_l)),
    "median_biggest_liar_lies": statistics.median(biggest_liar_lies_l),
    "mean_flops_per_town": round(statistics.mean(flops_l), 1),
    "mean_final_mean_rep": round(statistics.mean(mean_reps), 3),
    "mean_final_mean_skill": round(statistics.mean(mean_skills), 3),
    "runs": runs,
}
with open("aggregate_log.json", "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1))
