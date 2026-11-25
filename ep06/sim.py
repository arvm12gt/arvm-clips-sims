#!/usr/bin/env python3
"""
EP06 simulation: 100 people, 30 days. 99 of them start poor with $100.
One of them — Richard — used to be rich. He lost everything and starts
from $0, like the rest... except he keeps what money can't take: high
skill, a Rolodex (starting reputation 0.85 — everyone in town knows his
name), and knowledge of how money works. After 30 days — who is richest?

Agent-based model. Fixed seed. Story comes from the output, not a script.

Premise (stated in the video): the question the sim actually answers is
"how much of being rich is the money, and how much is the know-how?"
Each person has 6 free hours a day after work. Free time does real work:
you LEARN (skill grows — the poor can acquire the know-how), you post
DEALS (group projects, same offer machinery as EP05), you NETWORK
(rally followers), you HELP people (build trust) — or you WASTE the
hours (nothing). Leadership is not appointed: it emerges from who
others CHOOSE to follow, and a leader earns a share of their followers'
output. The winner is the richest agent on day 30 (same scoring as
EP01-EP05).

The money-specific mechanic is CREDIT. Every morning anyone may borrow
from the town bank: the limit is 200 x reputation — so a trusted name
borrows more. Richard's old contacts double his limit and halve his
interest (5% vs 10%): that is the Rolodex, priced in. Borrowed money
can be INVESTED in the day's work: an investor stakes a share of their
money (more if they are risk-hungry) on the project they work on. The
return rides on the project's realised quality (followers) or on their
own skill (solo workers): good judgement pays, bad judgement loses the
stake. The loan is repaid at nightfall with interest — if the money
isn't there, the agent goes broke. Credit amplifies skill; it does not
create it. That is the claim the sim tests, and the batch measures
whether it holds.

Traits per agent (0..1), drawn in this fixed order:
  skill, work_ethic (grit), risk_appetite, honesty, luck
Honesty is an ordinary trait spread across the whole town; anyone may lie.
Richard is the one fixed exception (like Robert's fixed honesty in EP03):
his traits are set, not drawn — skill 0.95, grit 0.90, risk 0.55,
honesty 0.85 — because "the man who used to be rich" is the premise,
not a random draw. His luck is still drawn. His starting reputation is
0.85 (the Rolodex); everyone else starts at 0.5.

Strategy labels are derived from traits (checked in this order):
  - waster     : grit < 0.25 and risk > 0.40 (can't focus; the hours
    go nowhere — 5 hours wasted, 1 hour networking, nothing else)
  - learner    : skill > 0.55 and grit > 0.55 (studies the trade:
    3 learn hours a day, skill grows)
  - hustler    : risk > 0.55 and honesty > 0.55 (bold, trusted: talks
    to the whole town, 2 network hours a day)
  - gambler    : risk > 0.55 and honesty < 0.45 (lies in deals, bets
    big: 2 deals a day, 2 hours wasted watching the damage)
  - dealer     : skill > 0.50 (trades: 2 deals a day)
  - worker     : everyone else (a bit of everything)

Day plan (learn, deal, network, help, waste) in hours per day:
  waster   (0, 0, 1, 0, 5) = 6 spent, 0 left
  learner  (3, 1, 0, 1, 0) = 5 spent, 1 left
  hustler  (0, 1, 2, 1, 0) = 4 spent, 2 left
  gambler  (0, 2, 1, 0, 2) = 5 spent, 1 left
  dealer   (1, 2, 1, 1, 0) = 5 spent, 1 left
  worker   (1, 1, 1, 1, 1) = 5 spent, 1 left
Unspent hours are OFFLINE time: attention. A person with hours left
over spots lies better — the waster, busy all day, spots almost
nothing. Wasting counts as spent: it consumes attention too, it just
produces nothing.

Mechanics (all parameters below, all in REPRODUCE.md):
  - 99 poor start with $100; Richard starts with $0. Ranking is by
    money; money <= 0 at day's end = bankrupt: out of the economy
    (followers leave, no wages, no deals), final money $0.
  - CREDIT. Each morning an agent may borrow up to
    limit = 200 * reputation (Richard: x2). Borrowed amount is
    risk-driven: if risk > 0.35 they take limit * (0.3 + 0.7*risk);
    Richard always takes the full limit (he knows how to use credit);
    otherwise they borrow only in desperation (money < $30: half the
    limit). Interest 10% per day (Richard 5%), repaid at nightfall.
    The loan is added to money in the morning, so it can be invested.
  - INVESTING. Each agent stakes part of the day's money on the work
    they do: invest = min(money * (0.2 + 0.4*risk), 250). The return
    rate rides on realised quality for followers ((q - 0.5) * 2.0) or
    on own skill for solo workers ((skill - 0.5) * 1.5). Invested money
    itself is never lost as principal — only the return is added (or
    subtracted). A skilled investor on a good project profits; a
    bad judge loses the return.
  - LEARN. Each learn hour raises skill by 0.008 * (0.5 + grit),
    capped at 1.0. Skill is the town's only durable asset: it raises
    wages and deal quality. A learner studying 3 hours a day gains
    roughly 0.02 skill a day. Learning compounds; wasting does not.
  - DEALS. Each deal proposes a group project with true quality
    q = 0.20 + 0.60*skill + 0.20*U(0,1). A liar may inflate the claim:
    with probability (1-honesty)*(0.4+0.6*risk) they claim
    q*(1+L), L = (0.15+0.60*risk)*U(0.5,1.2). Learners post only if
    the idea clears 0.55 — they put their name on good ideas only.
  - LISTENING. Each agent samples 6 deals a day (weighted by the
    speaker's reputation — the trusted get heard), plus their current
    leader's deal if they have one. A listener may spot a lie:
    detection probability grows with their skill, their unspent hours
    (attention) and the lie's size. The FIRST listener to spot a lie
    exposes it publicly: the speaker's reputation takes a hit and
    every later listener discounts that deal. An exposed lie is
    narratable; a small lie that nobody spots still pays.
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
  - REPUTATION (0.02..1.0, starts 0.5; Richard 0.85) is public and is
    the town's memory. It steers who gets heard (sampling weights),
    who gets followed (follow score), network power — and the credit
    limit. A delivered honest deal (q >= 0.5, no lie) adds 0.01; a
    successful coordination day adds up to 0.01. A caught lie costs
    0.05 + 0.10*L.
  - WAGES. Solo work pays (12 + 30*skill) * (0.5 + 0.8*grit) *
    U(0.85, 1.15), minus a $15 living cost — the same base economy
    as EP01-EP05, so learning and leadership income are visible on
    top of it. Skill grows through the month, so wages grow with it.
"""
import json, random
from dataclasses import dataclass

SEED = 192           # featured seed chosen by the disclosed seed scan (see REPRODUCE.md); canonical re-run is md5-identical
DAYS = 30
N = 100
START_MONEY = 100.0
RICH_NAME = "Richard"
RICH_START_MONEY = 0.0
RICH_REP_START = 0.85
RICH_SKILL, RICH_GRIT, RICH_RISK, RICH_HONESTY = 0.95, 0.90, 0.55, 0.85
RICH_CREDIT_MULT = 2.0
RICH_INTEREST = 0.05
LIVING_COST = 15.0
FREE_HOURS = 6

# ---- wages (same base economy as EP01-EP05) ----
WAGE_BASE, WAGE_SKILL = 12.0, 30.0     # wage = (12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)

# ---- credit ----
CREDIT_BASE = 200.0                    # limit = 200 * rep (Richard x2)
INTEREST = 0.10                        # per day, repaid at nightfall
DESPERATION_MONEY = 30.0               # borrow half the limit if money below this
INVEST_FRAC_BASE, INVEST_FRAC_RISK = 0.20, 0.40   # invest = min(money*(0.2+0.4*risk), 250)
INVEST_CAP = 200.0
INVEST_Q_MULT = 0.8                    # follower return rate = (realised_q - 0.5) * 0.8
INVEST_SKILL_MULT = 0.6                # solo return rate = (skill - 0.5) * 0.6

# ---- learn ----
LEARN_RATE = 0.008                     # skill gain per learn hour: * (0.5 + grit), cap 1.0
LEARNER_DEAL_FLOOR = 0.55              # learners post only if the idea clears this quality

# ---- deals (same machinery as EP04/EP05 pitches) ----
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
assert FIRST[12] == RICH_NAME

# day plan (learn, deal, network, help, waste) in hours per day, by strategy
DAY_PLAN = {
    "waster":   (0, 0, 1, 0, 5),
    "learner":  (3, 1, 0, 1, 0),
    "hustler":  (0, 1, 2, 1, 0),
    "gambler":  (0, 2, 1, 0, 2),
    "dealer":   (1, 2, 1, 1, 0),
    "worker":   (1, 1, 1, 1, 1),
}

def pick_strategy(a):
    if a.work_ethic < 0.25 and a.risk > 0.40: return "waster"
    if a.skill > 0.55 and a.work_ethic > 0.55: return "learner"
    if a.risk > 0.55 and a.honesty > 0.55: return "hustler"
    if a.risk > 0.55 and a.honesty < 0.45: return "gambler"
    if a.skill > 0.50: return "dealer"
    return "worker"

def apply_rich_override(a):
    """The premise, not a draw: Richard keeps his know-how and his name.
    Shared by sim.py and the renderer (both must replay it identically)."""
    if a.name != RICH_NAME:
        return
    a.skill, a.work_ethic, a.risk, a.honesty = RICH_SKILL, RICH_GRIT, RICH_RISK, RICH_HONESTY
    a.money = RICH_START_MONEY
    a.rep = RICH_REP_START

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
    borrowed_total: float = 0.0
    interest_paid_total: float = 0.0
    days_borrowed: int = 0
    invest_total: float = 0.0
    invest_return_total: float = 0.0
    money_rank_day1: int = 0     # filled in after day 1

def trait_dict(a):
    return {"skill": round(a.skill, 2), "work_ethic": round(a.work_ethic, 2),
            "risk": round(a.risk, 2), "honesty": round(a.honesty, 2),
            "luck": round(a.luck, 2)}

def strongest_trait(a):
    # EP05/EP06: skill GROWS through the month (learning), so the honest
    # grouping is by the traits the winner STARTED with — end-state skill
    # is ~1.0 for every learner and would make the grouping degenerate.
    vals = [("skill", a.skill_start), ("grit", a.work_ethic), ("risk", a.risk),
            ("honesty", a.honesty), ("luck", a.luck)]
    return max(vals, key=lambda kv: kv[1])[0]

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
        apply_rich_override(a)
        a.strategy = pick_strategy(a)
        a.skill_start = a.skill
        a.peak_money = a.money

    events = []
    daily = []
    prev_leader = None
    total_hours = total_learn = total_waste = 0
    total_lies = total_caught = 0
    total_deals = total_flops = 0
    total_borrowed = total_interest = 0.0
    total_invest = total_invest_ret = 0.0
    leader_history = []   # (day, leader name, followers)
    rich_money_rank = []  # Richard's money rank each day

    for day in range(1, DAYS + 1):
        active = [a for a in agents if not a.bankrupt]
        # ---------------- credit phase: borrow in the morning ----------------
        borrowed_today = 0.0
        borrowed_by = {}
        for a in active:
            limit = CREDIT_BASE * a.rep * (RICH_CREDIT_MULT if a.name == RICH_NAME else 1.0)
            if a.name == RICH_NAME:
                amt = limit
            elif a.risk > 0.35:
                amt = limit * (0.3 + 0.7 * a.risk)
            elif a.money < DESPERATION_MONEY:
                amt = limit * 0.5
            else:
                amt = 0.0
            amt = round(amt, 2)
            borrowed_by[a.id] = amt
            if amt > 0:
                a.money += amt
                a.borrowed_total += amt
                a.days_borrowed += 1
                borrowed_today += amt
        total_borrowed += borrowed_today

        # ---------------- day phase: learn + deals ----------------
        deals = []
        day_hours = day_learn = day_waste = 0
        for a in active:
            nlearn, ndeal, nnet, nhelp, nwaste = DAY_PLAN[a.strategy]
            # learn: skill grows, capped at 1.0
            if nlearn:
                a.skill = min(1.0, a.skill + LEARN_RATE * nlearn * (0.5 + a.work_ethic))
                a.learn_hours += nlearn; day_learn += nlearn
            # networking only counts if there is someone to rally: a leader
            # with no followers spends those hours on nothing (they stay
            # unspent, i.e. offline attention) instead of shouting at nobody
            nnet_eff = nnet if a.followers_yesterday > 0 else 0
            # deals: learners post only when the idea is worth posting
            made = 0
            for _ in range(ndeal):
                q = 0.20 + 0.60 * a.skill + 0.20 * rng.random()
                if a.strategy == "learner" and q < LEARNER_DEAL_FLOOR:
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

        # ---------------- work phase ----------------
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
        for a in active:
            wage = (WAGE_BASE + WAGE_SKILL * a.skill) * (0.5 + 0.8 * a.work_ethic) \
                   * rng.uniform(0.85, 1.15)
            # investment: stake a share of today's money on the work done
            invest = min(a.money * (INVEST_FRAC_BASE + INVEST_FRAC_RISK * a.risk), INVEST_CAP)
            if a.leader_id >= 0:
                leader = agents[a.leader_id]
                if leader.bankrupt:
                    a.leader_id = -1
                    rate = (a.skill - 0.5) * INVEST_SKILL_MULT
                    inv_ret = invest * rate
                    a.money += wage + inv_ret - LIVING_COST
                    a.invest_total += invest; a.invest_return_total += inv_ret
                    total_invest += invest; total_invest_ret += inv_ret
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
                inv_ret = invest * (realised - 0.5) * INVEST_Q_MULT
                a.money += keep + inv_ret - LIVING_COST
                a.follower_bonus_earned += keep - wage
                a.invest_total += invest; a.invest_return_total += inv_ret
                total_invest += invest; total_invest_ret += inv_ret
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
                rate = (a.skill - 0.5) * INVEST_SKILL_MULT
                inv_ret = invest * rate
                a.money += wage + inv_ret - LIVING_COST
                a.invest_total += invest; a.invest_return_total += inv_ret
                total_invest += invest; total_invest_ret += inv_ret
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

        # ---------------- nightfall: repay the loan, then bankruptcy, snapshots ----------------
        interest_today = 0.0
        for a in active:
            amt = borrowed_by.get(a.id, 0.0)
            if amt > 0:
                rate = RICH_INTEREST if a.name == RICH_NAME else INTEREST
                due = amt * (1 + rate)
                a.money -= due
                a.interest_paid_total += amt * rate
                interest_today += amt * rate
        total_interest += interest_today
        for a in agents:
            if not a.bankrupt and a.money <= 0:
                a.money = 0.0; a.bankrupt = True; a.bankrupt_day = day
                events.append({"day": day, "type": "bankrupt", "who": a.name,
                               "detail": f"{a.name} ({a.strategy}) went broke on day {day}"})
            if not a.bankrupt:
                a.peak_money = max(a.peak_money, a.money)
        ranked = sorted(agents, key=lambda a: -a.money)
        rich = agents[12]
        rich_money_rank.append(ranked.index(rich) + 1)
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
            "mean_rep": round(sum(a.rep for a in act) / len(act), 3) if act else 0.0,
            "mean_skill": round(sum(a.skill for a in act) / len(act), 3) if act else 0.0,
            "borrowed_today": round(borrowed_today),
            "interest_today": round(interest_today, 1),
            "rich_money": round(rich.money),
            "rich_money_rank": ranked.index(rich) + 1,
            "rich_rep": round(rich.rep, 3),
            "rich_borrowed_today": round(borrowed_by.get(rich.id, 0.0)),
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
    rich = agents[12]
    most_skilled = max(agents, key=lambda a: a.skill)
    hardest = max(agents, key=lambda a: a.work_ethic)
    biggest_liar = max(agents, key=lambda a: a.lies_told)
    most_followed = max(agents, key=lambda a: a.followers_peak)
    biggest_waster = max(agents, key=lambda a: a.waste_hours)
    biggest_learner = max(agents, key=lambda a: a.learn_hours)
    biggest_borrower = max(agents, key=lambda a: a.borrowed_total)
    best_investor = max(agents, key=lambda a: a.invest_return_total)
    strat_counts = {}
    for s in ("waster", "learner", "hustler", "gambler", "dealer", "worker"):
        strat_counts[s] = sum(1 for a in agents if a.strategy == s)
    lead_changes = sum(1 for i in range(1, len(leader_history))
                       if leader_history[i]["leader"] != leader_history[i - 1]["leader"]
                       and leader_history[i]["leader"] is not None)
    distinct_leaders = len({h["leader"] for h in leader_history if h["leader"]})
    rich_days_money_no1 = sum(1 for r in rich_money_rank if r == 1)
    rich_days_top3 = sum(1 for r in rich_money_rank if r <= 3)

    def fate(a):
        return {"name": a.name, "strategy": a.strategy, "traits": trait_dict(a),
                "bankrupt": a.bankrupt,
                "bankrupt_day": a.bankrupt_day,
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
                "borrowed_total": round(a.borrowed_total),
                "interest_paid_total": round(a.interest_paid_total, 1),
                "days_borrowed": a.days_borrowed,
                "borrowed_per_day": round(a.borrowed_total / DAYS, 1),
                "invest_total": round(a.invest_total),
                "invest_return_total": round(a.invest_return_total),
                "money_rank_day1": a.money_rank_day1,
                "is_rich": a.name == RICH_NAME}
    log = {
        "seed": seed, "days": DAYS,
        "premise": "99 start with $100, Richard (ex-rich) starts $0 with skill 0.95, rep 0.85, 2x credit limit, 5% interest",
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
        "rich": fate(rich),
        "rich_money_rank_by_day": rich_money_rank,
        "rich_days_money_no1": rich_days_money_no1,
        "rich_days_top3": rich_days_top3,
        "final_leader": fate(max(agents, key=lambda a: len([x for x in agents if x.leader_id == a.id and not x.bankrupt]))),
        "most_skilled": fate(most_skilled),
        "hardest_worker": fate(hardest),
        "biggest_liar": fate(biggest_liar),
        "most_followed": fate(most_followed),
        "biggest_waster": fate(biggest_waster),
        "biggest_learner": fate(biggest_learner),
        "biggest_borrower": fate(biggest_borrower),
        "best_investor": fate(best_investor),
        "total_screen_hours": total_hours,
        "total_learn_hours": total_learn,
        "total_waste_hours": total_waste,
        "total_deals": total_deals,
        "total_lies": total_lies, "total_caught": total_caught,
        "total_flops": total_flops,
        "total_bankrupt": sum(1 for a in agents if a.bankrupt),
        "total_borrowed": round(total_borrowed),
        "total_interest": round(total_interest, 1),
        "total_invest": round(total_invest),
        "total_invest_return": round(total_invest_ret),
        "final_mean_rep": daily[-1]["mean_rep"] if daily else 0.0,
        "final_mean_skill": daily[-1]["mean_skill"] if daily else 0.0,
        "median_final_money": round(sorted(a.money for a in agents)[50]),
        "town_avg_learn_per_day": round(total_learn / (DAYS * N), 2),
        "town_avg_waste_per_day": round(total_waste / (DAYS * N), 2),
        "town_avg_screen_per_day": round(total_hours / (DAYS * N), 2),
        "town_avg_borrowed_per_day": round(total_borrowed / (DAYS * N), 1),
        "agents": [dict({"id": a.id, "name": a.name}, **fate(a)) for a in agents],
    }
    return log

if __name__ == "__main__":
    log = run()
    with open("sim_log.json", "w") as f:
        json.dump(log, f, indent=1)
    w = log["winner"]
    r = log["rich"]
    print("winner:", w["name"], w["strategy"], w["final_money"],
          "| runner-up:", log["runner_up"]["name"], log["runner_up"]["final_money"],
          "| margin:", log["winning_margin"], f"({log['winning_margin_pct']}%)")
    print("RICHARD: rank", r["final_rank"], "money", r["final_money"],
          "| borrowed total", r["borrowed_total"], "| invest return", r["invest_return_total"],
          "| days money #1:", log["rich_days_money_no1"], "| days top3:", log["rich_days_top3"])
    print("winner skill:", w["skill_start"], "->", w["skill_end"],
          "| learn/day:", w["learn_per_day"], "| waste/day:", w["waste_per_day"],
          "| borrowed/day:", w["borrowed_per_day"], "| invest return:", w["invest_return_total"])
    print("final leader (most followers):", log["final_leader"]["name"],
          log["final_leader"]["final_followers"], "followers")
    print("biggest waster:", log["biggest_waster"]["name"],
          log["biggest_waster"]["waste_per_day"], "hrs/day | rank",
          log["biggest_waster"]["final_rank"], "| money", log["biggest_waster"]["final_money"])
    print("biggest borrower:", log["biggest_borrower"]["name"],
          "borrowed", log["biggest_borrower"]["borrowed_total"], "| rank",
          log["biggest_borrower"]["final_rank"], "| money", log["biggest_borrower"]["final_money"])
    print("best investor:", log["best_investor"]["name"],
          "invest return", log["best_investor"]["invest_return_total"], "| rank",
          log["best_investor"]["final_rank"])
    print("biggest learner:", log["biggest_learner"]["name"],
          log["biggest_learner"]["learn_per_day"], "hrs/day | rank",
          log["biggest_learner"]["final_rank"])
    print("most followed:", log["most_followed"]["name"], "peak",
          log["most_followed"]["followers_peak"], "| rank", log["most_followed"]["final_rank"])
    print("biggest liar:", log["biggest_liar"]["name"], "lies",
          log["biggest_liar"]["lies_told"], "caught", log["biggest_liar"]["lies_caught"],
          "| rank", log["biggest_liar"]["final_rank"])
    print("borrowed:", log["total_borrowed"], "interest:", log["total_interest"],
          "invest:", log["total_invest"], "invest return:", log["total_invest_return"],
          "deals:", log["total_deals"], "lies:", log["total_lies"],
          "caught:", log["total_caught"], "flops:", log["total_flops"],
          "bankrupt:", log["total_bankrupt"])
    print("lead changes:", log["lead_changes"], "distinct leaders:", log["distinct_leaders"])
    print("strategy counts:", log["strategy_counts"])
    print("leader by day:", [(h["day"], h["leader"], h["followers"]) for h in log["leader_history"]])
    print("rich money rank by day:", log["rich_money_rank_by_day"])
    print("final mean skill:", log["final_mean_skill"], "| final mean rep:", log["final_mean_rep"])
