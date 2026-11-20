# Reproduce EP02 — "100 people wash up on a desert island. Only 10 tools. 30 days — who thrives?"

## 中文摘要

这一集的实验是一个真实运行的 agent-based 模型（`sim.py`），不是编出来的剧情：
100 个小人被冲上荒岛，每人 5 个随机特质（技能、毅力、风险偏好、诚实、运气），
策略由特质按固定规则推出；岛上只有 10 件工具，随机发给 10 个人。每天依次发生
工具租赁、白天劳作（采集/钓鱼/打猎/建屋/休息/救治）、晚餐分配、食物腐败、夜间偷窃、
夜晚暴露与死亡结算。任何人都可以用下面的种子和命令一键复现：主集种子 `42`
跑出的赢家必须是 Dorothy、兴旺分 151.5；批量种子 1000–1099 跑出的最强特质胜场
必须是 技能 54 / 诚实 15 / 运气 15 / 毅力 12 / 风险 4。需要说明的是：模型参数是
我们做的设计选择，机制（如「分工与共享降低死亡率」）是被参数编码进去的，所以
结果是**演示**原理，不是**证明**现实世界结论——视频里也只说 "shows"，不说
"proves"。

## What the model is

An agent-based simulation in a single Python file (`sim.py`, standard library
only). 100 castaways on one island for **30 days**, with only **10 tools**
between them. Nobody's fate is scripted: the story in the video is read off
the output log of one run.

Each agent gets **5 traits**, drawn independently from a uniform [0, 1)
distribution, in this fixed order: `skill`, `work_ethic` (called *grit* in
the video), `risk_appetite`, `honesty`, `luck`. Names come from a fixed list
of 100, in order. Starting health is 85 + 15·U(0, 1).

An agent's **strategy is derived from its traits** by fixed rules (checked in
this order):

| Strategy | Rule |
|---|---|
| thief | honesty < 0.25 **and** risk > 0.55 |
| leader | skill ≥ 0.72 **and** honesty ≥ 0.60 (founds a camp) |
| hoarder | honesty < 0.40 **and** work_ethic ≥ 0.55 |
| loner | risk ≥ 0.72 |
| cooperator | honesty ≥ 0.52 (joins a camp, shares fully) |
| survivor | everyone else (joins a camp if there is room) |

**Camps**: each leader founds a camp of at most 9 (leader included).
Cooperators and survivors join a random camp with room; hoarders, loners and
thieves stay solo. Camp members pool food (keeping a 15 % personal stash of
their own catch), share tools and shelter, share water duty, and gather with
a ×1.08 coordination bonus while their leader lives.

## The island

**The 10 tools** (one each, dealt to 10 distinct random agents at the start):
axe, saw, fishing net, hook set, knife, rope, cooking pot, firestarter,
tarp, medicine kit.

| Tool | Effect |
|---|---|
| axe | hunting success +0.08; building ×1.5 |
| saw | building ×1.6 |
| fishing net | fishing yield ×1.9 |
| hook set | fishing yield ×1.45 (also what a renter gets) |
| knife | hunting success +0.12; stolen amount ×1.3 |
| rope | building ×1.25 |
| cooking pot | with a firestarter: daily food need drops to 0.80 (vs 0.90 fire only, 1.00 raw) |
| firestarter | cooked food (need 0.90, or 0.80 with pot); night exposure ×0.7; food spoilage 8 % instead of 14 % |
| tarp | instant shelter level 2 for the holder (and their camp) |
| medicine kit | holder can spend the day *tending* (heals the camp's weakest member +9); resting with a kit heals +4 extra |

**Daily cycle** (in order): lost tools wash up (50 % found by a random living
agent) → tool rental → daytime actions → gathered food lands (camp members
stash 15 %, pool the rest) → evening meal → spoilage → night theft → night
exposure / recovery / deaths → commons regenerate → daily snapshot.

**Effort and needs.** Daily effort E = (8 + 6·grit) × (0.35 + 0.65·health/100).
Fetching water costs 2.0 effort solo, 0.8 per member in a camp; an agent too
weak to fetch water loses 6 health. Action costs: forage 4, fish 5, hunt 6,
build 5, tend 4, rest 0. Leftover effort (≥ 3) goes to building (if shelter
< 4) or extra foraging.

**Gathering and the commons.** Three shared stocks deplete with use and
regenerate daily: forage (start 700, cap 800, +30/day), fish (450, 550,
+22/day), game (300, 380, +12/day). Yields scale with the stock level
(stock / (stock + 150) for forage, stock / (stock + 120) for fish).

| Action | Yield |
|---|---|
| forage | (1.3 + 2.2·skill) × U(0.6, 1.35) × stock factor (×0.5 on storm days) |
| fish | (1.0 + 2.4·skill) × U(0.6, 1.3) × stock factor × tool bonus; impossible on storm days |
| hunt | success p = 0.22 + 0.33·skill + 0.18·luck (+knife/axe); success → U(3.5, 6.5) food; injury p = 0.07 + 0.10·risk → −U(6, 14) health |
| build | shelter progress += (0.5 + skill) × tool bonuses × 0.34 (level = progress, cap 5) |
| tend | the camp's weakest member +9 health (medicine-kit holder only) |
| rest | +6 health (+4 more with a medicine kit) |

**Camp role assignment** (each day): the weakest rest (health < 35); the
medicine-kit holder tends if anyone is under 72 health; net/hook holders
fish; axe/saw holders build while camp shelter < 4; in the first 6 days half
the camp builds while shelter < 4; high-skill members (≥ 0.55) mostly fish,
sometimes hunt; the rest forage. Solo agents follow their strategy: loners
hunt while healthy, hoarders gather steadily, thieves forage lightly and
steal at night, everyone builds early and rests when weak.

**Trade.** One simple form: a solo agent with ≥ 2.5 food and skill ≥ 0.5
and no fishing gear can rent a solo holder's net/hook set for the day —
0.5 food changes hands, the renter fishes with the ×1.45 hook bonus that
day. One renter per holder per day.

**Meal, spoilage, theft, night.**
- Meal: everyone needs 1.0 food (0.90 with fire, 0.80 with fire + pot).
  Camp members eat from the pool in equal shares; if a share falls short,
  the member dips into their personal stash before going hungry. Going
  hungry costs 9 × (shortfall fraction) health.
- Spoilage: stored food (pools and personal stores) loses 14 % nightly,
  8 % with fire access — there is no refrigeration on the island.
- Theft (night): each thief steals from the richest pool or solo store:
  min(store, U(1.0, 3.5) × (0.6 + 0.6·luck)), ×1.3 with a knife. Catch
  probability = 0.16 + 0.22 × (1 − skill), **+0.15 when robbing a camp**
  (more eyes on the stores). Caught → beaten for U(8, 15) health and 60 %
  of the thief's own stash is confiscated back to the victim.
- Night exposure: health drain = max(0, 5.5 − 1.3 × shelter level), ×0.7
  with fire access, ×2 on storm days (storm probability 0.13/day). Fed and
  watered agents recover +2.5. **Health ≤ 0 is death.** A dead camp member's
  tools stay with the camp; a dead solo agent's tools wash up and may be
  found (50 % per day).

**Thriving score** (what the video ranks by), for living agents:
`health + 5 × effective stored food + 10 × shelter level`, where a camp
member's effective food is their personal stash plus their per-capita share
of the pool. Dead agents score 0.

## Seeds

- **Featured (story) run: seed 42** → `sim_log.json`. The seed was chosen
  from a documented scan of candidate seeds for story quality (late lead
  change, a fallen early leader, a dramatic solo death); the run itself was
  never altered — see the assumptions note.
- **Aggregate batch: seeds 1000–1099** (the featured seed is *not* in the
  batch) → `aggregate_log.json`

## Run it yourself

Requirements: Python 3 (developed and verified on CPython 3.12),
**standard library only** — no pip installs.

```bash
cd ep02                 # the folder containing sim.py
python3 sim.py          # writes sim_log.json, prints a summary
python3 batch_run.py    # writes aggregate_log.json (100 runs)
```

Exact reproduction relies on CPython's `random` module: for a fixed seed,
its sequences are stable across CPython 3 versions, so you should get
bit-for-bit identical results.

## What you should get

**Featured run (`python3 sim.py`, seed 42)**

- Winner: **Dorothy — thriving score 151.5** (camp leader; honesty 1.00,
  the most honest agent on the island; gathered 98 food, the most of
  anyone). Runner-up: **Matthew — 148.5**. Winning margin: **3.0 points**.
- Dorothy's camp (9 people) gathered 470 food in total — the most of any
  camp — and **all 9 members survived**.
- Diane led days 3–7 (183 points on day 6) and finished 10th. Kathryn
  peaked at 186 on day 8 — the highest score anyone reached — and
  finished 17th. Matthew led on days 20–21, slid to 14th by day 28, and
  leapt to 2nd on day 30.
- Sarah (work_ethic 1.00, the island's hardest worker, a solo hoarder) was
  the first to die, on **day 8**.
- **32 of the 100 died.** Every loner (12) and every hoarder (10) died;
  3 of 13 thieves survived; **all 65 camp members survived**.
- The game stock was hunted down from 300 to its 12-unit floor by day 9;
  storms hit on days 17, 22, 23 and 26.
- `sim_log.json` contains all 100 agents' scores, health, food and shelter
  for all 30 days — a diff against the archived copy should be empty.

**Batch (`python3 batch_run.py`)** — 100 fresh islands, seeds 1000–1099.
The winner is classified by their **strongest trait** (the maximum of the
five; ties broken in the order skill, grit, risk, honesty, luck).

- Wins by strongest trait: **skill 54 · honesty 15 · luck 15 · grit 12 · risk 4**
- Wins by strategy (raw, undisguised): **leader 52 · survivor 26 ·
  cooperator 18 · hoarder 3 · loner 0 · thief 1**
- The winner lived in a camp in **95 of 100** runs.
- Survival by strategy (pooled): camp members — leaders 97.3 %,
  cooperators 97.8 %, survivors 97.7 %; solo — hoarders 21.2 %,
  **loners 1.3 % (21 of 1,617 survived)**, thieves 22.9 %.
- Median winning score 160; mean deaths per island 36.4.

## Honest assumptions note

The parameters above are **design choices**, made before any run: the
mechanisms the episode talks about (specialisation, sharing as insurance,
the depletion of a commons) are *encoded by construction* — camps pool risk
because the rules let them share food, tools and shelter, and solo agents
face the island's variance alone. So the results **illustrate** these
principles; they do not **prove** anything about the real world, and the
narration only ever says the simulation "shows" them. The featured seed
(42) was selected from a scan of candidate seeds because its story had the
reversals a 2-minute video needs; the 100-island aggregate — which does not
include the featured seed — is the unbiased picture, and it tells the same
story. Further simplifications: traits are uniform and independent (real
people's aren't); the island's stocks are simple logistic-style pools, not
an ecology; nobody ages, leaves, or is rescued; and "thriving" is our
scoring formula (health + stored food + shelter), not a law of nature.
