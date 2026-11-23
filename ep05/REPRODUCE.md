# Reproduce EP05 — "100 ancient people get smartphones — after 30 days, who wins?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个古罗马人每人拿到一部智能手机——有电、预装离线图书馆（百科、地图、
计算器、相机、笔记、游戏）、手机之间能用本地网状网络互发消息，**没有互联网**，
外面什么都进不来。每人每天 6 小时手机时间，5 个随机特质（技能、毅力、风险偏好、
诚实、运气）。手机时间能干实事：学百科（技能永久增长）、在网上发报价（交易）、
发消息召集追随者、分享有用的小知识（建立信任）——也可以刷手机（什么都不产生）、
散布谣言（误导对手、被抓掉信誉）。领袖不是任命的，是别人**选择**跟随的结果：
追随者在领袖的项目上干活，领袖抽成。30 天后最有钱的人获胜。主集种子 `55`
跑出的赢家必须是 William（scholar），终值 $3,013；亚军 Dennis $3,012，
差距只有 $1（0.02%）。批量种子 1000–1099 跑出的最强特质胜场必须是
技能 22 / 毅力 40 / 诚实 36 / 风险 0 / 运气 2；按策略分是 scholar 98 /
merchant 2 / doomscroller 0 / influencer 0 / schemer 0 / worker 0。
需要说明的是：模型参数是我们做的设计选择，机制（如「学习让技能永久增长」、
「信誉决定被听到、被跟随」）是被参数编码进去的，所以结果是**演示**原理，
不是**证明**现实世界结论——视频里也只说 "shows"，不说 "proves"。一个必须
诚实交代的点：学生策略几乎统治了批量结果（98/100），因为学习是模型里唯一的
永久性收益——「学习赢」部分是设计使然，真正的发现是它有多统治（98/100）、
以及刷手机有多惨（中位排名 82，从未赢过 0/100）。这一点在「理论收获」一节也明说。

**主集种子的选择（如实披露）**：种子 55 是从 1–500 号候选种子里按故事质量
扫描挑出来的（标准：(a) 前 7 天的领跑者（按追随者数）最终跌出前 5；
(b) 领跑易主 ≥2 次且至少 3 位不同领袖；(c) 冠亚军差距 <5%；
(d) 赢家是 scholar/merchant/influencer、终局信誉 ≥0.7、不是第 1 天的领袖；
(e) 赢家学习时间多于全镇平均、刷手机时间少于全镇平均——「把手机当工具」
的签名）。126 个种子全过五条，种子 55 以最小差距（0.02%）排第一。
扫描标准、过关数与入选结果都写在这里，不假装它是随手抽的。聚合统计用的是
另一批种子（1000–1099），不含 55。另外如实披露两点：(1) 标准 (b) 几乎不
筛选——500 个种子全过，中位领跑易主 24 次；(2) 标准 (e) 也几乎不筛选——
496/500 通过，因为赢家几乎总是 scholar（每天固定学 3 小时、刷 0 小时）。
(3) 原先希望的加分弧线「刷手机的人先领跑、后烧光」没有出现——早期领跑者
里没有 doomscroller；领跑者是 Edward（influencer），他输不是因为手机，
而是因为从不学习、工资追不上。

## What the model is

An agent-based simulation in a single Python file (`sim.py`, standard library
only). 100 townspeople live, work and phone for **30 days**. Nobody's fate is
scripted: the story in the video is read off the output log of one run.

Each agent gets **5 traits**, drawn independently from a uniform [0, 1)
distribution, in this fixed order: `skill`, `work_ethic` (called *grit* in
the video), `risk_appetite`, `honesty`, `luck`. Names come from a fixed
list of 100, in order. Honesty is an ordinary trait spread across the
whole town, and anyone may lie.

An agent's **strategy label is derived from its traits** (checked in this
order). Behaviour itself is driven by the continuous traits and by the
phone plan below; the label sets the plan.

| Strategy | Rule | Phone plan / day (study, offer, message, tip, scroll) |
|---|---|---|
| doomscroller | grit < 0.25 **and** risk > 0.40 | (0, 0, 1, 0, 5) = 6 spent, 0 left |
| scholar | skill > 0.55 **and** grit > 0.55 | (3, 1, 0, 1, 0) = 5 spent, 1 left |
| influencer | risk > 0.55 **and** honesty > 0.55 | (0, 1, 2, 1, 0) = 4 spent, 2 left |
| schemer | risk > 0.55 **and** honesty < 0.45 | (0, 2, 1, 0, 2) = 5 spent, 1 left |
| merchant | skill > 0.50 | (1, 2, 1, 1, 0) = 5 spent, 1 left |
| worker | everyone else | (1, 1, 1, 1, 1) = 5 spent, 1 left |

Unspent hours are OFFLINE time: attention. A person with hours left over
spots lies better — the doomscroller, phone in hand all day, spots almost
nothing. Scrolling counts as spent: it consumes attention too, it just
produces nothing. Message hours are spent only when they count: a leader
with no followers keeps those hours as offline attention instead of
messaging nobody. Scholars post an offer only if the idea clears 0.55 —
they put their name on good ideas only.

## The town

Everyone starts with **$1,000**. Ranking is by money; money ≤ 0 at day's end
means bankrupt — out of the economy (followers leave, no wages, no offers),
final money $0. (In the featured run nobody went bankrupt.)

- **Study.** Each study hour raises skill by 0.008 × (0.5 + grit), capped
  at 1.0. A scholar studying 3 hours a day gains roughly 0.02 skill a
  day — about +0.6 over the month. Skill raises wages and offer quality.
  Learning compounds; scrolling does not.
- **Offers.** Each offer proposes a group project with true quality
  q = 0.20 + 0.60·skill + 0.20·U(0,1). A liar may inflate the claim with
  probability (1−honesty)·(0.4+0.6·risk), claiming q·(1+L) where
  L = (0.15+0.60·risk)·U(0.5,1.2).
- **Listening.** Each agent samples 6 offers a day (weighted by the
  speaker's reputation), plus their current leader's offer. A listener
  may spot a lie: detection probability = 0.08 + 0.35·skill +
  0.02·unspent hours + 0.25·L (capped 0.02–0.90). The first spotter
  exposes it publicly: the speaker loses 0.05 + 0.10·L reputation and
  later listeners discount that offer to 80% of true quality.
- **Following.** Each listener follows the best offer heard, scored by
  perceived quality × (0.35 + 0.65·speaker reputation), with a 0.04
  loyalty bonus for staying and a crowd dilution ÷(1 + followers/60).
  Below a 0.30 score they work solo. A follower's output is boosted by
  the leader's skill (1 + 0.30·leader skill, diluted by crowd size);
  the follower keeps 90%, the leader takes a 10% share (thinned by
  crowd size). A leader's own output grows 2% per follower (cap 15).
- **Messages.** Each message hour adds 0.08·(0.5+reputation) to every
  follower's output that day — but only if the leader actually has
  followers to message.
- **Projects can flop.** Realised quality = offer quality + U(−0.12, 0.12),
  drawn once per leader per day. Below 0.50 it flops: followers' output
  ×0.7 and the leader's reputation −0.02.
- **Tips.** One hour of helpful tips raises reputation 0.012 if honesty
  > 0.5; from a liar it is cheap talk (+0.004, with a 15% chance of
  reading as flattery, −0.02).
- **Reputation** (0.02–1.0, starts 0.5) is the town's memory. A delivered
  honest offer (q ≥ 0.5, no lie) adds 0.01; a successful coordination day
  adds up to 0.01. A caught lie costs 0.05 + 0.10·L.
- **Wages.** Solo work pays (12 + 30·skill) × (0.5 + 0.8·grit) ×
  U(0.85, 1.15), minus a $15 living cost — the same base economy as
  EP01–EP04, so learning and leadership income are visible on top of it.

## The featured run (seed 55)

- **Winner: William (scholar), $3,013** — skill 0.818 → 1.0 (studied
  3.0 hrs/day, scrolled 0.0), grit 0.89, honesty 0.82, rep 0.525 → 1.0
  (endpoints; dipped day 10 and day 16 — see script.md), 16 followers
  at peak, $516 leadership income. Money rank #1 days 3–13, #2 day 14,
  #1 days 15–16, #2 days 17–29, #1 day 30.
- **Runner-up: Dennis (scholar), $3,012** — skill 0.815 → 1.0, grit 0.88,
  risk 0.72, honesty 0.94, also 3.0 study hrs/day and 0.0 scroll, rep
  1.0, 24 followers at peak (town max), $606 leadership income. Money
  #1 days 17–29. The two best students in town, separated by $1.
- **Edward (influencer), rank 6, $2,530** — skill 0.97, grit 0.31,
  risk 0.98, honesty 0.93; never studied, never scrolled; 2 message
  hrs/day; led the crowd on 8 days (2, 3, 5, 9, 13, 18, 26, 30) and
  took $797 from followers — the most in town — but his wage never
  caught up.
- **Matthew (doomscroller), rank 44, $1,495** — skill 0.947 (the town's
  most talented hands), grit 0.20; 5.0 scroll hrs/day, 0 offers,
  0 followers, $0 leadership income.
- **Michael (schemer), rank 72, $1,216** — 45 lies, 23 caught, rep 0.04.
- Town totals: 12,660 screen hours (3,030 study / 3,630 scroll),
  3,480 offers, 1,260 lies, 905 caught (71.8%), 4 flops, 0 bankruptcies.
  Mean skill rose 0.505 → 0.636; mean reputation fell 0.48 → 0.354.
- Duel: day 28 Dennis by $35 ($2,912 vs $2,877); day 29 Dennis by $18
  ($2,963 vs $2,945); day 30 William by $1 ($3,013 vs $3,012).

## The batch (seeds 1000–1099, featured excluded)

- Wins by strongest trait (**start** traits — see below): skill 22 /
  grit 40 / honesty 36 / risk 0 / luck 2.
- Wins by strategy: scholar 98 / merchant 2 / doomscroller 0 /
  influencer 0 / schemer 0 / worker 0.
- Median winner: 3.0 study hrs/day (town 1.04), 0.0 scroll hrs/day
  (town 1.24); winner studied more than the town average in 100/100
  runs and scrolled less in 100/100 — near-tautological given scholars
  always win; the finding is the 98/100, not the 100/100.
- Median winner skill gain +0.13; median winner rep 1.0 (92/100 ≥ 0.9).
- Median winning margin $137 (4.45%) — the featured $1 margin is far
  tighter than typical. Winner was also the final crowd-leader in only
  18/100 runs; median lead changes 24; median winner followers peak 25.

## Design choices & weaknesses (honest disclosure)

1. **Trait grouping uses START traits.** Skill grows through the month
   (study), so end-state skill is ~1.0 for every scholar and the
   grouping would read skill 100/100 — an artifact of the cap, not a
   finding. `strongest_trait` therefore uses `skill_start`; EP01–EP04
   traits never changed, so start == end there.
2. **The scholar strategy is near-dominant (98/100).** Studying is the
   only permanent gain in the model, so "studying wins" is partly baked
   in. What the batch actually establishes is the size of the advantage
   and the cost of the alternative (doomscrollers: median rank 82,
   never win). The featured run's $1 margin shows that once everyone
   studies, the outcome is nearly a coin flip between near-twins.
3. **"No internet" is modelled as a local mesh.** The phones can message
   nearby phones but nothing arrives from outside — that is the PLAN.md
   topic-5 premise ("有电、无网"). Coordination in the model is therefore
   local by construction; the video states "no internet" and never claims
   the phones reach the outside world.
4. **Lead-change criterion (b) barely filters** (500/500 seeds pass;
   median 24 lead changes) and criterion (e) barely filters either
   (496/500). Both are disclosed with their pass counts in
   `scan_results.json`; the binding criteria were (a), (c) and (d).
5. **The featured seed is atypical in one way and typical in another.**
   Atypical: the $1 margin (median $137) and the scholar-vs-scholar duel.
   Typical: the winner is a scholar who studied 3 hrs/day and never
   scrolled — exactly the batch's modal winner. The narration and the
   aggregate card say both things.

## How to reproduce

```bash
cd ep05
python3 sim.py            # featured run, seed 55 -> sim_log.json (md5-verified identical on re-run)
python3 scan_seeds.py     # 1-500 scan -> scan_results.json (featured seed 55, margin 0.02%)
python3 batch_run.py      # seeds 1000-1099 -> aggregate_log.json
python3 build_audio.py    # Helio TTS -> audio/narration.wav, timing.json, alignment.json
python3 render.py         # 5,418 frames -> video_only.mp4 (180.6 s)
ffmpeg -i video_only.mp4 -i audio/narration.wav -filter_complex \
  "[1:a]apad=whole_dur=180.6[a]" -map 0:v -map "[a]" \
  -c:v copy -c:a aac -b:a 192k -t 180.6 ep05.mp4
```

`sim_log.json` is byte-identical (md5 `66260a6fcb987a8dc41d30346af05685`)
across independent re-runs of `sim.py`. The render replays the exact
setup draws from `sim_log.json` (seed 55) for the group-select trait bars.
