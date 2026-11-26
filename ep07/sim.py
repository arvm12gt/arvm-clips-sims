#!/usr/bin/env python3
"""
EP07 simulation: 100 people in a city whose shared resources shrink
10% every day. 30 days. Who is still standing — and richest?

Agent-based model. Fixed seed. Story comes from the output, not a script.

Premise (stated in the video): the city granary loses 10% of what is
in it every morning — food, water, fuel, everything the town runs on,
evaporating. What people produce goes back in; what they eat comes out.
Each person has 6 free hours a day after work. Free time does real work:
you LEARN (skill grows — the only durable asset), you post DEALS (group
projects, same offer machinery as EP03-EP06), you NETWORK (rally
followers), you HELP people (build trust) — or you WASTE the hours
(nothing). Leadership is not appointed: it emerges from who others
CHOOSE to follow, and a leader earns a share of their followers'
output. The winner is the richest agent on day 30 (same scoring as
EP01-EP06).

The scarcity mechanic is THE GRANARY. It starts at 3,000 units and
loses 10% every morning, no matter what. Production puts food back in;
eating takes it out. The FOOD PRICE is set by the granary: cheap while
it is full, ruinous when it thins — price = 4 * 2000 / stock, capped
at $60. Everyone must eat one unit a day. Three strategies answer
scarcity differently, and that is the claim the sim tests:
  - HOARDERS buy food while it is cheap and eat from their own pile
    when the price explodes (a private stockpile, capped at 12 units);
  - SHARERS buy food for the granary when it runs low (2 units a day,
    if they can afford it) and earn the trust that brings followers;
  - PRODUCERS work the land: they put the most food back in (1.6x
    production) and their wages grow with the skill they learn.
Go hungry three days in a row and you starve out of the city. The
granary never refills from outside: the only question is who adapts
as it thins.

Traits per agent (0..1), drawn in this fixed order:
  skill, work_ethic (grit), risk_appetite, honesty, luck
Honesty is an ordinary trait spread across the whole town; anyone may lie.

Strategy labels are derived from traits (checked in this order):
  - hoarder   : risk < 0.40 and grit > 0.45 (cautious, self-reliant:
    buys food cheap, keeps a pile, shares nothing)
  - sharer    : honesty > 0.60 and grit > 0.50 (donates food when the
    granary runs low, builds trust)
  - producer  : skill > 0.55 and grit > 0.55 (works the land: 3 learn
    hours a day, 1.6x food production)
  - trader    : risk > 0.55 and honesty > 0.45 (bold, trusted: talks
    to the whole town, 2 deals a day)
  - schemer   : risk > 0.55 and honesty < 0.45 (lies in deals, bets
    big: 2 deals a day, 2 hours wasted watching the damage)
  - worker    : everyone else (a bit of everything)

Day plan (learn, deal, network, help, waste) in hours per day:
  hoarder  (1, 1, 0, 0, 0) = 2 spent, 4 left (watchful: unspent hours
    are offline attention — hoarders spot lies well)
  sharer   (1, 1, 1, 2, 0) = 5 spent, 1 left
  producer (3, 1, 0, 1, 0) = 5 spent, 1 left
  trader   (0, 2, 1, 1, 0) = 4 spent, 2 left
  schemer  (0, 2, 1, 0, 2) = 5 spent, 1 left
  worker   (1, 1, 1, 1, 1) = 5 spent, 1 left
Unspent hours are OFFLINE time: attention. A person with hours left
over spots lies better. Wasting counts as spent: it consumes attention
too, it just produces nothing.

Mechanics (all parameters below, all in REPRODUCE.md):
  - 100 people start with $100 each. Ranking is by money; money <= 0
    at day's end = bankrupt: out of the economy (followers leave, no
    wages, no deals, no food), final money $0.
  - GRANARY. Starts at 3,000 units. Every morning it loses 10%
    (stock *= 0.90). Production adds to it during the day; eating
    takes from it at night. Tracked daily in the log.
  - FOOD PRICE. Set each morning from the post-decay stock:
    price = clamp(4 * 2000 / stock, $2, $60). Full granary: ~$2.70 a
    meal. Thin granary (~450 left): ~$18 a meal. The price is the
    crunch, made visible. (Tuned 2026-11-26: REF 1500 left the price
    at ~$9 on day 30 — no bite; REF 3000+ starved 30-60% of the town.
    REF 2000 gives a ~7x price rise with 20-35 bankrupt.)
  - PRODUCTION. Each agent's work puts food in the granary:
    produce = (0.45 + 0.9*skill) * (0.5 + 0.8*grit) * strat_mult,
    strat_mult: producer 1.6, hoarder 1.2, sharer 1.0, trader 0.8,
    schemer 0.8, worker 1.0. A hungry agent produces 0.7x (and earns
    0.7x wages) — hunger compounds.
  - HOARDING. Each morning, a hoarder with a pile below 12 buys up to
    4 units if the price is under $8 and they can afford it. The pile
    is eaten first, free, when the price is high.
  - SHARING. At night, a sharer with money > $150 buys 2 units at the
    day's price and puts them in the granary (donation), gaining
    reputation +0.02. Trust is the sharer's currency.
  - EATING. At night, in random order, each agent eats one unit: from
    their pile first (free), else buys one unit from the granary at
    the day's price (if money and stock allow), else goes hungry.
    Hungry 3 days in a row = starved out (bankrupt, money $0).
  - LEARN. Each learn hour raises skill by 0.008 * (0.5 + grit),
    capped at 1.0. Skill is the town's only durable asset: it raises
    wages, deal quality and food production.
  - DEALS. Each deal proposes a group project with true quality
    q = 0.20 + 0.60*skill + 0.20*U(0,1). A liar may inflate the claim:
    with probability (1-honesty)*(0.4+0.6*risk) they claim
    q*(1+L), L = (0.15+0.60*risk)*U(0.5,1.2). Producers post only if
    the idea clears 0.55 — they put their name on good ideas only.
  - LISTENING. Each agent samples 6 deals a day (weighted by the
    speaker's reputation — the trusted get heard), plus their current
    leader's deal if they have one. A listener may spot a lie:
    detection probability grows with their skill, their unspent hours
    (attention) and the lie's size. The FIRST listener to spot a lie
    exposes it publicly: the speaker's reputation takes a hit and
    every later listener discounts that deal.
  - FOLLOWING. Each listener follows the best deal they heard,
    scored by perceived quality x (0.35+0.65*speaker reputation),
    with a small loyalty bonus for staying with their current leader.
    A big crowd also dilutes the score a little (divided by
    1 + followers/60). If no deal scores above the threshold they
    work solo. Following is a real economic choice: a follower's
    output is boosted by the leader's skill (1 + 0.30*leader skill,
    diluted as the crowd grows), the follower keeps 90% of it, and
    the leader takes a 10% share of every follower's output — a share
    that also thins with crowd size. A leader's own output also grows
    with their following (1 + 0.02 per follower, capped at 15).
  - NETWORKING. A leader may spend hours networking — but only if
    they actually have followers to rally. Each network hour adds
    0.08*(0.5+reputation) to every follower's output that day.
  - PROJECTS CAN FLOP. The followed project's realised quality is
    its deal quality plus execution noise U(-0.12, 0.12), drawn once
    per leader per day. Below 0.50 it flops: followers' output x0.7
    and the leader's reputation drops 0.02.
  - HELP. One hour of helping people raises reputation a little
    (0.012 if honesty > 0.5). From a liar it is cheap talk: +0.004,
    with a 15% chance of being read as flattery (-0.02).
  - REPUTATION (0.02..1.0, starts 0.5) is public and is the town's
    memory. It steers who gets heard (sampling weights), who gets
    followed (follow score) and network power. A delivered honest deal
    (q >= 0.5, no lie) adds 0.01; a successful coordination day adds
    up to 0.01. A caught lie costs 0.05 + 0.10*L.
  - WAGES. Solo work pays (12 + 30*skill) * (0.5 + 0.8*grit) *
    U(0.85, 1.15), minus a $15 living cost — the same base economy
    as EP01-EP06, so learning and leadership income are visible on
    top of it. Food is bought on top of the living cost, at the
    day's granary price.
"""
import json, random
from dataclasses import dataclass

SEED = 1              # placeholder; the featured seed comes from scan_seeds.py
DAYS = 30
N = 100
START_MONEY = 100.0
LIVING_COST = 15.0
FREE_HOURS = 6

# ---- granary (the scarcity mechanic) ----
STOCK_START = 3000.0                 # granary units on day 1
DECAY = 0.90                         # granary keeps 90% each morning (-10%/day)
PRICE_BASE, PRICE_REF = 4.0, 2000.0  # price = PRICE_BASE * PRICE_REF / stock
PRICE_MIN, PRICE_CAP = 2.0, 60.0
HOARD_BUY_PRICE = 8.0               # hoarders buy only while food is cheap
HOARD_PILE_CAP = 12                 # personal stockpile cap (units)
HOARD_BUY_MAX_DAY = 4               # max units bought per morning
SHARE_DONATE_STOCK = 800.0          # sharers donate while granary is below this
SHARE_DONATE_MONEY = 150.0          # ... and only if they can afford it
SHARE_DONATE_UNITS = 2
REP_DONATE = 0.02
HUNGER_LIMIT = 3                    # hungry this many days in a row = starved out
HUNGER_PENALTY = 0.7                # hungry agents earn/produce 0.7x
PROD_BASE, PROD_SKILL = 0.45, 0.9   # produce = (0.45 + 0.9*skill) * (0.5 + 0.8*grit) * mult
PROD_MULT = {"producer": 1.6, "hoarder": 1.2, "sharer": 1.0,
             "trader": 0.8, "schemer": 0.8, "worker": 1.0}

# ---- wages (same base economy as EP01-EP06) ----
WAGE_BASE, WAGE_SKILL = 12.0, 30.0     # wage = (12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)

# ---- learn ----
LEARN_RATE = 0.008                     # skill gain per learn hour: * (0.5 + grit), cap 1.0
PRODUCER_DEAL_FLOOR = 0.55             # producers post only if the idea clears this quality

# ---- deals (same machinery as EP04/EP05/EP06 pitches) ----
DEAL_COST = 1                          # 1 free hour per deal
DEALS_HEARD = 6                        # deals a listener samples per day (+ current leader's)
FOLLOW_THRESHOLD = 0.30                # min follow score, else work solo
LOYALTY_BONUS = 0.04                   # score bonus for staying with current leader
REP_HEAR_WEIGHT = 0.20                 # sampling weight = (0.20 + rep) x (4 / deals made today)
FOLLOW_REP_WEIGHT = 0.35               # follow score = perceived q * (0.35 + 0.65*rep)

# ---- lies & detection ----
LIE_BASE, LIE_RISK = 0.15, 0.60        # L = (0.15 + 0.60*risk) * U(0.5, 1.2)
REP_LIE_CAUGHT = 0.05                  # rep hit: + 0.10 * L on top
DETECT_BASE, DETECT_SKILL = 0.08, 0.35 # p_detect = 0.08 + 0.35*skill + 0.02*unspent + 0.25*L
DETECT_ATTENTION, DETECT_LIE = 0.02, 0.25
EXPOSED_DISCOUNT = 0.80                # exposed deal perceived at 80% of true quality

# ---- coordination ----
COORD_SKILL_BONUS = 0.30               # follower output x (1 + 0.30*leader skill), crowd-diluted
COORD_CROWD_DIVISOR = 30.0             # skill bonus divided by (1 + followers/30)
LEADER_SHARE = 0.10                    # leader takes 10% of each follower's output, crowd-thinned
LEADER_SHARE_DIVISOR = 20.0            # share rate divided by (1 + followers/20)
LEADER_CROWD_BONUS = 0.02              # leader's own output +2% per follower, cap 15
LEADER_CROWD_CAP = 15
RALLY_BOOST = 0.08                     # per network hour: +0.08*(0.5+rep) follower output
FLOP_NOISE = 0.12                      # realised quality = deal q + U(-0.12, 0.12), once per leader/day
FLOP_THRESHOLD = 0.50                  # realised quality below this = flop
SCORE_CROWD_DIVISOR = 60.0             # follow score divided by (1 + followers/60)
FLOP_OUTPUT = 0.70                     # flop: followers' output x0.7
REP_FLOP = 0.02
REP_HONEST_DEAL = 0.01                 # delivered honest deal with q >= 0.5
REP_COORD_DAY = 0.01                   # successful coordination day (scaled by followers/10)

# ---- help ----
REP_TRUST_HONEST = 0.012
REP_TRUST_CHEAP = 0.004
FLATTERY_P, REP_FLATTERY = 0.15, 0.02

FIRST = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda","David","Elizabeth",
"William","Barbara","Richard","Susan","Joseph","Jessica","Thomas","Sarah","Charles","Karen",
"Daniel","Nancy","Matthew","Lisa","Anthony","Betty","Mark","Margaret","Donald","Sandra",
"Steven","Ashley","Paul","Kimberly","Andrew","Emily","Joshua","Michelle","Kenneth","Dorothy",
"Kevin","Amanda","Brian","Melissa","George","Deborah","Timothy","Rebecca","Ronald","Stephanie",
"Edward","Catherine","Jeffrey","Christine","Ryan","Debra","Jacob","Rachel","Gary","Carolyn",
"Nicholas","Janet","Eric","Maria","Jonathan","Olivia","Stephen","Heather","Larry","Diane",
"Justin","Julie","Scott","Joyce","Brandon","Victoria","Benjamin","Kelly","Samuel","Lauren",
"Gregory","Cheryl","Alexander","Hannah","Patrick","Jacqueline","Frank","Martha","Raymond","Gloria",
"Jack","Ann","Dennis","Teresa","Jerry","Kathryn","Tyler","Janice","Aaron","Lawrence","Ethan","Diana"]

# day plan (learn, deal, network, help, waste) in hours per day, by strategy
DAY_PLAN = {
    "hoarder":  (1, 1, 0, 0, 0),
    "sharer":   (1, 1, 1, 2, 0),
    "producer": (3, 1, 0, 1, 0),
    "trader":   (0, 2, 1, 1, 0),
    "schemer":  (0, 2, 1, 0, 2),
    "worker":   (1, 1, 1, 1, 1),
}

def pick_strategy(a):
    if a.risk < 0.40 and a.work_ethic > 0.45: return "hoarder"
    if a.honesty > 0.60 and a.work_ethic > 0.50: return "sharer"
    if a.skill > 0.55 and a.work_ethic > 0.55: return "producer"
    if a.risk > 0.55 and a.honesty > 0.45: return "trader"
    if a.risk > 0.55 and a.honesty < 0.45: return "schemer"
    return "worker"

@dataclass
class Agent:
    id: int
    name: str
    skill: float
    work_ethic: float
    risk: float
    honesty: float
    luck: float
    strategy: str = ""
    money: float = START_MONEY
    rep: float = 0.5
    bankrupt: bool = False
    bankrupt_day: int = -1
    starved: bool = False
    peak_money: float = START_MONEY
    skill_start: float = 0.0
    leader_id: int = -1          # who this agent follows (-1 = solo)
    followers_yesterday: int = 0  # followers at end of yesterday (network only if > 0)
    network_today: int = 0        # effective network hours spent today
    unspent: int = 0              # free hours left over today (= offline attention, for lie detection)
    hours_spent: int = 0
    learn_hours: int = 0
    waste_hours: int = 0
    deals: int = 0
    network: int = 0
    helps: int = 0
    lies_told: int = 0
    lies_caught: int = 0
    followers_peak: int = 0
    days_as_leader: int = 0      # days as the town's most-followed leader
    leadership_income: float = 0.0  # share collected from followers
    follower_bonus_earned: float = 0.0  # extra output earned by following vs solo
    projects_led: int = 0        # days leading >=1 follower
    projects_flopped: int = 0
    # granary economy
    stockpile: int = 0           # personal food pile (units)
    stockpile_peak: int = 0
    produced_total: float = 0.0
    food_bought_total: int = 0   # units bought for eating (not hoarding)
    food_spent_total: float = 0.0
    hoarded_total: int = 0       # units bought into the pile
    ate_free_days: int = 0       # days eaten from the pile
    donated_total: int = 0       # units donated to the granary
    hungry_days: int = 0
    hungry_streak: int = 0
    money_rank_day1: int = 0     # filled in after day 1

def trait_dict(a):
    return {"skill": round(a.skill, 2), "work_ethic": round(a.work_ethic, 2),
            "risk": round(a.risk, 2), "honesty": round(a.honesty, 2),
            "luck": round(a.luck, 2)}

def strongest_trait(a):
    # EP05/EP06/EP07: skill GROWS through the month (learning), so the honest
    # grouping is by the traits the winner STARTED with — end-state skill
    # is ~1.0 for every learner and would make the grouping degenerate.
    vals = [("skill", a.skill_start), ("grit", a.work_ethic), ("risk", a.risk),
            ("honesty", a.honesty), ("luck", a.luck)]
    return max(vals, key=lambda kv: kv[1])[0]

def food_price(stock):
    return min(PRICE_CAP, max(PRICE_MIN, PRICE_BASE * PRICE_REF / max(stock, 1.0)))

def run(seed=SEED):
    rng = random.Random(seed)
    # --- setup: 5 trait draws per agent, fixed order (renderer replays this) ---
    agents = []
    for i in range(N):
        skill = rng.random(); grit = rng.random(); risk = rng.random()
        hon = rng.random(); luck = rng.random()
        agents.append(Agent(id=i, name=FIRST[i], skill=skill, work_ethic=grit,
                            risk=risk, honesty=hon, luck=luck))
    for a in agents:
        a.strategy = pick_strategy(a)
        a.skill_start = a.skill
        a.peak_money = a.money

    stock = STOCK_START
    events = []
    daily = []
    prev_leader = None
    total_hours = total_learn = total_waste = 0
    total_lies = total_caught = 0
    total_deals = total_flops = 0
    total_produced = total_donated = 0.0
    total_hungry_days = total_starved = 0
    total_food_spent = 0.0
    leader_history = []   # (day, leader name, followers)
    stock_by_day = []
    price_by_day = []

    for day in range(1, DAYS + 1):
        active = [a for a in agents if not a.bankrupt]
        # ---------------- morning: the granary loses 10%, price is set ----------------
        stock *= DECAY
        price = food_price(stock)
        stock_morning = stock
        price_by_day.append(round(price, 2))
        # hoarders buy while food is cheap (before the day's work)
        hoarded_today = 0
        for a in active:
            if a.strategy != "hoarder" or price >= HOARD_BUY_PRICE:
                continue
            room = HOARD_PILE_CAP - a.stockpile
            if room <= 0:
                continue
            want = min(room, HOARD_BUY_MAX_DAY)
            afford = int(a.money // price)
            buy = min(want, afford)
            if buy > 0:
                a.money -= buy * price
                a.stockpile += buy
                a.hoarded_total += buy
                a.food_spent_total += buy * price
                a.stockpile_peak = max(a.stockpile_peak, a.stockpile)
                hoarded_today += buy
        total_food_spent += hoarded_today * price

        # ---------------- day phase: learn + deals ----------------
        deals = []
        day_hours = day_learn = day_waste = 0
        for a in active:
            nlearn, ndeal, nnet, nhelp, nwaste = DAY_PLAN[a.strategy]
            hungry_mult = HUNGER_PENALTY if a.hungry_streak > 0 else 1.0
            # learn: skill grows, capped at 1.0
            if nlearn:
                a.skill = min(1.0, a.skill + LEARN_RATE * nlearn * (0.5 + a.work_ethic))
                a.learn_hours += nlearn; day_learn += nlearn
            # networking only counts if there is someone to rally
            nnet_eff = nnet if a.followers_yesterday > 0 else 0
            # deals: producers post only when the idea is worth posting
            made = 0
            for _ in range(ndeal):
                q = 0.20 + 0.60 * a.skill + 0.20 * rng.random()
                if a.strategy == "producer" and q < PRODUCER_DEAL_FLOOR:
                    continue   # saves the hour: it becomes offline attention
                lying = rng.random() < (1 - a.honesty) * (0.4 + 0.6 * a.risk)
                if lying:
                    L = (LIE_BASE + LIE_RISK * a.risk) * rng.uniform(0.5, 1.2)
                    claim = min(1.2, q * (1 + L))
                    a.lies_told += 1; total_lies += 1
                else:
                    L = 0.0; claim = q
                deals.append({"speaker": a, "q": q, "claim": claim,
                              "lying": lying, "L": L, "exposed": False})
                made += 1
            spent = nlearn + made * DEAL_COST + nnet_eff + nhelp + nwaste
            spent = min(spent, FREE_HOURS)
            a.hours_spent += spent
            day_hours += spent
            a.waste_hours += nwaste; day_waste += nwaste
            a.deals += made; a.network += nnet_eff; a.helps += nhelp
            a.network_today = nnet_eff
            a.unspent = FREE_HOURS - spent   # offline attention, for detection
            # help
            for _ in range(nhelp):
                if a.honesty > 0.5:
                    a.rep = min(1.0, a.rep + REP_TRUST_HONEST)
                else:
                    if rng.random() < FLATTERY_P:
                        a.rep = max(0.02, a.rep - REP_FLATTERY)
                    else:
                        a.rep = min(1.0, a.rep + REP_TRUST_CHEAP)
        total_hours += day_hours
        total_learn += day_learn
        total_waste += day_waste
        total_deals += len(deals)

        # ---------------- listening & following ----------------
        made_count = {}
        for p in deals:
            made_count[p["speaker"].id] = made_count.get(p["speaker"].id, 0) + 1
        weights = [(REP_HEAR_WEIGHT + p["speaker"].rep) * (4.0 / made_count[p["speaker"].id])
                   for p in deals]
        wsum = sum(weights)
        followers = {a.id: [] for a in active}   # leader id -> follower agents
        for a in active:
            heard = []
            if deals and wsum > 0:
                idxs = set()
                tries = 0
                while len(idxs) < min(DEALS_HEARD, len(deals)) and tries < 40:
                    tries += 1
                    x = rng.random() * wsum
                    for j, w in enumerate(weights):
                        x -= w
                        if x <= 0:
                            idxs.add(j); break
                heard = [deals[j] for j in idxs]
            if a.leader_id >= 0:
                for p in deals:
                    if p["speaker"].id == a.leader_id and p not in heard:
                        heard.append(p)
            best = None; best_score = FOLLOW_THRESHOLD
            for p in heard:
                sp = p["speaker"]
                if sp is a or sp.bankrupt:
                    continue
                if p["lying"] and not p["exposed"]:
                    pd = min(0.90, max(0.02, DETECT_BASE + DETECT_SKILL * a.skill
                                        + DETECT_ATTENTION * a.unspent + DETECT_LIE * p["L"]))
                    if rng.random() < pd:
                        p["exposed"] = True
                        sp.rep = max(0.02, sp.rep - (REP_LIE_CAUGHT + 0.10 * p["L"]))
                        sp.lies_caught += 1; total_caught += 1
                        if p["L"] >= 0.45:
                            events.append({"day": day, "type": "exposed", "who": sp.name,
                                           "detail": f"{sp.name} caught lying: claimed a project worth "
                                                     f"{p['claim']:.2f} that was really {p['q']:.2f}"})
                perceived = p["q"] * EXPOSED_DISCOUNT if p["exposed"] else p["claim"]
                perceived = min(1.0, perceived)
                score = perceived * (FOLLOW_REP_WEIGHT + (1 - FOLLOW_REP_WEIGHT) * sp.rep)
                score /= 1.0 + sp.followers_yesterday / SCORE_CROWD_DIVISOR
                if sp.id == a.leader_id:
                    score += LOYALTY_BONUS
                if score > best_score:
                    best_score = score; best = sp
            a.leader_id = best.id if best is not None else -1
            if best is not None:
                followers[best.id].append(a)
        for p in deals:
            if not p["lying"] and p["q"] >= 0.5 and not p["exposed"]:
                p["speaker"].rep = min(1.0, p["speaker"].rep + REP_HONEST_DEAL)

        # ---------------- work phase: wages + food production ----------------
        realised_q = {}
        for a in active:
            fols = followers.get(a.id, [])
            if not fols:
                continue
            ldeal = None
            for p in deals:
                if p["speaker"] is a:
                    ldeal = p; break
            realised_q[a.id] = (ldeal["q"] + rng.uniform(-FLOP_NOISE, FLOP_NOISE)) if ldeal else 0.5
        rally_mult = {}
        for a in active:
            fols = followers.get(a.id, [])
            if fols and a.network_today > 0:
                rally_mult[a.id] = 1.0 + RALLY_BOOST * a.network_today * (0.5 + a.rep)
                if len(fols) >= 15:
                    events.append({"day": day, "type": "rally", "who": a.name,
                                   "detail": f"{a.name} networks with {len(fols)} followers "
                                             f"({a.network_today} hour{'s' if a.network_today > 1 else ''})"})
        produced_today = 0.0
        for a in active:
            hungry_mult = HUNGER_PENALTY if a.hungry_streak > 0 else 1.0
            wage = (WAGE_BASE + WAGE_SKILL * a.skill) * (0.5 + 0.8 * a.work_ethic) \
                   * rng.uniform(0.85, 1.15) * hungry_mult
            # food production goes straight into the granary
            prod = (PROD_BASE + PROD_SKILL * a.skill) * (0.5 + 0.8 * a.work_ethic) \
                   * PROD_MULT[a.strategy] * hungry_mult
            a.produced_total += prod
            produced_today += prod
            if a.leader_id >= 0:
                leader = agents[a.leader_id]
                if leader.bankrupt:
                    a.leader_id = -1
                    a.money += wage - LIVING_COST
                    continue
                fols = followers.get(leader.id, [])
                realised = realised_q.get(leader.id, 0.5)
                flop = realised < FLOP_THRESHOLD
                n_fols = len(fols)
                crowd = 1.0 + n_fols / COORD_CROWD_DIVISOR
                out = wage * (1 + COORD_SKILL_BONUS * leader.skill / crowd)
                out *= rally_mult.get(leader.id, 1.0)
                if flop:
                    out *= FLOP_OUTPUT
                share_rate = LEADER_SHARE / (1.0 + n_fols / LEADER_SHARE_DIVISOR)
                keep = out * (1 - share_rate)
                share = out * share_rate
                a.money += keep - LIVING_COST
                a.follower_bonus_earned += keep - wage
                leader.money += share
                leader.leadership_income += share
                if flop and a is fols[0]:
                    leader.projects_flopped += 1
                    total_flops += 1
                    leader.rep = max(0.02, leader.rep - REP_FLOP)
                    if len(fols) >= 8:
                        events.append({"day": day, "type": "flop", "who": leader.name,
                                       "detail": f"{leader.name}'s project flopped with "
                                                 f"{len(fols)} followers on it"})
            else:
                a.money += wage - LIVING_COST
        for a in active:
            fols = followers.get(a.id, [])
            if fols:
                a.projects_led += 1
                a.followers_peak = max(a.followers_peak, len(fols))
                a.money += (WAGE_BASE + WAGE_SKILL * a.skill) * 0.3 \
                           * LEADER_CROWD_BONUS * min(len(fols), LEADER_CROWD_CAP)
                realised = realised_q.get(a.id, 0.5)
                if realised >= 0.5:
                    a.rep = min(1.0, a.rep + REP_COORD_DAY * min(len(fols), 10) / 10.0)
        stock += produced_today
        total_produced += produced_today

        # ---------------- night: sharers donate, everyone eats ----------------
        donated_today = 0
        for a in active:
            if a.strategy == "sharer" and stock < SHARE_DONATE_STOCK and a.money > SHARE_DONATE_MONEY:
                cost = SHARE_DONATE_UNITS * price
                if a.money >= cost:
                    a.money -= cost
                    a.donated_total += SHARE_DONATE_UNITS
                    a.food_spent_total += cost
                    stock += SHARE_DONATE_UNITS
                    donated_today += SHARE_DONATE_UNITS
                    a.rep = min(1.0, a.rep + REP_DONATE)
        total_donated += donated_today
        eat_order = active[:]
        rng.shuffle(eat_order)
        hungry_today = 0
        starved_today = 0
        for a in eat_order:
            if a.stockpile > 0:
                a.stockpile -= 1
                a.ate_free_days += 1
                a.hungry_streak = 0
                continue
            if stock >= 1.0 and a.money >= price:
                a.money -= price
                stock -= 1.0
                a.food_bought_total += 1
                a.food_spent_total += price
                total_food_spent += price
                a.hungry_streak = 0
            else:
                a.hungry_days += 1
                a.hungry_streak += 1
                hungry_today += 1
                if a.hungry_streak >= HUNGER_LIMIT:
                    a.starved = True
                    a.bankrupt = True
                    a.bankrupt_day = day
                    a.money = 0.0
                    starved_today += 1
                    events.append({"day": day, "type": "starved", "who": a.name,
                                   "detail": f"{a.name} ({a.strategy}) starved out on day {day} "
                                             f"— 3 days with no food (price ${price:.0f})"})
        total_hungry_days += hungry_today
        total_starved += starved_today
        if hungry_today >= 10:
            events.append({"day": day, "type": "hunger", "who": "town",
                           "detail": f"{hungry_today} people went hungry on day {day} "
                                     f"(food ${price:.0f}, granary {stock:.0f})"})

        # ---------------- bankruptcy (money) + snapshots ----------------
        for a in agents:
            if not a.bankrupt and a.money <= 0:
                a.money = 0.0; a.bankrupt = True; a.bankrupt_day = day
                events.append({"day": day, "type": "bankrupt", "who": a.name,
                               "detail": f"{a.name} ({a.strategy}) went broke on day {day}"})
            if not a.bankrupt:
                a.peak_money = max(a.peak_money, a.money)
        ranked = sorted(agents, key=lambda a: -a.money)
        if day == 1:
            for a in agents:
                a.money_rank_day1 = ranked.index(a) + 1
        day_leader = None; day_fols = 0
        for a in active:
            n = len(followers.get(a.id, []))
            if n > day_fols or (n == day_fols and n > 0 and day_leader is not None
                                and a.money > day_leader.money):
                day_leader = a; day_fols = n
        for a in active:
            a.followers_yesterday = len(followers.get(a.id, []))
        leader_name = day_leader.name if day_leader is not None else None
        if day_leader is not None:
            day_leader.days_as_leader += 1
        leader_history.append({"day": day, "leader": leader_name, "followers": day_fols})
        if prev_leader is not None and leader_name is not None and leader_name != prev_leader:
            newl = day_leader
            events.append({"day": day, "type": "lead_change", "who": leader_name,
                           "detail": f"{leader_name} ({newl.strategy}) takes the lead with "
                                     f"{day_fols} followers, ${newl.money:,.0f}"})
        if leader_name is not None:
            prev_leader = leader_name
        act = [a for a in agents if not a.bankrupt]
        stock_by_day.append(round(stock, 1))
        daily.append({
            "day": day,
            "leader": leader_name,
            "leader_followers": day_fols,
            "leader_money": round(day_leader.money) if day_leader is not None else 0,
            "leader_strategy": day_leader.strategy if day_leader is not None else None,
            "top5": [{"name": x.name, "money": round(x.money), "strategy": x.strategy}
                     for x in ranked[:5]],
            "active_count": len(act),
            "bankrupt_total": sum(1 for a in agents if a.bankrupt),
            "starved_total": total_starved,
            "mean_rep": round(sum(a.rep for a in act) / len(act), 3) if act else 0.0,
            "mean_skill": round(sum(a.skill for a in act) / len(act), 3) if act else 0.0,
            "stock_morning": round(stock_morning, 1),
            "stock": round(stock, 1),
            "food_price": round(price, 2),
            "produced_today": round(produced_today, 1),
            "donated_today": donated_today,
            "hoarded_today": hoarded_today,
            "hungry_today": hungry_today,
            "starved_today": starved_today,
            "screen_hours": day_hours,
            "learn_hours_day": day_learn,
            "waste_hours_day": day_waste,
            "lies_told_day": sum(1 for p in deals if p["lying"]),
            "lies_caught_day": sum(1 for p in deals if p["exposed"]),
            "money": [round(a.money, 1) for a in agents],
            "rep": [round(a.rep, 3) for a in agents],
            "skill": [round(a.skill, 3) for a in agents],
            "followers": [len(followers.get(a.id, [])) for a in agents],
            "bankrupt": [a.bankrupt for a in agents],
        })

    ranked = sorted(agents, key=lambda a: -a.money)
    winner = ranked[0]
    most_skilled = max(agents, key=lambda a: a.skill)
    hardest = max(agents, key=lambda a: a.work_ethic)
    biggest_liar = max(agents, key=lambda a: a.lies_told)
    most_followed = max(agents, key=lambda a: a.followers_peak)
    biggest_waster = max(agents, key=lambda a: a.waste_hours)
    biggest_learner = max(agents, key=lambda a: a.learn_hours)
    biggest_producer = max(agents, key=lambda a: a.produced_total)
    biggest_hoarder = max(agents, key=lambda a: a.hoarded_total)
    biggest_donor = max(agents, key=lambda a: a.donated_total)
    hungriest = max(agents, key=lambda a: a.hungry_days)
    strat_counts = {}
    for s in ("hoarder", "sharer", "producer", "trader", "schemer", "worker"):
        strat_counts[s] = sum(1 for a in agents if a.strategy == s)
    lead_changes = sum(1 for i in range(1, len(leader_history))
                       if leader_history[i]["leader"] != leader_history[i - 1]["leader"]
                       and leader_history[i]["leader"] is not None)
    distinct_leaders = len({h["leader"] for h in leader_history if h["leader"]})
    day_stock_below_1000 = next((i + 1 for i, s in enumerate(stock_by_day) if s < 1000), None)
    day_stock_below_500 = next((i + 1 for i, s in enumerate(stock_by_day) if s < 500), None)

    def fate(a):
        return {"name": a.name, "strategy": a.strategy, "traits": trait_dict(a),
                "bankrupt": a.bankrupt,
                "bankrupt_day": a.bankrupt_day,
                "starved": a.starved,
                "final_rank": ranked.index(a) + 1, "final_money": round(a.money),
                "peak_money": round(a.peak_money), "final_rep": round(a.rep, 3),
                "skill_start": round(a.skill_start, 3),
                "skill_end": round(a.skill, 3),
                "skill_gain": round(a.skill - a.skill_start, 3),
                "final_followers": len([x for x in agents if x.leader_id == a.id and not x.bankrupt]),
                "followers_peak": a.followers_peak,
                "days_as_leader": a.days_as_leader,
                "hours_spent": a.hours_spent,
                "hours_per_day": round(a.hours_spent / DAYS, 2),
                "learn_hours": a.learn_hours,
                "learn_per_day": round(a.learn_hours / DAYS, 2),
                "waste_hours": a.waste_hours,
                "waste_per_day": round(a.waste_hours / DAYS, 2),
                "deals": a.deals, "network": a.network, "helps": a.helps,
                "lies_told": a.lies_told, "lies_caught": a.lies_caught,
                "leadership_income": round(a.leadership_income),
                "follower_bonus_earned": round(a.follower_bonus_earned),
                "projects_led": a.projects_led, "projects_flopped": a.projects_flopped,
                "stockpile_final": a.stockpile,
                "stockpile_peak": a.stockpile_peak,
                "produced_total": round(a.produced_total, 1),
                "produced_per_day": round(a.produced_total / DAYS, 2),
                "food_bought_total": a.food_bought_total,
                "food_spent_total": round(a.food_spent_total),
                "hoarded_total": a.hoarded_total,
                "ate_free_days": a.ate_free_days,
                "donated_total": a.donated_total,
                "hungry_days": a.hungry_days,
                "money_rank_day1": a.money_rank_day1}
    log = {
        "seed": seed, "days": DAYS,
        "premise": "100 start with $100; granary 3,000 units, -10% every morning; food price = 4*2000/stock (cap $60); hoarders stockpile, sharers donate, producers grow food 1.6x; 3 hungry days = starved out",
        "strategy_counts": strat_counts,
        "daily": daily,
        "leader_history": leader_history,
        "lead_changes": lead_changes,
        "distinct_leaders": distinct_leaders,
        "events": events,
        "final_top10": [dict({"rank": i + 1}, **fate(a)) for i, a in enumerate(ranked[:10])],
        "winner": dict(fate(winner), strongest_trait=strongest_trait(winner)),
        "runner_up": fate(ranked[1]),
        "winning_margin": round(winner.money - ranked[1].money),
        "winning_margin_pct": round(100 * (winner.money - ranked[1].money) / winner.money, 2) if winner.money else 0.0,
        "final_leader": fate(max(agents, key=lambda a: len([x for x in agents if x.leader_id == a.id and not x.bankrupt]))),
        "most_skilled": fate(most_skilled),
        "hardest_worker": fate(hardest),
        "biggest_liar": fate(biggest_liar),
        "most_followed": fate(most_followed),
        "biggest_waster": fate(biggest_waster),
        "biggest_learner": fate(biggest_learner),
        "biggest_producer": fate(biggest_producer),
        "biggest_hoarder": fate(biggest_hoarder),
        "biggest_donor": fate(biggest_donor),
        "hungriest": fate(hungriest),
        "total_screen_hours": total_hours,
        "total_learn_hours": total_learn,
        "total_waste_hours": total_waste,
        "total_deals": total_deals,
        "total_lies": total_lies, "total_caught": total_caught,
        "total_flops": total_flops,
        "total_bankrupt": sum(1 for a in agents if a.bankrupt),
        "total_starved": total_starved,
        "total_hungry_days": total_hungry_days,
        "total_produced": round(total_produced, 1),
        "total_donated": total_donated,
        "total_food_spent": round(total_food_spent),
        "stock_by_day": stock_by_day,
        "price_by_day": price_by_day,
        "stock_day30": stock_by_day[-1] if stock_by_day else 0.0,
        "price_day30": price_by_day[-1] if price_by_day else 0.0,
        "day_stock_below_1000": day_stock_below_1000,
        "day_stock_below_500": day_stock_below_500,
        "final_mean_rep": daily[-1]["mean_rep"] if daily else 0.0,
        "final_mean_skill": daily[-1]["mean_skill"] if daily else 0.0,
        "median_final_money": round(sorted(a.money for a in agents)[50]),
        "town_avg_learn_per_day": round(total_learn / (DAYS * N), 2),
        "town_avg_waste_per_day": round(total_waste / (DAYS * N), 2),
        "town_avg_screen_per_day": round(total_hours / (DAYS * N), 2),
        "town_avg_produced_per_day": round(total_produced / (DAYS * N), 2),
        "agents": [dict({"id": a.id, "name": a.name}, **fate(a)) for a in agents],
    }
    return log

if __name__ == "__main__":
    log = run()
    with open("sim_log.json", "w") as f:
        json.dump(log, f, indent=1)
    w = log["winner"]
    print("winner:", w["name"], w["strategy"], w["final_money"],
          "| runner-up:", log["runner_up"]["name"], log["runner_up"]["final_money"],
          "| margin:", log["winning_margin"], f"({log['winning_margin_pct']}%)")
    print("winner skill:", w["skill_start"], "->", w["skill_end"],
          "| learn/day:", w["learn_per_day"], "| produced/day:", w["produced_per_day"],
          "| hoarded:", w["hoarded_total"], "| ate free:", w["ate_free_days"],
          "| donated:", w["donated_total"], "| hungry days:", w["hungry_days"],
          "| food spent:", w["food_spent_total"])
    print("final leader (most followers):", log["final_leader"]["name"],
          log["final_leader"]["final_followers"], "followers")
    print("biggest producer:", log["biggest_producer"]["name"],
          log["biggest_producer"]["produced_per_day"], "units/day | rank",
          log["biggest_producer"]["final_rank"], "| money", log["biggest_producer"]["final_money"])
    print("biggest hoarder:", log["biggest_hoarder"]["name"],
          "hoarded", log["biggest_hoarder"]["hoarded_total"], "| ate free",
          log["biggest_hoarder"]["ate_free_days"], "| rank", log["biggest_hoarder"]["final_rank"])
    print("biggest donor:", log["biggest_donor"]["name"],
          "donated", log["biggest_donor"]["donated_total"], "| rank",
          log["biggest_donor"]["final_rank"], "| money", log["biggest_donor"]["final_money"])
    print("hungriest:", log["hungriest"]["name"], log["hungriest"]["hungry_days"],
          "hungry days | starved:", log["hungriest"]["starved"],
          "| rank", log["hungriest"]["final_rank"])
    print("stock: day1", log["stock_by_day"][0], "day10", log["stock_by_day"][9],
          "day20", log["stock_by_day"][19], "day30", log["stock_day30"])
    print("price: day1", log["price_by_day"][0], "day10", log["price_by_day"][9],
          "day20", log["price_by_day"][19], "day30", log["price_day30"])
    print("stock <1000 on day:", log["day_stock_below_1000"],
          "| <500 on day:", log["day_stock_below_500"])
    print("bankrupt:", log["total_bankrupt"], "starved:", log["total_starved"],
          "hungry days:", log["total_hungry_days"], "produced:", log["total_produced"],
          "donated:", log["total_donated"], "food spent: $", log["total_food_spent"])
    print("lead changes:", log["lead_changes"], "distinct leaders:", log["distinct_leaders"])
    print("strategy counts:", log["strategy_counts"])
    print("leader by day:", [(h["day"], h["leader"], h["followers"]) for h in log["leader_history"]])
    print("final mean skill:", log["final_mean_skill"], "| final mean rep:", log["final_mean_rep"])
