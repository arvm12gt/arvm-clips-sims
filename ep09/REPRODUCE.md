# EP09 — Reproduce this episode

**Topic:** A town where everyone forgets yesterday — except one person. After 30 days, is he a god or a madman?

**Model:** `sim.py` (Python stdlib only). 100 agents, $100 each, 6 free hours/day, 30 days. Each agent is rolled from the same 5 traits (skill, grit, risk, honesty, luck) and picks one of 6 strategies (gambler / schemer / grinder / scholar / trader / worker) by fixed thresholds. Every morning, the 99 non-Rememberers forget yesterday: their reputation decays 90% toward 0.5, their follow bonds dissolve, and their liar ledger clears. ONE agent — the Rememberer, chosen by `rng.randrange(100)` after the trait draws, with no trait override — remembers everything: his reputation persists, and he keeps a `known_liars` set (anyone he saw exposed, or personally detected; he detects a known liar's lies with p=0.95, and a known liar's deals/follow appeal are halved). Skill and learning are NOT memory — they persist for everyone.

**Featured seed: 39.** Re-run it:

```bash
python3 -c "import sim, json; json.dump(sim.run(seed=39), open('sim_log.json','w'), indent=1)"
```

Re-running seed 39 must reproduce `sim_log.json` exactly (same winner, same margins, same daily series). The featured run:

- **Winner: Kevin** (grinder, the Rememberer) — $1,720, rep 1.00, honesty 0.99, skill 0.371 → 1.00 (3 hrs learning/day), grit 0.95. Rank 49 on day 1 → 29 day 7 → 18 day 12 → 9 day 18 → 2 day 26 → #1 day 27, held to day 30. 0 lies told, 0 caught; 17 lies spotted, 32 known liars by name; crowd leader 14 days, followers peak 19, leadership income $480.
- **Runner-up: Jacob** (grinder) — $1,652, rep 0.512, skill 0.775 → 1.00, grit 0.98, 9 lies told, 8 caught. Money #1 on day 7 and days 9–26 — 19 days in all (Catherine took day 8). Margin: $68 (3.96%).
- **Biggest liar: Julie** (schemer) — 56 lies, 42 caught, rank 65, $390, rep 0.396, followers peak 2.
- **Top schemer: Timothy** (schemer) — 31 lies, 23 caught, rank 29, $1,054, rep 0.30.
- **Day-1 money leader: David** (grinder) — $155, skill_start 0.934, final rank 10, $1,457.
- **Duel (days 27–30):** $1,515 vs $1,508 ($7) → $1,587 vs $1,546 ($41) → $1,646 vs $1,598 ($48) → $1,720 vs $1,652 ($68). A widening gap, not a last-day flip.
- **Town totals:** 1,480 lies, 1,214 caught, 17 flops, 2 bankrupt, 19 lead changes, 15 distinct leaders, median final money $699.

## How the featured seed was chosen (scan criteria)

`scan_seeds.py` scanned seeds 1–500 and required ALL of:

- (a) the day-1 money leader finishes outside the top 5 (David → rank 10);
- (b) lead_changes ≥ 2 and distinct_leaders ≥ 3 (19 and 15);
- (c) winner's margin < 5% **and ≥ $1** — a $0 margin is a tie, not a finish (this guard was added after seed 98 was rejected: Barbara and Paul both finished at $1,749);
- (d) winner final_rep ≥ 0.52 and winner is not the day-1 crowd leader (Kevin rep 1.00; day-1 crowd leader was Kathryn);
- (e) the Rememberer finishes top 3 AND the winner is the Rememberer or the top schemer (Kevin won);
- (f) ≤ 40 bankrupt (2);
- (g) signature — Rememberer winner: lies_spotted ≥ 10 and known_liars ≥ 20 (17 and 32).

Pass counts (of 500): a 144, b 500, c 341, d 268, e 14, f 500, g 168. Shortlist: **1 seed — 39** (seed 98 was dropped by the (c) ≥ $1 guard). Ranking: Rememberer wins first → smallest margin → most lead changes → fewest bankrupt. Full scan output: `scan_results.json`.

## The 100-run batch

`batch_run.py` runs the identical model on seeds 1000–1099 (featured seed 39 excluded) and writes `aggregate_log.json`. Headline results:

| Stat | Value |
|---|---|
| Wins by strongest START trait | skill 20 · grit 67 · risk 0 · honesty 8 · luck 5 |
| Wins by strategy (raw) | grinder 93 · gambler 5 · schemer 2 · scholar 0 · trader 0 · worker 0 |
| Rememberer won / top 3 | 3 / 6 of 100 |
| Rememberer median rank / money | 58th / $550 |
| Rememberer median honesty / skill_start | 0.52 / 0.43 |
| Rememberer median lies spotted / known liars | 16 / 39 |
| Honest Rememberers (honesty ≥ 0.70) | 31 runs, won 2 |
| Dishonest Rememberers (honesty < 0.50) | 45 runs, won **0** |
| Honest + learning Rememberers (honesty ≥ 0.70 and grinder/scholar) | 8 runs, won **2**, top 3 in 3 |
| Winner learned more than town avg | 93 / 100 |
| Winner wasted less than town avg | 93 / 100 |
| Median winner skill gain | 0.13 |
| Winner rep ≥ 0.9 / 0.7–0.9 / 0.5–0.7 / < 0.5 | 2 / 0 / 82 / 16 |
| Median winning margin | $52 (3.08%) |
| Winner = final crowd leader | 5 / 100 |
| Median lead changes | 27 |
| Median winner followers peak | 8 |
| Mean lies / caught per town | 1,628 / 1,285 |
| Median biggest-liar lies | 56 |
| Mean flops per town | 31.9 |
| Median bankrupt per town | 3 |

## Atypicality disclosures (read before believing the episode)

1. **Kevin's win is uncommon.** The Rememberer won 3 of 100 towns. His $68 margin is wider than the batch median ($52). What IS typical about him: he learned 3 hrs/day (winner learned more than town in 93/100) and told 0 lies.
2. **Memory is a ledger that cuts both ways.** The Rememberer's median rank across towns is 58th — worse than random. The reason is in the design: he is the only agent whose lies are never forgotten, so a dishonest Rememberer (45/100) never won and ranks 65th at the median. The honest + learning Rememberer (8/100) won 2. Memory amplifies who you are; it does not replace an economic base. The episode states the honest conditional, not a blanket "memory wins".
3. **The grinder dominates the batch (93/100).** The headline contest of this episode is memory vs forgetting, but the batch's dominant fact is that learning beats both: the winner learned more than the town average in 93 of 100 runs. The aggregate card shows this.
4. **"Jacob led the money nineteen days in all" is counted, not consecutive.** He was money #1 on day 7 and days 9–26; Catherine took day 8. The narration says "in all". The first audio build said "twenty days" by mistake; it was caught in fact-check, re-recorded, and the audio rebuilt before render.
5. **Trait grouping uses START traits.** Skill grows through the month (learning), so end-state skill is ~1.0 for every learner. `strongest_trait` uses `skill_start`.
6. **The Rememberer's rep persists by design.** The morning reset decays every non-Rememberer's rep 90% toward 0.5, but the Rememberer's rep is untouched — he keeps the town's ledger, and his own name is in it. A lying Rememberer's rep crashes permanently. This is a deliberate design decision, documented in `sim.py`'s docstring.
7. **"He lied every day" (Timothy) is a rounded claim.** Timothy told 31 lies across 30 days — more than one a day on average. The exact figure (31) is stated in the same segment.
8. **Spotlight readouts are linearly interpolated between daily snapshots** (EP03–EP08 behaviour). Every number *stated* in the narration, duel cards, and aggregate card is an exact log value.

## Vote chain

- **EP09's topic was NOT voted for.** The EP08 comments' EP09 vote (🧠 the town that forgets vs ⏳ lying costs lifespan) was 0–0, so the default rule applied: next unused topic in PLAN.md order — #7, the town that forgets.
- **EP10 vote (end card + description):** ⏳ LYING COSTS LIFESPAN (PLAN #10, the last remaining original topic: a town where every lie costs you a day of your life) vs ⏰ ONE EXTRA HOUR (100 people each get one extra hour a day — after 30 days, who wins? — the first NEW topic beyond the original 10). **This is the first vote pair that mixes an original topic with a new one.** Most-voted wins.

## Theory

Robert Axelrod, *The Evolution of Cooperation* (1984) — tit for tat: cooperation only works if players remember the other player's last move. The episode says the simulation "shows" this pattern; it never says "proves".

## Files

- `sim.py` — the model (stdlib only)
- `batch_run.py` — the 100-run batch (seeds 1000–1099)
- `sim_log.json` — featured run (seed 39), exact reproduction target
- `aggregate_log.json` — batch results
- `scan_seeds.py`, `scan_results.json` — the featured-seed scan
- `segments.txt`, `script.md` — narration + fact-check
- `build_audio.py`, `render.py` — TTS/mastering and the v9 frame renderer
- `description.txt` — the publish description
