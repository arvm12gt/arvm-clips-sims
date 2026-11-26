# Reproduce EP07 — "A city loses 10% of its resources every day — after 30 days, who is still standing?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个人每人从 100 美元开始，住在一座只有一个粮仓的城市里。粮仓一开始有
3000 单位粮食，**每天早上少 10%**，谁也补不回来——只能靠大家白天生产、晚上
吃饭来维持。粮价跟着粮仓走：满的时候一顿饭约 3 美元，见底时涨到 22 美元。
每人每天 6 小时自由时间，5 个随机特质（技能、毅力、风险偏好、诚实、运气）。
自由时间能干实事：学习（技能永久增长）、发交易报价、拉拢追随者、帮人建立
信任——也可以浪费掉。领袖不是任命的，是别人**选择**跟随的结果：追随者在领袖
的项目上干活，领袖抽成。三种策略回答紧缩的方式不同：**囤积者**趁粮价便宜买
粮存起来（私人粮堆上限 12 单位，粮价低于 8 美元才买）；**分享者**在粮仓低于
800 时自掏腰包买粮捐给粮仓（每天 2 单位，换信任）；**生产者**种粮最多
（1.6 倍产量）。连续 3 天吃不上饭就饿死出局。30 天后最有钱的人获胜。主集种
子 `19` 跑出的赢家必须是 Rebecca（hoarder），终值 $1,385；亚军 Michael
（sharer）$1,385，差距不到 1 美元（原始差值 $0.20）。批量种子 1000–1099 跑
出的最强特质胜场必须是技能 34 / 毅力 39 / 诚实 24 / 风险 2 / 运气 1；策略胜
场必须是囤积者 46 / 分享者 42 / 生产者 4 / 交易者 1 / 骗子 0 / 普通人 7。

## How to reproduce

```bash
cd ep07
python3 sim.py            # featured run, seed 19 -> sim_log.json
python3 scan_seeds.py     # seeds 1-500, story-quality scan -> scan_results.json
python3 batch_run.py      # seeds 1000-1099, 100 towns -> aggregate_log.json
python3 build_audio.py    # Helio TTS segments -> audio/narration.wav + audio/timing.json
python3 render.py         # PIL frames -> video_only.mp4
ffmpeg -y -i video_only.mp4 -i audio/narration.wav -c:v copy -c:a aac -b:a 192k \
  -shortest ep07.mp4      # mux (narration is the master clock; video is 5 s longer)
```

`sim.py` is stdlib only. The featured seed is **19** (picked by `scan_seeds.py`,
criteria below). Re-running `sim.py` must reproduce Rebecca $1,385 /
Michael $1,385 exactly (deterministic `random.Random(19)`).

## The model (all parameters in `sim.py`)

- **Granary**: starts 3,000 units; every morning `stock *= 0.90` (−10%/day, the
  premise). Production adds during the day; eating takes out at night.
- **Food price**: set each morning from post-decay stock:
  `price = clamp(4 * 2000 / stock, $2, $60)`. Full granary ≈ $2.70/meal;
  day-30 stock ≈ 450 → ≈ $19/meal. (Tuning note 2026-11-26: REF 1500 left
  the day-30 price at ~$9 — no bite; REF 3000+ starved 30–60% of the town;
  REF 2000 gives a ~7x price rise with 20–35 bankrupt per town.)
- **Production**: `produce = (0.45 + 0.9*skill) * (0.5 + 0.8*grit) * mult`,
  mult: producer 1.6, hoarder 1.2, sharer 1.0, trader 0.8, schemer 0.8,
  worker 1.0. (Tuned 2026-11-26: 0.6/1.2 produced ~175/day and the stock
  settled near 750 — no crunch; 0.45/0.9 gives ~95/day and the stock
  falls 3,000 → ~450.) Hungry agents produce and earn 0.7x.
- **Hoarding**: each morning a hoarder with a pile below 12 buys up to 4
  units if the price is under $8 and they can afford it. The pile is eaten
  first, free. **Piles do not decay** — only the granary loses 10%. That
  asymmetry is the hoarder's edge, and the takeaway line ("The granary
  lost ten percent every morning. She never did.") states it.
- **Sharing**: at night, a sharer with money > $150 buys 2 units at the
  day's price and puts them in the granary, gaining reputation +0.02.
- **Eating**: at night, in random order, each agent eats one unit — from
  their pile first (free), else buys one from the granary at the day's
  price (if money and stock allow), else goes hungry. Hungry 3 days in a
  row = starved out (bankrupt, money $0).
- **Wages**: `(12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)`, minus a
  $15 living cost — the same base economy as EP01–EP06. Food is bought on
  top of the living cost.
- **Learn / deals / listening / following / reputation / flops**: the same
  machinery as EP03–EP06 (see `sim.py` docstring). No credit, no
  investing — that was EP06's mechanic. Producers post a deal only if its
  quality clears 0.55 (they put their name on good ideas only).
- **Strategies** (checked in order): hoarder (risk < 0.40, grit > 0.45);
  sharer (honesty > 0.60, grit > 0.50); producer (skill > 0.55, grit >
  0.55); trader (risk > 0.55, honesty > 0.45); schemer (risk > 0.55,
  honesty < 0.45); worker (everyone else).

## Seed scan (seeds 1–500, `scan_seeds.py`)

Criteria, all required: (a) day-1 money leader finishes outside the top 5;
(b) lead changes ≥ 2 and distinct leaders ≥ 3; (c) winning margin < 5%;
(d) winner is producer/sharer/hoarder/trader, rep ≥ 0.7, not the day-1
crowd leader; (e) ≥ 3 starved, granary fell below 1,000, day-30 stock <
600; (f) ≤ 30 starved and ≤ 40 bankrupt (not a massacre); (g) winner has
a strategy-specific scarcity signature (hoarder hoarded ≥ 8, sharer
donated ≥ 10, producer produced ≥ 35, trader never hungry). Ranking:
smallest margin, then most lead changes, then fewest starved.
Pass counts (of 500): a 204, b 500, c 178, d 352, e 489, f 500, g 484.
Shortlist: 41 seeds. Featured seed **19**: Rebecca (hoarder) $1,385 vs
Michael (sharer) $1,385, margin 0.02%, 15 lead changes, early leader
Larry (sharer, final rank 8), 29 starved / 33 bankrupt, stock day-30
400.8, price day-30 $21.76, Rebecca hoarded 21 / ate free 21 / donated 0 /
produced 49.2.

## Featured run (seed 19) — the story, with receipts

- **Larry** (sharer): day-1 money leader ($152), rank #1 days 1–11, donated
  32 meals, rank #2 days 12–17, #3 days 18–21, faded to #8 ($1,176) by
  day 30. The town's first leader, forgotten by the end.
- **Michael** (sharer): money rank #1 days 12–29 (18 days), crowd leader
  13 days, followers peak 31, donated 32 meals, leadership income $805,
  day-29 lead $53, day-30 $1,385.0 — second by $0.20.
- **Rebecca** (hoarder): rank 19 day 1 → #3 from day 22, never led the
  crowd (0 days as leader), hoarded 21 units, ate free 21 days, food
  spent $262 all month (Michael: $911), day-30 $1,385.2 — wins by less
  than a dollar. Skill 0.82 → 1.0, honesty 0.98, rep 0.952, 0 lies.
- **Edward** (hoarder): #3 ($1,381), also hoarded 21 / ate free 21, crowd
  leader days 1–3. The top three are separated by $4.
- **Cheryl** (worker): #4 ($1,361), rep 1.0, never hoarded or donated.
- **The growers**: Charles, Eric and Timothy grew the most food in town
  (78.8 / 81.4 / 78.9 units) and finished #5 / #6 / #7 — with reputations
  0.02 / 0.034 / 0.048 and followers peaks 2 / 0 / 0. They also lied the
  most (11 / 23 / 22 times, caught 10 / 19 / 17). The episode states both
  facts side by side (theory card) without claiming farming caused the
  distrust — their lies did that. Cut from the narration to hold the
  180 s duration cap.
- **The crunch**: first hungry faces day 11 (3 people); first starved
  Kenneth, day 13 (food $10/meal); stock 3,000 → 1,055 (day 10) → 557
  (day 20) → 401 (day 30); price $2.96 → $7.61 → $15.46 → $21.76; 29
  starved, 33 bankrupt, median final money $205.
- **The duel**: day 27 Michael by $106 ($1,388 vs $1,282); day 28 by $102
  ($1,403 vs $1,301); day 29 by $53 ($1,386 vs $1,333); day 30 Rebecca
  $1,385.2 vs Michael $1,385.0. Michael's money fell $1 on the last day;
  Rebecca's rose $51.

## Aggregate (seeds 1000–1099, featured excluded)

- Wins by strongest trait: skill 34 / grit 39 / honesty 24 / risk 2 / luck 1.
- Wins by strategy: hoarder 46 / sharer 42 / producer 4 / trader 1 /
  schemer 0 / worker 7. Hoarding beats sharing 46–42 — nearly a tie.
- Winner never went hungry: 100/100 runs. Winner grew more food than the
  town average: 98/100. Median winner produced 1.73 units/day vs town
  0.92. Winner ate from a pile: 46/100. Winner donated: 42/100.
- Median winner rep 0.998 (≥0.9 in 70/100). Median winning margin $133
  (8.35%) — the featured $0.20 margin is far tighter than typical.
- Granary at day 30 (median): 449 units left, food $19.29/meal; below
  1,000 on day 12 (median), below 500 on day 25; 72/100 runs ended below
  500; 0/100 ended below 100. Median starved 15/town, bankrupt 23/town.
- Winner was also the final crowd leader in only 14/100 runs. Median
  lead changes 23. Mean lies 1,344/town, caught 904.

## Atypicality — what the featured run is and isn't

Rebecca's hoarder win is the modal outcome (46/100), and her never-hungry
run matches the batch exactly (100/100 winners never hungry). But her
margin ($0.20) is far tighter than the median $133, and her 29-starved
town is harsher than the batch median (15 starved). The narration never
claims her margin is typical; the aggregate card carries the median.
Hoarders re-buy: Rebecca hoarded 21 units against a pile cap of 12 — she
filled the pile twice, buying while the price was under $8 (early days),
eating from it, and topping it up while it was still cheap.

## Vote chain — an honest note

EP05's description offered the EP07 vote as 🍀 max-luck vs 🧠 forgetful
town; it came back 0–0, so EP07 took the next topic in PLAN.md order
(#9, the shrinking city) by the standing default rule. EP06's end card
and description then offered the EP08 vote as 🏙️ city vs ⏳ lying-costs-
lifespan — but the city became EP07 itself, so that pair is moot. The
🍀/🧠 pair is therefore rolled forward: EP07's end card and description
carry it as the EP08 vote. Nothing about the chain is hidden; the vote
counts (0–0, verified 2026-11-26 ~09:26) are in the parent chat's record.

## Production notes

- **Duration cap (new, EP06 lesson)**: EP06 ran 196.1 s and YouTube
  classified it as a regular video, not a Short. EP07's narration is 398
  words (EP04: 415 / 175.4 s; EP05: 448 / 180.6 s); total runtime must be
  ≤180 s, target ~175 s. The median-survivor line and the day-22 rank
  beat were cut at script stage to hold the cap; the duel was never
  touched.
- **Rounding artifact (day 30)**: the log's canonical winning margin
  rounds to $0 (raw gap $0.20 on the 0.1-rounded daily arrays); the duel
  plates show the rounded end-of-day top-5 values ($1,385 vs $1,385).
  The narration says "less than a dollar", which is exactly true of the
  raw gap. Same class as EP04's day-29 $3/$4 and EP06's day-30 $1/$2.
- **Trait grouping uses START traits**: skill grows through the month, so
  end-state skill is ~1.0 for every learner and the grouping would read
  skill ~100/100. `strongest_trait` uses `skill_start`.
- **Spotlight readouts are linearly interpolated** between daily snapshots
  (EP03–EP06 behaviour). Every *stated* number (narration, duel cards,
  aggregate card) is an exact log value. Followers counts use the nearest
  daily snapshot (step function).
- **Starved vs broke**: the spotlight shows "STARVED OUT" for agents
  whose `starved` flag is set, "WENT BROKE" for money bankruptcy — EP07
  has both (29 starved, 4 broke by money in the featured run).
