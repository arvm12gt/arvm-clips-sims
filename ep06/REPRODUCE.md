# Reproduce EP06 — "One rich person starts from zero against 100 poor people — after 30 days, who is richest?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个人里，99 个人每人从 100 美元开始；一个人——Richard——曾经很有钱，
破产后从 0 美元开始，但他保住了钱拿不走的东西：技能 0.95、一个全镇都信任的
名字（初始信誉 0.85）、以及对金钱运作的了解。每人每天 6 小时自由时间，5 个
随机特质（技能、毅力、风险偏好、诚实、运气）。自由时间能干实事：学习（技能
永久增长）、发交易报价、拉拢追随者、帮人建立信任——也可以浪费掉。领袖不是
任命的，是别人**选择**跟随的结果：追随者在领袖的项目上干活，领袖抽成。
这一集新增的机制是**信贷**：每天早上任何人都能凭信誉向镇银行借钱（额度 =
200 × 信誉；Richard 的旧人脉让他的额度翻倍、利息减半：5% 对 10%），借来的
钱可以投进当天的工作，回报跟着项目质量（或自己的技能）走，晚上连本带息还
上——还不上就破产。30 天后最有钱的人获胜。主集种子 `192` 跑出的赢家必须是
Eric（learner），终值 $3,341；亚军 Richard $3,339，差距只有 $1（0.04%）。
批量种子 1000–1099 跑出的最强特质胜场必须是技能 33 / 毅力 35 / 诚实 25 /
风险 0 / 运气 7；按策略分是 learner 99 / dealer 1 / waster 0 / hustler 0 /
gambler 0 / worker 0；Richard 赢 14 次、进前三 61 次。
需要说明的是：模型参数是我们做的设计选择，机制（如「学习让技能永久增长」、
「信誉决定被听到、被跟随、能借多少」）是被参数编码进去的，所以结果是**演示**
原理，不是**证明**现实世界结论——视频里也只说 "shows"，不说 "proves"。一个
必须诚实交代的点：学习者策略几乎统治了批量结果（99/100），因为学习是模型里
唯一的永久性收益——「学习赢」部分是设计使然，真正的发现是它有多统治（99/100）、
以及常见的赢家根本不借钱（中位每天借 $0，全镇平均 $38）——信贷放大的是技能，
不是凭空造钱。这一点在「理论收获」一节也明说。

**主集种子的选择（如实披露）**：种子 192 是从 1–500 号候选种子里按故事质量
扫描挑出来的（标准：(a) 第 1 天金钱榜首最终跌出前 5；(b) 领跑易主 ≥2 次且
至少 3 位不同领袖；(c) 冠亚军差距 <5%；(d) 赢家是 learner/dealer/hustler、
终局信誉 ≥0.7、不是第 1 天的领袖；(e) Richard 最终进前三；(f) Richard 至少
有一天是金钱榜首或人群领袖）。109 个种子全过六条，种子 192 以最小差距
（0.04%）排第一。扫描标准、过关数与入选结果都写在这里，不假装它是随手抽的。
聚合统计用的是另一批种子（1000–1099），不含 192。另外如实披露三点：
(1) 标准 (a) 的第一版用的是「前 7 天的人群领袖跌出前 5」——但 Richard 的
0.85 初始信誉让他 493/500 的种子里都是前 7 天的人群领袖，所以 (a) 和 (e)
永远不可能同时成立；第一版扫描短名单是空的，发现后把 (a) 改成了「第 1 天
金钱榜首跌出前 5」才重跑，改动记在 `scan_seeds.py` 里；(2) 标准 (b) 和 (f)
几乎不筛选——500 个种子全过，中位领跑易主 21 次；Richard 在 500/500 的种子
里至少有一天领跑人群或金钱榜；(3) 原先希望的弧线「Richard 早期领跑人群、
后期被金钱榜反超」确实出现了——但方式是他从第 1 天倒数第一爬上来，而不是
一开始就领跑。

## What the model is

An agent-based simulation in a single Python file (`sim.py`, standard library
only). 100 townspeople live, work and borrow for **30 days**. Nobody's fate
is scripted: the story in the video is read off the output log of one run.

Each agent gets **5 traits**, drawn independently from a uniform [0, 1)
distribution, in this fixed order: `skill`, `work_ethic` (called *grit* in
the video), `risk_appetite`, `honesty`, `luck`. Names come from a fixed
list of 100, in order. Honesty is an ordinary trait spread across the
whole town, and anyone may lie. Richard is the one fixed exception (like
Robert's fixed honesty in EP03): his traits are set, not drawn — skill
0.95, grit 0.90, risk 0.55, honesty 0.85 — because "the man who used to
be rich" is the premise, not a random draw. His luck is still drawn. His
starting reputation is 0.85 (the Rolodex); everyone else starts at 0.5.

An agent's **strategy label is derived from its traits** (checked in this
order). Behaviour itself is driven by the continuous traits and by the
day plan below; the label sets the plan.

| Strategy | Rule | Day plan / day (learn, deal, network, help, waste) |
|---|---|---|
| waster | grit < 0.25 **and** risk > 0.40 | (0, 0, 1, 0, 5) = 6 spent, 0 left |
| learner | skill > 0.55 **and** grit > 0.55 | (3, 1, 0, 1, 0) = 5 spent, 1 left |
| hustler | risk > 0.55 **and** honesty > 0.55 | (0, 1, 2, 1, 0) = 4 spent, 2 left |
| gambler | risk > 0.55 **and** honesty < 0.45 | (0, 2, 1, 0, 2) = 5 spent, 1 left |
| dealer | skill > 0.50 | (1, 2, 1, 1, 0) = 5 spent, 1 left |
| worker | everyone else | (1, 1, 1, 1, 1) = 5 spent, 1 left |

Unspent hours are OFFLINE time: attention. A person with hours left over
spots lies better — the waster, busy all day, spots almost nothing.
Wasting counts as spent: it consumes attention too, it just produces
nothing. Network hours are spent only when they count: a leader with no
followers keeps those hours as offline attention instead of rallying
nobody. Learners post a deal only if the idea clears 0.55 — they put
their name on good ideas only.

## The town

99 people start with **$100**; Richard starts with **$0**. Ranking is by
money; money ≤ 0 at day's end means bankrupt — out of the economy
(followers leave, no wages, no deals), final money $0. (In the featured
run nobody went bankrupt.)

- **Credit.** Each morning an agent may borrow up to 200 × reputation
  (Richard ×2 — the Rolodex). How much they take is risk-driven: risk >
  0.35 takes limit × (0.3 + 0.7×risk); Richard always takes the full
  limit; otherwise they borrow only in desperation (money < $30: half
  the limit). Interest 10% per day (Richard 5%), repaid at nightfall
  from money. The loan is added to money in the morning, so it can be
  invested the same day.
- **Investing.** Each agent stakes part of the day's money on the work
  they do: invest = min(money × (0.2 + 0.4×risk), $200). The return rate
  rides on the project's realised quality for followers ((q − 0.5) ×
  0.8) or on own skill for solo workers ((skill − 0.5) × 0.6). Only the
  return is added or subtracted — the stake itself is never lost as
  principal. A skilled investor on a good project profits; a bad judge
  loses the return.
- **Learn.** Each learn hour raises skill by 0.008 × (0.5 + grit), capped
  at 1.0. A learner studying 3 hours a day gains roughly 0.02 skill a
  day. Skill raises wages and deal quality. Learning compounds; wasting
  does not.
- **Deals.** Each deal proposes a group project with true quality
  q = 0.20 + 0.60·skill + 0.20·U(0,1). A liar may inflate the claim with
  probability (1−honesty)·(0.4+0.6·risk), claiming q·(1+L) where
  L = (0.15+0.60·risk)·U(0.5,1.2).
- **Listening.** Each agent samples 6 deals a day (weighted by the
  speaker's reputation), plus their current leader's deal. A listener
  may spot a lie: detection probability = 0.08 + 0.35·skill +
  0.02·unspent hours + 0.25·L (capped 0.02–0.90). The first spotter
  exposes it publicly: the speaker loses 0.05 + 0.10·L reputation and
  later listeners discount that deal to 80% of true quality.
- **Following.** Each listener follows the best deal heard, scored by
  perceived quality × (0.35 + 0.65·speaker reputation), with a 0.04
  loyalty bonus for staying and a crowd dilution ÷(1 + followers/60).
  Below a 0.30 score they work solo. A follower's output is boosted by
  the leader's skill (1 + 0.30·leader skill, diluted by crowd size);
  the follower keeps 90%, the leader takes a 10% share (thinned by
  crowd size). A leader's own output grows 2% per follower (cap 15).
- **Networking.** Each network hour adds 0.08·(0.5+reputation) to every
  follower's output that day — but only if the leader actually has
  followers to rally.
- **Projects can flop.** Realised quality = deal quality + U(−0.12, 0.12),
  drawn once per leader per day. Below 0.50 it flops: followers' output
  ×0.7 and the leader's reputation −0.02.
- **Help.** One hour of helping people raises reputation 0.012 if honesty
  > 0.5; from a liar it is cheap talk (+0.004, with a 15% chance of
  reading as flattery, −0.02).
- **Reputation** (0.02–1.0, starts 0.5; Richard 0.85) is public and is
  the town's memory. It steers who gets heard (sampling weights), who
  gets followed (follow score), network power — and the credit limit. A
  delivered honest deal (q ≥ 0.5, no lie) adds 0.01; a successful
  coordination day adds up to 0.01. A caught lie costs 0.05 + 0.10·L.
- **Wages.** Solo work pays (12 + 30·skill) × (0.5 + 0.8·grit) ×
  U(0.85, 1.15), minus a $15 living cost — the same base economy as
  EP01–EP05, so learning and leadership income are visible on top of it.

## The featured run (seed 192)

- **Winner: Eric (learner), $3,341** — skill 0.959 → 1.0 (studied 3.0
  hrs/day, wasted 0.0), grit 0.67, risk 0.13, honesty 0.74, rep 0.53 →
  1.00 (day 20) → 0.89; borrowed **$0 in 30 days**; invest return
  $1,559; leadership income $532; followers peak 20; never led the
  crowd (0 days as leader). Money rank #15 day 1, top-5 from day 3,
  #3 days 16–26, #2 from day 27, #1 day 30.
- **Runner-up: Richard (learner), $3,339** — skill 0.95 → 1.0, grit
  0.90, risk 0.55, honesty 0.85; borrowed **$11,720** ($390.6/day, every
  one of the 30 days — the most in town), interest paid $586; invest
  return $1,678; leadership income $755; followers peak 37 (town max);
  led the crowd 12 days; rep 0.85 → 1.00; 2 lies told, both caught.
  Money rank #100 day 1 ($85), #19 day 2, #7 day 3, #2 days 11–20,
  #1 days 21–24 and 26–29 (8 days), #2 day 30.
- **Raymond (learner), rank 3, $3,305** — skill 0.789 → 1.0, grit 0.99,
  risk 0.84; led the money days 4–20 (17 days); 10 lies, all 10 caught,
  rep collapsed to 0.064; borrowed $2,027; invest return $1,826.
  Day 19: Raymond ahead by $0.40 ($2,083.60 vs $2,083.20). Day 20:
  $0.20 apart ($2,190.30 vs $2,190.10). Day 21: Richard passed him by
  $6.10.
- **Ronald (hustler), rank 9, $3,023** — skill 0.98, grit 0.41, luck
  0.98; day-1 money leader ($166); led the crowd 7 days; leadership
  income $780 (town max); 0 lies; rep 1.0; borrowed $4,284.
- **John (waster), rank 99, $951** — skill 0.18, grit 0.17, luck 0.89;
  5.0 waste hrs/day, 0 deals, 0 followers; borrowed $1,852, interest
  $185; invest return $1,084 (following good projects still paid —
  his stake rode their quality, which is why he finished at $951
  instead of broke). Town median final money $1,961.
- **Aaron (gambler), rank 25, $2,446** — 59 lies, 27 caught, rep 0.03.
- **Donald (hustler), rank 39, $2,154** — best investor in town
  (invest return $1,882) and still only 39th: investing alone doesn't win.
- Town totals: $132,865 borrowed, $12,701 interest, $500,738 invested,
  $150,850 invest return, 3,360 deals, 1,257 lies, 870 caught (69%),
  5 flops, 0 bankruptcies. Mean skill rose 0.50 → 0.61; mean reputation
  fell 0.48 → 0.37.
- Duel: day 27 Richard by $34 ($3,014.30 vs $2,979.90); day 28 Richard
  by $43 ($3,141.10 vs $3,098.10); day 29 Richard by $3 ($3,231.80 vs
  $3,228.80); day 30 Eric by $1.30 ($3,340.70 vs $3,339.40 — the log's
  rounded margin is $1; the duel plates show the rounded top-5 values
  $3,341 vs $3,339, same class of artifact as EP04, documented in
  script.md).

## The batch (seeds 1000–1099, featured excluded)

- Wins by strongest trait (**start** traits — see below): skill 33 /
  grit 35 / honesty 25 / risk 0 / luck 7.
- Wins by strategy: learner 99 / dealer 1 / waster 0 / hustler 0 /
  gambler 0 / worker 0.
- **Richard: won 14/100, median final rank 3, top-3 in 61/100, top-5
  in 84/100**; median borrowed $11,550 total; median invest return
  $1,810.
- Median winner: 3.0 learn hrs/day (town 1.06), 0.0 waste hrs/day
  (town 1.23); winner learned more than the town average in 100/100
  runs and wasted less in 100/100.
- Median winner borrowed **$0/day** (town avg $38); the winner
  borrowed more than the town average in only 28/100 runs; median
  winner invest return $1,690.
- Median winner skill gain +0.125; median winner rep 1.0 (89/100 ≥ 0.9).
- Median winning margin $114 (3.24%) — the featured $1 margin is far
  tighter than typical. Winner was also the final crowd-leader in only
  16/100 runs; median lead changes 21; median winner followers peak 24.

## Design choices & weaknesses (honest disclosure)

1. **Trait grouping uses START traits.** Skill grows through the month
   (learning), so end-state skill is ~1.0 for every learner and the
   grouping would read skill ~100/100 — an artifact of the cap, not a
   finding. `strongest_trait` therefore uses `skill_start`; EP01–EP04
   traits never changed, so start == end there.
2. **The learner strategy is near-dominant (99/100).** Learning is the
   only permanent gain in the model, so "learning wins" is partly baked
   in. What the batch actually establishes is the size of the advantage
   (99/100), that the typical winner doesn't borrow (median $0/day),
   and that Richard's Rolodex buys a top-3 finish (61/100) but rarely
   the win (14/100) — because the know-how is learnable: 15 learners
   per town study the same 3 hours a day. The featured run's $1 margin
   shows how thin it is once everyone learns.
3. **The credit layer is generous by design.** Borrowing is cheap
   (10%/day, 5% for Richard) and the investment return rides on
   project quality, so a skilled borrower almost always profits —
   Richard's credit machine netted him +$1,092 ($1,678 invest return
   minus $586 interest). The honest reading is not "borrowing loses":
   it is "borrowing amplifies skill, and skill can be learned by
   people who never borrow" — which is exactly what the batch shows
   (median winner borrowed $0).
4. **Richard is the crowd's default leader.** His 0.85 starting
   reputation makes him the modal most-followed leader in 493/500
   scanned seeds. That is the Rolodex working as designed, but it
   forced a rewrite of scan criterion (a) — see above.
5. **Lead-change criterion (b) and Richard-shot criterion (f) barely
   filter** (500/500 seeds pass both; median 21 lead changes). Both
   are disclosed with their pass counts in `scan_results.json`; the
   binding criteria were (a), (c), (d) and (e).
6. **The featured seed is atypical in one way and typical in another.**
   Atypical: the $1 margin (median $114) and the winner-never-borrowed
   vs runner-up-borrowed-$11,720 contrast. Typical: the winner is a
   learner who studied 3 hrs/day and never wasted — exactly the
   batch's modal winner — and Richard finished top-3, as he does in
   61/100 runs. The narration and the aggregate card say both things.
7. **No bankruptcies in the featured run** (0/100) despite the $100
   start — wages plus investment returns kept everyone afloat. The
   $100 start still matters: the median finished at $1,961 and the
   worst (John) at $951.

## How to reproduce

```bash
cd ep06
python3 sim.py            # featured run, seed 192 -> sim_log.json (md5-verified identical on re-run)
python3 scan_seeds.py     # 1-500 scan -> scan_results.json (featured seed 192, margin 0.04%)
python3 batch_run.py      # seeds 1000-1099 -> aggregate_log.json
python3 build_audio.py    # Helio TTS -> audio/narration.wav, timing.json, alignment.json
python3 render.py         # frames -> video_only.mp4
ffmpeg -i video_only.mp4 -i audio/narration.wav -filter_complex \
  "[1:a]apad=whole_dur=<TOTAL>[a]" -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 192k -t <TOTAL> ep06.mp4
```

`sim_log.json` is byte-identical across independent re-runs of `sim.py`.
The render replays the exact setup draws from `sim_log.json` (seed 192)
plus `sim.apply_rich_override` for the group-select trait bars.
