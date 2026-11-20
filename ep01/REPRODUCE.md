# Reproduce EP01 — "100 people, $10,000 each, 30 days, no rules"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个小人，每人 5 个随机特质（技能、勤奋、风险偏好、诚实、运气），策略由特质
按固定规则推出；每天依次发生偷窃、各自赚钱/下注、借贷、结算破产。任何人都可以用
下面的种子和命令一键复现：主集种子 `20261120` 跑出的赢家必须是 Ann、$69,836，
每日全部 100 人的余额都应与存档的 `sim_log.json` 逐项一致；批量种子 1–100 跑出的
原型胜场必须是 43 / 41 / 11 / 4 / 1。需要说明的是：模型参数是我们做的设计选择，
机制（如「破产风险」）是被参数编码进去的，所以结果是**演示**原理，不是**证明**
现实世界结论——这一点视频里也只说 "shows"，不说 "proves"。

## What the model is

An agent-based simulation in a single Python file (`sim.py`, standard library
only). 100 agents, each starting with **$10,000**, living in a closed town for
**30 days**. Nobody's fate is scripted: the story in the video is read off the
output log of one run.

Each agent gets **5 traits**, drawn independently from a uniform [0, 1)
distribution, in this fixed order: `skill`, `work_ethic`, `risk_appetite`,
`honesty`, `luck`. Names come from a fixed list of 100, in order.

An agent's **strategy is derived from its traits** by fixed rules (checked in
this order):

| Strategy | Rule |
|---|---|
| thief | honesty < 0.25 **and** risk > 0.55 |
| gambler | risk > 0.78 |
| builder | skill > 0.62 **and** risk > 0.35 |
| lender | honesty > 0.65 **and** skill > 0.45 |
| worker | everyone else |

Each day runs four phases in order: **theft → daily actions → lending →
bookkeeping** (peaks, bankruptcy flags, daily ranking snapshot).

## Key parameters (taken directly from `sim.py`)

| Parameter | Value |
|---|---|
| Start money / days | $10,000 / 30 |
| **Living cost** | **$95 per day, everyone, every day** (also while jailed) |
| Worker income | (140 + 260·skill) × (0.4 + work_ethic) × U(0.85, 1.15), plus safe interest of 0.15 %/day on the balance |
| Lender income | (120 + 200·skill) × (0.4 + work_ethic) × U(0.85, 1.15), plus lending (below) |
| Builder wage | (80 + 140·skill) × (0.4 + work_ethic) |
| **Builder business bet** | stake = balance × (0.10 + 0.25·risk); **win probability = 0.30 + 0.38·skill + 0.14·luck**; win → +stake × U(0.25, 1.00); lose → −stake × U(0.35, 0.90) |
| Gambler wage | 60 × work_ethic |
| **Gambler bet** | stake = balance × (0.15 + 0.45·risk); **jackpot probability = 0.06 + 0.10·luck → +2.2 × stake**; otherwise roll < 0.46 → +0.4 × stake; otherwise −stake × U(0.5, 1.0) |
| Thief wage | 50 × work_ethic |
| **Theft** | targets the richest other agent holding > $500; steals target_balance × U(0.04, 0.12) × (0.5 + luck); **catch probability = 0.16 + 0.25 × (1 − skill)**; **caught → fine = min(balance, $1,200 + U(0, $800)) and 3 jail days** (no actions in jail, living cost still applies) |
| **Loans** | each lender with ≥ $1,500 lends once a day to a random builder/gambler (balance > $200, not jailed): amount = min(18 % of lender balance, $600 + U(0, $1,400)); **interest 6 % flat, 1-day term**; borrower swing = U(−0.45, +0.55) + 0.18·borrower skill, applied to the amount; **default probability = 0.08 + 0.35 if swing < −0.15 + 0.30 × (1 − borrower honesty)**; default → lender loses the principal, otherwise principal + interest is repaid |
| Bankruptcy | balance ≤ $0 → flagged bankrupt that day; the agent takes no further actions |

## Seeds

- **Featured (story) run: seed 20261120** → `sim_log.json`
- **Aggregate batch: seeds 1–100** (the featured seed is *not* in the batch) → `aggregate_log.json`

## Run it yourself

Requirements: Python 3 (developed and verified on CPython 3.12.3),
**standard library only** — no pip installs.

```bash
cd ep01                 # the folder containing sim.py
python3 sim.py          # writes sim_log.json, prints a summary
python3 batch_run.py    # writes aggregate_log.json (100 runs)
```

Exact reproduction relies on CPython's `random` module: for a fixed seed, its
`random()`, `uniform()` and `shuffle()` sequences are stable across CPython 3
versions, so you should get **bit-for-bit identical results**.

## What you should get

**Featured run (`python3 sim.py`)**

- Winner: **Ann — $69,836** (builder), beating Ronald ($66,115) by **$3,721**
- Daniel: 7 jackpots, $44,514 on day 3, finishes 16th
- Benjamin (skill 1.00, the town's most skilled): bankrupt on **day 17**, finishes 90th
- Teresa (work_ethic 1.00, the hardest worker): leads on day 9, finishes 15th with $25,442
- `sim_log.json` contains all 100 agents' balances for all 30 days — a diff
  against the archived copy should be empty

**Batch (`python3 batch_run.py`)** — winner archetypes over 100 fresh towns.
Classification is trait-first, in this priority order: genius (winner skill
≥ 0.90) → workhorse (winner work_ethic ≥ 0.90) → gambler (winner strategy =
gambler) → quiet builder (winner strategy = builder) → other.

- Archetype wins: **quiet builders 43 · geniuses 41 · workhorses 11 · gamblers 4 · other 1**
- Raw winner strategies (undisguised): builder 93 · gambler 5 · thief 2 · worker 0 · lender 0
- The single most-skilled agent of each town won only **4 of 100** runs and went bankrupt in **8 of 100**
- Median winning fortune: **$51,416**

## Honest assumptions note

The parameters above are **design choices**, made before any run: the
mechanisms the episode talks about (risk of ruin, compounding ownership, luck
dominating short races) are *encoded by construction* — a gambler who stakes
15–60 % of everything daily *can* be ruined, a builder's edge *is* the
skill-weighted win formula. So the results **illustrate** these principles;
they do not **prove** anything about the real world, and the narration only
ever says the simulation "shows" them. Further simplifications: traits are
uniform and independent (real people's aren't), wages/interest/jackpots inject
money into the town while theft and loans only move it around, and there are
no taxes, prices or inflation. One town is one sample — which is exactly why
the episode also runs the town 100 times and reports the aggregate.
