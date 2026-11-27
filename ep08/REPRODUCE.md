# Reproduce EP08 — "One person with max luck against 99 ordinary people — after 30 days, can luck beat effort?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个人每人从 100 美元开始，每人 5 个随机特质（技能、毅力、风险偏好、
诚实、运气）。其中一个人抽到了**满格运气 1.00**（全镇运气最高的那个人），
其他 99 个人保留自己抽到的普通运气。每天早上命运来敲门：运气越好，撞上
横财（ found money / 意外之财）的概率越高、金额越大；运气越差，越可能
撞上倒霉事（账单、搞砸的交易）而丢钱。横财是运气唯一的作用通道——它不碰
工资、不碰技能、不碰交易质量，所以批量结果能干净地回答「光靠运气能不能赢」。
其余经济与 EP01–EP07 同款：学习（技能永久增长）、发交易报价、拉拢追随者、
帮人建立信任——也可以浪费掉。领袖不是任命的，是别人**选择**跟随的结果：
追随者在领袖的项目上干活，领袖抽成。30 天后最有钱的人获胜。主集种子 `492`
跑出的赢家必须是 John（scholar，同时也是幸运儿），终值 $2,433；亚军 Lisa
（grinder）$2,350，差距 83 美元（3.41%）。批量种子 1000–1099 跑出的最强特质
胜场必须是技能 17 / 毅力 25 / 诚实 16 / 风险 0 / 运气 42；策略胜场必须是
赌徒 9 / 骗子 2 / 苦干者 77 / 学者 12 / 交易者 0 / 普通人 0；幸运儿赢 11 次、
进前三 20 次。

## How to reproduce

```bash
cd ep08
python3 sim.py            # featured run, seed 492 -> sim_log.json
python3 scan_seeds.py     # seeds 1-500, story-quality scan -> scan_results.json
python3 batch_run.py      # seeds 1000-1099, 100 towns -> aggregate_log.json
python3 build_audio.py    # Helio TTS segments -> audio/narration.wav + audio/timing.json
python3 render.py         # PIL frames -> video_only.mp4
ffmpeg -y -i video_only.mp4 -i audio/narration.wav -c:v copy -c:a aac -b:a 192k \
  -af apad=whole_dur=TOTAL -t TOTAL ep08.mp4   # mux (see note below — NEVER -shortest)
```

`sim.py` is stdlib only. The featured seed is **492** (picked by `scan_seeds.py`,
criteria below). Re-running `sim.py` must reproduce John $2,433 /
Lisa $2,350 exactly (deterministic `random.Random(492)`).

**Mux trap (EP07 lesson, do not repeat):** a mux with `-shortest` cuts the
5 s silent end card — the file comes out 5 s short. Mux with
`apad=whole_dur=TOTAL` + `-t TOTAL` where TOTAL = narration + 5.0 s;
the narration is the master clock and the video is 5 s longer.

## The model (all parameters in `sim.py`)

- **The lottery**: 5 trait draws per agent in fixed order
  (skill, grit, risk, honesty, luck). Whoever drew the highest luck has
  it set to exactly 1.00; everyone else keeps their drawn luck. The
  renderer replays the same draws + override (asserted in `render.py`).
- **Fortune (every morning, before work)**: a lucky break with
  p = 0.05 + 0.45*luck^2 pays (10 + 50*luck^2) * U(0.5, 1.5); an unlucky
  break with p = 0.10*(1-luck) costs 5 + 15*U(0,1). Bankrupt agents draw
  nothing. Luck acts CONVEXLY on purpose: the gap between max luck
  (1.00) and ordinary luck (0.50) must be real. (Tuning note 2026-11-27:
  linear luck left the Lucky One winning 1/30 runs, top-3 1/30 — the
  edge was a rounding error next to a grinder's wage + leadership
  income. Convex V3 gives Lucky One wins ~11/100, top-3 ~20/100: luck
  matters, but rarely wins alone — which is the episode's honest answer.)
  Expected values: the Lucky One ~0.50 breaks/day at ~$60 — about $900
  over the month. An ordinary agent (luck ~0.5) ~0.16/day at ~$22 —
  about $110.
- **Wages**: `(12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)`, minus a
  $15 living cost — the same base economy as EP01–EP07.
- **Learn / deals / listening / following / reputation / flops**: the same
  machinery as EP03–EP07 (see `sim.py` docstring). No credit, no
  investing — that was EP06's mechanic. No granary, no food — that was
  EP07's mechanic. Scholars post a deal only if its quality clears 0.55
  (they put their name on good ideas only).
- **Strategies** (checked in order): gambler (risk > 0.55, honesty >
  0.45); schemer (risk > 0.55, honesty < 0.45); grinder (grit > 0.60);
  scholar (skill > 0.60); trader (honesty > 0.60, grit > 0.50); worker
  (everyone else).

## Seed scan (seeds 1–500, `scan_seeds.py`)

Criteria, all required: (a) day-1 money leader finishes outside the top 5;
(b) lead changes ≥ 2 and distinct leaders ≥ 3; (c) winning margin < 5%;
(d) winner rep ≥ 0.7, not the day-1 crowd leader; (e) the Lucky One
finishes top 3 AND the winner is the Lucky One or the top grinder — so
the finale is luck vs effort; (f) ≤ 40 bankrupt (not a massacre);
(g) winner has a signature: Lucky-One winner won ≥ $500 windfalls,
top-grinder winner gained ≥ 0.20 skill, else winner won ≥ $300 windfalls
or gained ≥ 0.20 skill. Ranking: Lucky-One wins first, then smallest
margin, then most lead changes, then fewest bankrupt.
Pass counts (of 500): a 271, b 500, c 192, d 393, e 88, f 500, g 302.
Shortlist: 5 seeds. Featured seed **492**: John (scholar, the Lucky One)
$2,433 vs Lisa (grinder, top grinder) $2,350, margin 3.41%, 25 lead
changes, early leader Michelle (gambler, final rank 8), 1 bankrupt,
John windfalls $861 on 14 days.

## Featured run (seed 492) — the story, with receipts

- **John** (scholar, the Lucky One): rank 48 day 1 → #3 day 7 → money #1
  from day 18, never gave it back. Skill 0.877 → 1.0, grit 0.28, honesty
  1.00, luck 1.00. Windfalls $861 on 14 days (biggest $86), 0 mishaps,
  0 lies, rep 1.0, leadership income $778, followers peak 26, crowd
  leader 3 days (20, 24, 26). Day-30 $2,433.
- **Lisa** (grinder, top grinder): rank 23 day 1 → #2. Skill 0.572 →
  1.0, grit 0.92, honesty 0.95, luck 0.74. Learned 3.0 hrs/day.
  Windfalls $266 on 7 days (biggest $56). Rep 1.0, leadership income
  $590, followers peak 23, crowd leader 3 days. Day-30 $2,350 — lost by
  $83. She closed the gap every day at the end: $180 (day 27) → $139
  (day 28) → $117 (day 29) → $83 (day 30).
- **Michelle** (gambler): day-1 money leader ($208), luck 0.96. Held
  money #1 on days 1–8 and 10–13 (12 days). Windfalls $809 on 15 days
  (biggest $77). But 34 lies, 18 caught, rep 0.02, followers peak 1.
  Final rank 8 ($1,896). Almost as lucky as John — and nobody trusted her.
- **Cheryl** (grinder): the most windfalls in town — $1,081 on 18 days
  (biggest $83), luck 0.96. Skill 0.18 → 1.0 (learned 3.0 hrs/day).
  Rep 0.15, followers peak 0, days as leader 0. Final rank 6 ($2,043).
  Luck without trust doesn't convert.
- **Carolyn** (grinder): skill 0.969, money #3 ($2,333), crowd leader
  many days (3, 12, 14, 16, 19, 21). **Scott** (grinder): money #4
  ($2,167), crowd leader many days. **Steven** (grinder): skill 0.995,
  windfalls $616, rep 0.038, money #5 ($2,165).
- **The duel**: day 27 John $2,251 vs Lisa $2,071 ($180); day 28 $2,344
  vs $2,205 ($139); day 29 $2,397 vs $2,280 ($117); day 30 $2,433 vs
  $2,350 ($83). Crowd leaders those days: Benjamin (20), Scott (20),
  Olivia (17), Benjamin (23).
- **The counterfactual (arithmetic, not a re-run)**: John $2,433 − $861
  = $1,572; Lisa $2,350 − $266 = $2,084; $2,084 − $1,572 = $512. Take
  away the windfalls and Lisa wins by $512. Money has no other feedback
  channel in this sim except bankruptcy (neither finalist was near it),
  so the ranking counterfactual is exact — but it is arithmetic on final
  totals, not a re-simulation. Stated on the theory card and takeaway
  card.
- **Town totals**: windfalls $22,772 on 617 agent-days; mishaps $1,330
  on 104 agent-days; median final money $972; 1 bankrupt; 25 lead
  changes; 8 distinct leaders.

## Aggregate (seeds 1000–1099, featured excluded)

- Wins by strongest trait: skill 17 / grit 25 / honesty 16 / risk 0 / luck 42.
- Wins by strategy: gambler 9 / schemer 2 / grinder 77 / scholar 12 / trader 0 / worker 0.
- The Lucky One: won 11/100, top-3 20/100, median rank 11.5, median windfall $926, median skill_start 0.54.
- The Mauboussin conditional (computed, does NOT pop): when the Lucky One also showed up skilled (skill_start ≥ 0.70), they won 5 of 31 runs (16%) vs 11/100 overall — so the batch does NOT support "luck decides among the skilled" as a strong claim. The honest aggregate answer is simpler: luck helps (winner beat the town on windfalls in 85/100; median winner windfall $790 vs town $222), but effort usually wins (grinder 77/100; winner learned more than town average in 89/100). The narration and theory card do not claim the conditional.
- Median winning margin $169 (7.0%) — the featured $83 is tighter than typical.
- Winner rep ≥ 0.9 in 79/100. Winner was also the final crowd leader in only 6/100 runs. Median lead changes 25.

## Atypicality — what the featured run is and isn't

John's Lucky-One win (11/100) is uncommon but not rare, and his $83
margin is tighter than the batch median ($169). His windfall total
($861) is near the batch median for a Lucky One ($926). His skill_start
(0.877) is high — the highest starting skill in town — which is why the
Mauboussin framing fits THIS run even though the batch conditional is
weak: in this town, the two finalists were both skilled and honest by
the end (John skill 1.0 / rep 1.0; Lisa skill 1.0 / rep 1.0), and the
$83 gap between them was the windfall gap ($861 vs $266). The narration
never claims his win is typical; the aggregate card carries the batch.

## Vote chain — an honest note

EP07's EP08 vote (🍀 max-luck vs 🧠 forgetful town) came back 0–0
(verified 2026-11-27 ~09:26: 2 comments, both the channel's own, no
replies), so EP08 takes the next topic in PLAN.md order (#6, max luck)
by the standing default rule. The 🧠/⏳ pair rolls forward: EP08's end
card and description carry it as the EP09 vote (🧠 forgetful town vs
⏳ lying costs lifespan). Nothing about the chain is hidden.

## Production notes

- **Duration cap (EP06 lesson)**: EP06 ran 196.1 s and YouTube
  classified it as a regular video, not a Short. EP08's narration is 379
  words (EP07: 398 / 167.28 s); total runtime TBD s (ffprobe, target
  ~175 s, hard cap 180 s).
- **Rounding artifact (day 30)**: none material — the duel plates show
  the log's rounded end-of-day top-5 values, which subtract exactly to
  $180 / $139 / $117 / $83.
- **Trait grouping uses START traits**: skill grows through the month, so
  end-state skill is ~1.0 for every learner and the grouping would read
  skill ~100/100. `strongest_trait` uses `skill_start`.
- **Spotlight readouts are linearly interpolated** between daily snapshots
  (EP03–EP07 behaviour). Every *stated* number (narration, duel cards,
  aggregate card) is an exact log value. Followers counts use the nearest
  daily snapshot (step function).
- **center_fit guard (new in EP08)**: `render.py` splits an overflowing
  aggregate line at the " · " separator into two centered lines instead
  of drawing it clipped off the frame edges (EP07's aggregate line
  clipped at 1082 px before it was shortened by hand).
- **Header readouts (new in EP08)**: left = cumulative town windfalls
  (WIND $), right = the Lucky One's money (LUCKY $), gold when the Lucky
  One is money #1.
