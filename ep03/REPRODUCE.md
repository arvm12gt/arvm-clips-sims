# Reproduce EP03 — "100 people in a town. 99 lie whenever it pays. 1 never lies. 30 days — who ends up richest?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个小人住进一座小镇，每人 5 个随机特质（技能、毅力、风险偏好、诚实、运气）。
本集的前提是人为设定的（视频里也明说「我们锁定了一个刻度」）：其中 1 人被指定为
诚实者，诚实度设为 1.0（永远说真话、从不策略性赖账）；其余 99 人的诚实度 =
原始抽签 × 0.30（很低，撒谎只要划算就撒）。诚实者的其他 4 个特质都是普通抽签
——他不比别人更聪明、更努力或更幸运。经济里有工资、买卖（可撒谎抬价、买家可
花钱验货、事后败露要退款+罚款）、公开信誉（决定接单量与被验货概率）和 3 天期
贷款（可赖账、败露毁信誉）。任何人都可以用下面的种子和命令一键复现：主集种子
`445` 跑出的赢家必须是 Robert、终值 $6,005；批量种子 1000–1099 跑出的最强特质
胜场必须是 诚实 48 / 技能 33 / 风险 9 / 毅力 7 / 运气 3。需要说明的是：模型参数
是我们做的设计选择，机制（如「信誉带来订单流」）是被参数编码进去的，所以结果
是**演示**原理，不是**证明**现实世界结论——视频里也只说 "shows"，不说 "proves"。

**主集种子的选择（如实披露）**：种子 445 是从 1–500 号候选种子里按故事质量扫描
挑出来的（标准：诚实者进前 3、有早期跌落再后期爬升的弧线、至少一位中盘领跑者
最终跌出前 3、领跑易主 ≥3 次、冠亚军差距小）。扫描标准与入选结果都写在这里，
不假装它是随手抽的。聚合统计用的是另一批种子（1000–1099），不含 445。

## What the model is

An agent-based simulation in a single Python file (`sim.py`, standard library
only). 100 townspeople trade, work and lend for **30 days**. Nobody's fate is
scripted: the story in the video is read off the output log of one run.

Each agent gets **5 traits**, drawn independently from a uniform [0, 1)
distribution, in this fixed order: `skill`, `work_ethic` (called *grit* in
the video), `risk_appetite`, `honesty_raw`, `luck`. Names come from a fixed
list of 100, in order. **The premise dial**: after the trait draws, one agent
(index drawn from the same seeded RNG) is designated the honest one and their
honesty is set to exactly 1.0; everyone else's effective honesty is
`honesty_raw * 0.30`. The video states this openly ("we fixed one dial").

An agent's **strategy label is derived from its traits** (checked in this
order). Behaviour itself is driven by the continuous traits; the label sets
the colour, the deal-seeking weight and a small wage bonus for workers.

| Strategy | Rule | Deal weight |
|---|---|---|
| honest | the designated agent | 1.0 |
| con artist | risk > 0.55 **and** skill > 0.55 | 1.4 |
| hustler | risk > 0.62 | 1.2 |
| trader | skill > 0.55 | 1.1 |
| worker | everyone else (wage ×1.05) | 0.9 |

## The town

Everyone starts with **$1,000**. Ranking is by money; money ≤ 0 at day's end
means bankrupt — out of the economy, final money $0. (In the featured run
nobody went bankrupt; across the batch the honest one went bankrupt 0 times.)

**Daily cycle** (in order): wages and living cost → loans due are settled →
new loans are written → deals run all day → bankruptcy check and snapshot.

**Wages.** Daily wage = (12 + 30·skill) × (0.5 + 0.8·grit) × U(0.85, 1.15),
minus a $15 living cost.

**Deals.** About 300 deal attempts per day, scaled by the town's trust:
attempts = 300 × (0.60 + 0.55 × mean reputation of active agents) — as trust
rots, the market thins. The seller is drawn with probability weighted by
(0.30 + reputation)^1.15 × strategy deal weight. The buyer is a random other
active agent with money > $60.

- True value V = (25 + 95·seller skill) × U(0.7, 1.3). The seller fronts the
  goods' cost, 68 % of V, so deal size is capped by both sides' capital:
  V ≤ (seller money × 0.75) / 0.68 and V ≤ (buyer money × 0.85) / (1 + Lmax),
  where Lmax is the seller's maximum lie factor. Deals with V < $10 are skipped.
- **The lie.** An honest seller claims exactly V. A liar claims V × (1 + L)
  with L = (0.10 + 0.75·risk) × U(0.4, 1.1).
- **Verification.** The buyer verifies with probability
  p = clamp(0.06 + 0.38·(1 − seller reputation) + 0.26·buyer skill + 0.08·L,
  0.02, 0.90), paying a verification cost of 5 % of the claim (min $2).
  - Lie found: the buyer walks away with probability 0.45; otherwise the sale
    completes at the TRUE price. The seller's reputation drops by 0.05 + 0.10·L.
  - Truthful: the sale completes at V; the seller's reputation rises by 0.025.
- **No verification.** The buyer pays the claim and resells the goods at
  V × (0.90 + 0.28·buyer skill). A completed deal with nothing caught nudges
  the seller's reputation up by 0.004 (a smooth liar can look fine for a
  while). A lie is still discovered afterwards with probability
  0.06 + 0.38·L + 0.22·buyer skill: the seller refunds the overpayment plus a
  fine of 30 % of the overpayment (the fine is burned), and their reputation
  drops by 0.16.

**Reputation** (0.02–1.0, starts at 0.5) is public. It steers deal flow
(seller weights, above), verification probability, loan access and loan
prices. In the featured run the town's mean reputation collapsed from 0.50
to 0.03 within about a week and never recovered; the honest one's reputation
reached 1.00 on day 10 and was the town's only perfect score.

**Loans.** 26 attempts per day: a lender with money > $400 lends a random
other agent $60–$220 (capped at 30 % of the lender's money) for 3 days at a
per-day rate of 0.03 + 0.16 × (1 − borrower reputation). Lenders refuse a
notorious borrower (reputation < 0.18) with probability 0.7. At maturity:
the honest one repays in full whenever they can; a liar defaults with
probability clamp(0.10 + 0.45·(1 − honesty) + 0.25·underwater share, 0, 0.90).
A default becomes public with probability 0.8 and costs the borrower 0.18
reputation; repaying on time adds 0.02.

**The only asymmetries in the code** are the premise itself: the honest
one's lie factor is always 0 and they never default strategically. They
verify as a buyer by the same formula, face the same capital caps, earn the
same wages and can be sold lemons like anyone else (in the featured run the
town's lies cost them dearly on day 4: $1,372 → $877, rank 92).

## The featured run (seed 445)

- Winner: **Robert** (the honest one) — $6,005. Runner-up: **Sarah** —
  $5,716 (margin $289). Robert's traits: skill 58, grit 60, risk 63,
  honesty 100, luck 30 — deliberately ordinary.
- Robert's arc: rank 17 on day 3 → **92 on day 4** ($877) → reputation 1.00
  on day 10 → rank 2 from day 21 → leads day 28 ($5,332 vs Sarah's $5,312,
  a $20 margin) → Sarah retakes day 29 ($5,539 vs $5,515, $24) → Robert
  wins day 30. He sold 204 deals (the town's most), was verified 31 times
  and found clean every time, repaid 7 of 7 loans, never defaulted.
- Sarah (con artist): skill 99 — the town's most skilled — grit 82, risk 59,
  honesty 2, luck 57. She lied on all 80 of her deals, was caught 53 times,
  kept $1,357 of lie profit, finished with reputation 0.02 — and still
  finished 2nd. She led days 17–27 and again on day 29.
- Patrick (con artist): skill 96, grit 0. Caught on day 1 claiming $160 for
  goods worth $105; led days 4–15 anyway; finished 4th ($4,755).
- Justin (con artist): grit 96, luck 92. Led exactly one day (day 16);
  finished 3rd ($4,764).
- Town totals: 5,529 lies told, 3,894 caught (verified pre-sale or
  discovered post-hoc), 131 loan defaults, 0 bankruptcies.

## The batch (seeds 1000–1099, featured seed excluded)

- Wins by strongest trait: **honesty 48, skill 33, risk 9, grit 7, luck 3**.
  (When the honest one wins, their strongest trait is honesty by
  construction — 1.0 beats any other draw.)
- Wins by strategy (raw): honest 48, con artist 49, trader 3, hustler 0,
  worker 0.
- The honest one: won 48, top-3 55, top-10 62, bankrupt 0; median final
  rank 2; median final money $5,262; median final reputation 1.0.
- The winner also held the town's highest final reputation in exactly
  48 of 100 runs — the same 48 the honest one won.
- Median winning fortune $5,650. Per town on average: 5,518 lies, 3,873
  caught, 127 defaults; day-30 mean reputation 0.032.

## How to reproduce

```bash
cd ep03
python3 sim.py         # writes sim_log.json — winner must be Robert, $6,005
python3 batch_run.py   # writes aggregate_log.json — wins must read
                       # honesty 48 / skill 33 / risk 9 / grit 7 / luck 3
```

Deterministic: CPython's `random.Random(seed)` with the draw order above.
No third-party packages, no network, no clock dependence.
