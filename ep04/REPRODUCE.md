# Reproduce EP04 — "100 people can only speak 10 sentences a day — after 30 days, who becomes the leader?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个小人住进一座小镇，每人每天只能说 10 句话，每人 5 个随机特质
（技能、毅力、风险偏好、诚实、运气）。说话要花句子，听是免费的；
话能干实事：推销项目、召集追随者、建立信任——也可以撒谎。领袖不是
任命的，是别人**选择**跟随的结果：追随者在领袖的项目上干活，领袖抽
成。30 天后最有钱的人获胜。主集种子 `5` 跑出的赢家必须是 Michael
（listener），终值 $3,081；亚军 Diane $3,053，差距只有 $27（0.89%）。
批量种子 1000–1099 跑出的最强特质胜场必须是 技能 45 / 诚实 26 /
毅力 22 / 风险 4 / 运气 3。需要说明的是：模型参数是我们做的设计选择，
机制（如「信誉决定被听到、被跟随」）是被参数编码进去的，所以结果是
**演示**原理，不是**证明**现实世界结论——视频里也只说 "shows"，不说
"proves"。一个必须诚实交代的点：批量结果里典型的赢家其实是话多的
orator（81/100，中位每天说 7.93 句），不是安静的 listener；安静者获胜
是少数路径（15/100），主集种子是按「安静者获胜」这个故事标准特意挑
出来的，不是常态。这一点在「理论收获」一节也明说。

**主集种子的选择（如实披露）**：种子 5 是从 1–500 号候选种子里按故事质量
扫描挑出来的（标准：(a) 前 7 天的领跑者最终跌出前 5；(b) 领跑易主 ≥2 次
且至少 3 位不同领袖；(c) 冠亚军差距 <5%；(d) 赢家是 listener 或 orator、
每天说话少于全镇平均、终局信誉 ≥0.7、不是第 1 天的领袖）。9 个种子全过
四条，种子 5 以最小差距（0.89%）排第一。扫描标准、过关数与入选结果都
写在这里，不假装它是随手抽的。聚合统计用的是另一批种子（1000–1099），
不含 5。另外如实披露两点：(1) 标准 (b) 几乎不筛选——500 个种子全过，
中位领跑易主 18 次；(2) 原先希望的加分弧线「大嗓门先领跑、后烧光」在
500 个种子里一次都没出现（早期领跑者是 loudmouth 的种子数为 0），原因
见「设计弱点」一节；我们试过一个补救参数（谎言识别随天数学习，见下）
但效果不佳又改回去了，没有为凑弧线硬调参数。

## What the model is

An agent-based simulation in a single Python file (`sim.py`, standard library
only). 100 townspeople talk, work and follow for **30 days**. Nobody's fate is
scripted: the story in the video is read off the output log of one run.

Each agent gets **5 traits**, drawn independently from a uniform [0, 1)
distribution, in this fixed order: `skill`, `work_ethic` (called *grit* in
the video), `risk_appetite`, `honesty`, `luck`. Names come from a fixed
list of 100, in order. Unlike EP03 there is no designated honest one:
honesty is an ordinary trait spread across the whole town, and anyone
may lie.

An agent's **strategy label is derived from its traits** (checked in this
order). Behaviour itself is driven by the continuous traits and by the
speech plan below; the label sets the plan. One labelling choice is
deliberate and disclosed: **listener is checked before orator** — what
makes a listener is how little they speak, not how little they know.
A skilled, honest, low-risk person IS a listener in this town (one
selective pitch a day), not an orator (two pitches, two rallies, two
trust-talks). The label follows behaviour, and the log's sentences/day
lets anyone check it.

| Strategy | Rule | Speech plan / day |
|---|---|---|
| loudmouth | risk > 0.60 **and** honesty < 0.45 | 4 pitches, 1 rally, 1 trust-talk = 10 sentences (0 left) |
| listener | honesty > 0.60 **and** risk < 0.40 | 1 pitch, 1 rally, 0 trust-talk = 3 sentences (7 left) |
| orator | skill > 0.55 **and** honesty > 0.55 | 2 pitches, 2 rallies, 2 trust-talks = 8 sentences (2 left) |
| schemer | risk > 0.55 **and** skill > 0.50 | 2 pitches, 1 rally, 1 trust-talk = 6 sentences (4 left) |
| worker | everyone else | 1 pitch, 1 rally, 1 trust-talk = 4 sentences (6 left) |

Two quiet-person rules, both part of the premise: (1) **when the quiet
one speaks, the room goes quiet** — a pitch is sampled for listening
with weight (0.20 + speaker reputation) × (4 / pitches the speaker
made today), so one pitch from a listener gets four times the hearing
of each of a loudmouth's four; total airtime per speaker is roughly
equal, quality decides. (2) **A listener speaks only when it is worth
saying** — they pitch only if the idea's quality clears 0.55, otherwise
they save the 2 sentences (they stay unspent, i.e. attention). Nobody
else filters. Rallies are also spent only when they count: a rally
sentence is spent only if the agent had followers yesterday, otherwise
it stays unspent instead of shouting at nobody.

## The town

Everyone starts with **$1,000**. Ranking is by money; money ≤ 0 at day's end
means bankrupt — out of the economy (followers leave, no wages, no
pitches), final money $0. (In the featured run nobody went bankrupt.)

**Daily cycle** (in order): speech phase (pitches + trust-talk) →
listening & following → work phase (wages, coordination, rallies,
flops) → bankruptcy check and snapshot.

**Wages.** Solo work pays (12 + 30·skill) × (0.5 + 0.8·grit) × U(0.85, 1.15),
minus a $15 living cost — the same base economy as EP01–EP03, so
leadership income is visible on top of it.

**Pitches.** Each pitch proposes a group project with true quality
q = 0.20 + 0.60·skill + 0.20·U(0,1). A liar may inflate the claim: with
probability (1 − honesty)·(0.4 + 0.6·risk) they claim q·(1 + L) with
L = (0.15 + 0.60·risk)·U(0.5, 1.2), capped at a claim of 1.20.

**Listening & detection.** Listening is free but attention is limited:
each agent samples 6 pitches a day (weights above), plus their current
leader's pitch if they have one. A lie may be spotted: detection
probability = clamp(0.08 + 0.35·listener skill + 0.02·unspent sentences
+ 0.25·L, 0.02, 0.90). The FIRST listener to spot a lie exposes it
publicly: the speaker's reputation drops by 0.05 + 0.10·L, the pitch is
perceived at 80% of its true quality by everyone after, and the lie
counts as caught. A small lie nobody spots still pays.

**Following.** Each listener follows the best pitch they heard, scored by
perceived quality × (0.35 + 0.65·speaker reputation), divided by
(1 + followers/60) — a big crowd dilutes the score a little — plus a
0.04 loyalty bonus for staying with their current leader. Below a
score of 0.30 they work solo. Following is an economic choice: a
follower's output is wage × (1 + 0.30·leader skill / (1 + followers/30))
— the leader's attention spreads thin as the crowd grows — times the
rally multiplier, and the follower keeps 90% of it while the leader
takes a 10% share, thinned the same way (10% / (1 + followers/20)).
Following a skilled, honest leader with a small crowd pays better than
solo work; following a loud fraud in a huge crowd pays worse, so crowds
split instead of piling onto one person forever. A leader's own output
also grows with their following (+2% per follower, capped at 15).

**Rallies.** Each rally sentence (only spent when the leader has
followers) adds 0.08·(0.5 + reputation) to every follower's output
that day.

**Projects can flop.** The followed project's realised quality is its
pitch quality plus execution noise U(−0.12, 0.12), drawn once per leader
per day — the whole crowd shares one outcome. Below 0.50 it flops:
followers' output ×0.7 and the leader's reputation −0.02. Great
projects never flop; mediocre ones and liars' inflated ones sometimes do.

**Trust-talk.** One sentence of honest talk raises reputation by 0.012
if honesty > 0.5. From a liar it is cheap talk: +0.004, with a 15%
chance of being read as flattery (−0.02).

**Reputation** (0.02–1.0, starts at 0.5) is public. It steers who gets
heard (sampling weights), who gets followed (follow score) and rally
power. A delivered honest pitch (q ≥ 0.5, no lie) adds 0.01; a
successful coordination day adds up to 0.01. A caught lie costs
0.05 + 0.10·L. In the featured run the town's mean reputation fell from
0.46 on day 1 to 0.24 on day 30 — the town as a whole got more
distrustful, while the honest few climbed to 0.93–1.00.

## The featured run (seed 5)

- Winner: **Michael** (listener) — $3,081. Runner-up: **Diane**
  (listener) — $3,053 (margin $27, 0.89%). Michael's traits: skill 98,
  grit 87, risk 29, honesty 96, luck 54. He spoke 2.97 sentences/day
  (town average 4.82), pitched 30 times, told 1 lie (caught once),
  ended with reputation 0.93, followers peaking at 25, and $605 of
  leadership income. He was the town's most-followed leader on exactly
  one day — day 30.
- Michael's arc: rank 4 on day 1 → 2 on day 3 → 1 on day 14 → back to
  2nd for fourteen straight days (days 15–28) → 1st on days 29–30. The
  eternal second place who wins on the last day. His reputation rose
  from 0.51 to 0.93 overall, with one dip on day 3 (0.53 → 0.45) — the
  day his single lie was caught. (Correction 2026-11-23: an earlier
  draft said it "never fell"; the log shows the day-3 dip.)
- **Diane** (listener): skill 100, grit 70, risk 5, honesty 84, luck 22.
  Never told a lie in 30 pitches, reputation 1.00, followers peaking at
  34 (the town's most), led 5 days, $688 leadership income — and still
  lost by $27. She led on day 29 with 34 followers; Michael took the
  lead (25 followers) and the money on day 30.
- **Mary** (orator): skill 92, grit **3**, honesty 94. She led the town
  for 19 days (days 4–16, 18, 20–21, 23, 25, 28), peaked at 33
  followers, and collected $1,116 of leadership income — the town's
  most — but finished **8th** ($2,519). She had the crowd but never did
  the work: with grit 0.03 her own wage barely covered the $15 living
  cost. The leader who couldn't earn.
- The loud side: **Julie** (loudmouth, skill 92, grit 15) spent 9.10
  sentences/day, told 51 lies (17 caught), finished 43rd ($1,508) with
  reputation 0.02 and a followers peak of 4. **Ronald** (loudmouth) is
  the cautionary tale with talent: skill 96, grit 97, luck 89 — the
  most gifted loudmouth in town — told 56 lies (24 caught), reputation
  0.074, followers peak 4, finished 7th ($2,520) on wages alone.
  **Melissa** (loudmouth, honesty 0.00) told 115 lies, 44 caught,
  finished 55th ($1,369). **Margaret** (schemer, skill 99, grit 96)
  told 25 lies, reputation 0.02, finished 4th ($2,662) — skill kept her
  rich, lies kept her friendless.
- Lead changes: 16 across 7 distinct leaders (Margaret → Frank →
  Maria → Mary → Sandra → Diane → Michael), with Mary and Diane trading
  the lead nine times in the last twelve days (days 19–30).
- Town totals: 14,451 sentences spoken, 5,515 pitches, 2,775 lies told,
  1,377 caught (about half), 4 project flops, 0 bankruptcies.
  Strategy counts: loudmouth 25, orator 8, schemer 7, listener 16,
  worker 44.

## The batch (seeds 1000–1099, featured seed excluded)

- Wins by strongest trait: **skill 45, honesty 26, grit 22, risk 4,
  luck 3**.
- Wins by strategy (raw): orator 81, listener 15, worker 4, loudmouth 0,
  schemer 0. Loudmouths never win; schemers never win.
- Winner sentences: median winner 7.93 sentences/day vs median town
  average 4.52 — the typical winner talks MORE than the town, not less.
  The winner spoke less than the town average in only 19 of 100 runs.
- Winner reputation: median 1.0; buckets ≥0.9: 85 runs, 0.7–0.9: 11,
  0.5–0.7: 2, <0.5: 2.
- Median winning margin $266 (8.3%). The winner was also the
  most-followed agent on day 30 in only 27 of 100 runs — wealth and
  followership usually diverge; the featured run is one of the 27 where
  they coincide. Median lead changes 18; median winner followers peak 27.
- Per town on average: 2,283 lies, 1,175 caught, 7.4 flops; day-30 mean
  reputation 0.29.

## The seed scan (seeds 1–500; full table in scan_results.json)

Criteria: (a) the modal leader of days 1–7 finishes outside the top 5
by money; (b) lead changes ≥ 2 and distinct leaders ≥ 3; (c) winning
margin < 5%; (d) winner is listener/orator, spends fewer sentences/day
than the town average, final reputation ≥ 0.7, and was not the day-1
leader. Pass counts of 500: (a) 98, (b) 500, (c) 207, (d) 50.
Shortlist (all four): 9 seeds, ranked by smallest margin, then most
lead changes, then fewest winner sentences/day.

| Seed | Winner | Strategy | Margin | Lead changes | Early leader (final rank) | Sent/day |
|---|---|---|---|---|---|---|
| **5** | **Michael** | listener | 0.89% | 16 | Mary, orator (8th) | 2.97 |
| 432 | Margaret | listener | 1.34% | 14 | Emily, orator (9th) | 2.97 |
| 58 | Kenneth | listener | 2.01% | 23 | Justin, schemer (9th) | 2.97 |
| 197 | Steven | listener | 2.18% | 19 | Rachel, worker (25th) | 2.93 |
| 221 | Rachel | listener | 2.27% | 20 | Deborah, orator (7th) | 2.93 |
| 329 | Barbara | listener | 2.31% | 21 | Larry, orator (10th) | 2.97 |
| 123 | Jack | listener | 2.99% | 22 | Victoria, orator (7th) | 2.97 |
| 397 | Jerry | listener | 3.38% | 20 | Jacqueline, orator (10th) | 2.97 |
| 367 | Tyler | listener | 3.63% | 23 | Mary, listener (19th) | 2.97 |

All 9 shortlist winners are listeners at ~2.9 sentences/day — the scan
selected for the quiet-winner story, and that is exactly what it found.
The featured seed is the closest finish of the nine.

**A design tweak that was tried and reverted (disclosed):** the first scan
showed the early leader is a loudmouth in 0 of 500 seeds — loudmouths
never lead even the early game, because a lie is usually exposed within
a day or two and reputation craters. We tried a "town learns to spot
lies" rule (detection at 45%, then 25%, strength on day 1, ramping to
full by day 10) to give loudmouths an early window. It barely moved the
needle (early loudmouth leader: 1 of 50 seeds either way) while making
listener wins rarer (3/50 vs 5/50) and median margins wider (8.2% vs
~5%), so it was reverted in full. The shipped model has no learning
curve. The honest consequence: the episode's loud-vs-quiet contrast
lives in sentence counts and final ranks (Julie 9.1/day, rank 43;
Michael 2.97/day, rank 1), not in an early loudmouth reign.

## Theory the data genuinely supports

Candidate theory: **cheap talk and costly signalling** (Crawford &
Sobel 1982 on cheap talk; Spence 1973 on signalling). Talk is cheap to
produce, so a claim is only credible when the speaker has something at
stake — here, a public reputation that detection can destroy. Does the
data illustrate it? **Yes, narrowly, and the batch is the evidence:**
loudmouths win 0 of 100 towns, 85 of 100 winners end with reputation
≥ 0.9, and about half of all lies are caught — inflated claims stop
paying once the town can check them and remembers who lied. But the
honest qualification matters for the video: the theory as usually told
("the quiet one wins because talk is cheap") is NOT what the batch
shows. The typical winner is a talkative orator (7.93 sentences/day),
not a quiet listener — what wins is **honest, skilled speech**, and
silence only wins when it is selective (a listener pitches only good
ideas) on top of top skill (the featured Michael: skill 0.98). Saying
"silence wins" would overclaim; saying "in a town where lies get
caught and remembered, the people who end up followed are the ones
whose words turn out true" is what the numbers support. And the model
illustrates the mechanism it was built with — it does not prove the
theory about the real world.

## Design weaknesses (flagged, not hidden)

- **Loudmouths never lead, even early (0/500).** The premise image — a
  loud talker who burns their budget by noon — is present as a failure
  (rank 43, reputation 0.02) but not as an early reign. A slower
  reputation update or delayed public exposure might produce it, but
  that would be a different model; the tried fix is documented above.
- **Lead changes are very frequent (median 18).** Criterion (b) passes
  in all 500 seeds, so it is not really a filter — the leadership is
  churny by construction, and a "stable reign then a fall" arc has to be
  found by the other criteria, as in seed 5 (Mary's 19 days).
- **The winner is usually not the final leader (73/100).** Money and
  followership diverge because wages and follower bonuses also pay. The
  episode's "who becomes the leader" framing and its "who ends up
  richest" scoring are two different crowns that coincide only
  sometimes.
- **Schemer is a near-empty label (1–7 agents per town).** The orator
  and listener checks run first, so few agents land in it. Harmless for
  the story (no schemer is featured), but the label is thinner than the
  cast suggests.
- **Flops rarely bite the narrative.** The featured run had 4 flops, none
  with ≥ 8 followers, so no flop event appears in the log — the flop
  mechanism matters in the batch (7.4 per town) but not in the featured
  story.
- **The featured seed is selected, not typical.** Seed 5 is one of the 9
  in 500 where a quiet listener wins a close finish; the batch says the
  usual winner is a talkative orator. The video must present Michael's
  win as what happened in this town, with the aggregate card showing the
  usual outcome — not as "silence always wins".

## How to reproduce

```bash
cd ep04
python3 sim.py         # writes sim_log.json — winner must be Michael, $3,081,
                       # runner-up Diane $3,053, margin 0.89%
python3 batch_run.py   # writes aggregate_log.json — wins must read
                       # skill 45 / honesty 26 / grit 22 / risk 4 / luck 3,
                       # orator 81 / listener 15 / worker 4 / loudmouth 0 / schemer 0
python3 scan_seeds.py  # re-runs the 1-500 seed scan (~3 min), rewrites
                       # scan_results.json — featured seed must still be 5
```

Deterministic: CPython's `random.Random(seed)` with the draw order above.
No third-party packages, no network, no clock dependence.

**Reproducibility check (done 2026-11-23):** `sim_log.json` was saved,
`python3 sim.py` was re-run fresh, and the two logs compared byte-for-byte
identical (same winner, same final numbers, same events list).
