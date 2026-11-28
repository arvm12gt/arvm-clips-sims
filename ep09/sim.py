#!/usr/bin/env python3
"""
EP09 simulation: a town where everyone forgets yesterday — except one
person. 100 people, 30 days. Is the one who remembers a god or a madman?

Agent-based model. Fixed seed. Story comes from the output, not a script.

Premise (stated in the video): 100 people, each rolled from the same
five traits — skill, grit, risk, honesty, luck. Every morning, 99 of
them wake up and forget yesterday: who lied, who to trust, who they
followed, which projects flopped. ONE of them remembers everything.

What "memory" means in this model (the three channels it touches):
  1. REPUTATION is the town's memory. Each morning, every agent except
     the Rememberer has their reputation decayed 90% back toward neutral
     (0.5): yesterday's trust is gone. The Rememberer's reputation
     PERSISTS — he keeps the town's only written ledger, and a record
     does not forget: his own name is in it, entry by entry, so the
     town's trust in him compounds while everyone else's evaporates.
     The ledger cuts both ways: if the Rememberer lies, his lies are
     written down too, and his reputation crashes and never recovers
     (50-seed check: rememberer final-rep median 0.11 — most
     rememberers end as pariahs; only the honest ones keep rep ~1.0).
     Memory amplifies who you are; it does not forgive you.
  2. FOLLOW BONDS are memory. Each morning, every agent except the
     Rememberer wakes up leaderless (leader_id = -1) and with no crowd
     to rally (followers_yesterday = 0). The Rememberer keeps his leader
     and his crowd: he is the only one who can NETWORK, because he is
     the only one who remembers having followers.
  3. LIE KNOWLEDGE is memory. The Rememberer keeps a private ledger:
     every liar he has personally seen exposed goes into `known_liars`.
     Against a known liar his lie detection is near-certain (0.95) and
     he discounts their claims by half and halves their follow score.
     He also remembers which leaders' projects flopped in the last 3
     days and discounts them. Everyone else starts each day with a
     clean slate for every liar.

The rest of the economy is the same base as EP01-EP08: you LEARN
(skill grows — the only durable asset, and NOT memory: the town forgets
what happened but keeps what it learned), you post DEALS, you NETWORK
(only the Rememberer, see above), you HELP people (build trust) — or
you WASTE the hours. Leadership is not appointed: it emerges from who
others CHOOSE to follow, and a leader earns a share of their followers'
output. The winner is the richest agent on day 30.

The Rememberer is chosen by lottery (rng.randrange after the trait
draws) with NO trait override — memory is his ONLY difference. His
strategy is trait-derived like everyone else's.

Mechanics (all parameters below, all in REPRODUCE.md):
  - 100 people start with $100 each. Ranking is by money; money <= 0
    at day's end = bankrupt: out of the economy (followers leave, no
    wages, no deals), final money $0.
  - FORGETTING. Each morning, before work: every agent except the
    Rememberer has rep = 0.5 + (rep - 0.5) * 0.10, leader_id = -1,
    followers_yesterday = 0. The Rememberer is untouched.
  - LEARN. Each learn hour raises skill by 0.008 * (0.5 + grit),
    capped at 1.0. Skill is the town's only durable asset.
  - DEALS. Each deal proposes a group project with true quality
    q = 0.20 + 0.60*skill + 0.20*U(0,1). A liar may inflate the claim:
    with probability (1-honesty)*(0.4+0.6*risk) they claim
    q*(1+L), L = (0.15+0.60*risk)*U(0.5,1.2). Scholars post only if
    the idea clears 0.55 — they put their name on good ideas only.
  - LISTENING. Each agent samples 6 deals a day (weighted by the
    speaker's reputation — the trusted get heard), plus their current
    leader's deal if they have one. A listener may spot a lie:
    detection probability grows with their skill, their unspent hours
    (attention) and the lie's size. The FIRST listener to spot a lie
    exposes it publicly: the speaker's reputation takes a hit and
    every later listener discounts that deal. The Rememberer, against
    a KNOWN liar (in his ledger), detects with p = 0.95 and discounts
    the claim by half even before exposure; he also halves the follow
    score of known liars and discounts leaders who flopped in the
    last 3 days (x0.7).
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
    0.08*(0.5+reputation) to every follower's output that day. In
    this town only the Rememberer ever has followers_yesterday > 0,
    because only he remembers his crowd.
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
    up to 0.01. A caught lie costs 0.05 + 0.10*L. Every morning it
    decays 90% toward 0.5 for everyone except the Rememberer — his
    persists, because he keeps the ledger and his own name is written
    in it. The ledger cuts both ways: a lying Rememberer's reputation
    crashes and never recovers.
  - WAGES. Solo work pays (12 + 30*skill) * (0.5 + 0.8*grit) *
    U(0.85, 1.15), minus a $15 living cost — the same base economy
    as EP01-EP08, so learning and leadership income are visible on
    top of it.
"""
import json, random
from dataclasses import dataclass, field

SEED = 39   # featured run: Kevin (Rememberer) wins by $68; see REPRODUCE.md              # placeholder; the featured seed comes from scan_seeds.py
DAYS = 30
N = 100
START_MONEY = 100.0
LIVING_COST = 15.0
FREE_HOURS = 6

# ---- forgetting (the memory mechanic) ----
MEMORY_RETENTION = 0.10   # each morning, non-Rememberers keep 10% of yesterday's rep deviation from 0.5
REMEMBERER_DETECT = 0.95  # Rememberer's lie-detection p against a KNOWN liar
KNOWN_LIAR_CLAIM_DISCOUNT = 0.5  # Rememberer discounts a known liar's claim by half
KNOWN_LIAR_FOLLOW_DISCOUNT = 0.5 # ...and halves their follow score
FLOP_MEMORY_DAYS = 3      # Rememberer discounts leaders who flopped within this many days
FLOP_FOLLOW_DISCOUNT = 0.7

# ---- wages (same base economy as EP01-EP08) ----
WAGE_BASE, WAGE_SKILL = 12.0, 30.0     # wage = (12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)

# ---- learn ----
LEARN_RATE = 0.008                     # skill gain per learn hour: * (0.5 + grit), cap 1.0
SCHOLAR_DEAL_FLOOR = 0.55              # scholars post only if the idea clears this quality

# ---- deals (same machinery as EP04-EP08 pitches) ----
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
    "gambler":  (0, 2, 1, 0, 2),
    "schemer":  (0, 2, 1, 0, 2),
    "grinder":  (3, 1, 0, 1, 0),
    "scholar":  (2, 1, 1, 1, 0),
    "trader":   (0, 2, 1, 1, 0),
    "worker":   (1, 1, 1, 1, 1),
}

def pick_strategy(a):
    if a.risk > 0.55 and a.honesty > 0.45: return "gambler"
    if a.risk > 0.55 and a.honesty < 0.45: return "schemer"
    if a.work_ethic > 0.60: return "grinder"
    if a.skill > 0.60: return "scholar"
    if a.honesty > 0.60 and a.work_ethic > 0.50: return "trader"
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
    peak_money: float = START_MONEY
    skill_start: float = 0.0
    is_rememberer: bool = False      # the one agent who remembers yesterday
    known_liars: set = field(default_factory=set)  # agent ids whose lies the Rememberer has seen exposed
    lies_spotted: int = 0            # lies the Rememberer personally detected
    flopped_leaders: dict = field(default_factory=dict)  # leader id -> last flop day (Rememberer's ledger)
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
    money_rank_day1: int = 0     # filled in after day 1

def trait_dict(a):
    return {"skill": round(a.skill, 2), "work_ethic": round(a.work_ethic, 2),
            "risk": round(a.risk, 2), "honesty": round(a.honesty, 2),
            "luck": round(a.luck, 2)}

def strongest_trait(a):
    # EP05-EP09: skill GROWS through the month (learning), so the honest
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
    # --- the lottery: ONE agent remembers. Chosen by RNG, no trait override:
    # memory is his ONLY difference. (Renderer replays this exact draw.)
    rem = agents[rng.randrange(N)]
    rem.is_rememberer = True
    for a in agents:
        a.strategy = pick_strategy(a)
        a.skill_start = a.skill
        a.peak_money = a.money

    events = []
    daily = []
    prev_leader = None
    total_hours = total_learn = total_waste = 0
    total_lies = total_caught = 0
    total_deals = total_flops = 0
    leader_history = []   # (day, leader name, followers)
    rem_money_by_day = []
    rem_rank_by_day = []

    for day in range(1, DAYS + 1):
        active = [a for a in agents if not a.bankrupt]
        # ---------------- morning: the town forgets ----------------
        # Everyone except the Rememberer wakes up with yesterday wiped:
        # reputation decays 90% toward neutral, follow bonds dissolve,
        # yesterday's crowd is forgotten (no one to rally). The Rememberer
        # keeps all three — including his own reputation, which persists
        # because he keeps the ledger and his own name is written in it.
        for a in agents:
            if not a.is_rememberer:
                a.rep = 0.5 + (a.rep - 0.5) * MEMORY_RETENTION
                a.leader_id = -1
                a.followers_yesterday = 0

        # ---------------- day phase: learn + deals ----------------
        deals = []
        day_hours = day_learn = day_waste = 0
        for a in active:
            nlearn, ndeal, nnet, nhelp, nwaste = DAY_PLAN[a.strategy]
            # learn: skill grows, capped at 1.0 (skill is NOT memory: the
            # town forgets what happened but keeps what it learned)
            if nlearn:
                a.skill = min(1.0, a.skill + LEARN_RATE * nlearn * (0.5 + a.work_ethic))
                a.learn_hours += nlearn; day_learn += nlearn
            # networking only counts if there is someone to rally: in this
            # town only the Rememberer ever has followers_yesterday > 0,
            # because only he remembers his crowd
            nnet_eff = nnet if a.followers_yesterday > 0 else 0
            # deals: scholars post only when the idea is worth posting
            made = 0
            for _ in range(ndeal):
                q = 0.20 + 0.60 * a.skill + 0.20 * rng.random()
                if a.strategy == "scholar" and q < SCHOLAR_DEAL_FLOOR:
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
                    if a.is_rememberer and sp.id in a.known_liars:
                        pd = REMEMBERER_DETECT  # he remembers this liar
                    else:
                        pd = min(0.90, max(0.02, DETECT_BASE + DETECT_SKILL * a.skill
                                            + DETECT_ATTENTION * a.unspent + DETECT_LIE * p["L"]))
                    if rng.random() < pd:
                        p["exposed"] = True
                        sp.rep = max(0.02, sp.rep - (REP_LIE_CAUGHT + 0.10 * p["L"]))
                        sp.lies_caught += 1; total_caught += 1
                        if a.is_rememberer:
                            a.lies_spotted += 1
                            a.known_liars.add(sp.id)
                        if p["L"] >= 0.45:
                            events.append({"day": day, "type": "exposed", "who": sp.name,
                                           "detail": f"{sp.name} caught lying: claimed a project worth "
                                                     f"{p['claim']:.2f} that was really {p['q']:.2f}"})
                if p["exposed"]:
                    perceived = p["q"] * EXPOSED_DISCOUNT
                elif a.is_rememberer and sp.id in a.known_liars:
                    perceived = min(1.0, p["claim"]) * KNOWN_LIAR_CLAIM_DISCOUNT
                else:
                    perceived = p["claim"]
                perceived = min(1.0, perceived)
                score = perceived * (FOLLOW_REP_WEIGHT + (1 - FOLLOW_REP_WEIGHT) * sp.rep)
                score /= 1.0 + sp.followers_yesterday / SCORE_CROWD_DIVISOR
                if a.is_rememberer and sp.id in a.known_liars:
                    score *= KNOWN_LIAR_FOLLOW_DISCOUNT
                if a.is_rememberer and sp.id in a.flopped_leaders \
                        and day - a.flopped_leaders[sp.id] <= FLOP_MEMORY_DAYS:
                    score *= FLOP_FOLLOW_DISCOUNT
                if sp.id == a.leader_id:
                    score += LOYALTY_BONUS
                if score > best_score:
                    best_score = score; best = sp
            # the Rememberer writes down every liar he SAW exposed today —
            # he was in the room, he remembers it tomorrow
            if a.is_rememberer:
                for p in heard:
                    if p["exposed"]:
                        a.known_liars.add(p["speaker"].id)
            a.leader_id = best.id if best is not None else -1
            if best is not None:
                followers[best.id].append(a)
        for p in deals:
            if not p["lying"] and p["q"] >= 0.5 and not p["exposed"]:
                p["speaker"].rep = min(1.0, p["speaker"].rep + REP_HONEST_DEAL)

        # ---------------- work phase: wages ----------------
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
                    # the Rememberer writes the flop in his ledger, if he
                    # was standing in that crowd
                    if rem in fols:
                        rem.flopped_leaders[leader.id] = day
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

        # ---------------- nightfall: bankruptcy + snapshots ----------------
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
        rem_money_by_day.append(round(rem.money, 1))
        rem_rank_by_day.append(ranked.index(rem) + 1)
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
            "lies_today": sum(1 for p in deals if p["lying"]),
            "lies_caught_today": sum(1 for p in deals if p["exposed"]),
            "rememberer_money": round(rem.money, 1),
            "rememberer_rank": ranked.index(rem) + 1,
            "known_liars": len(rem.known_liars),
            "rememberer_lies_spotted": rem.lies_spotted,
            "screen_hours": day_hours,
            "learn_hours_day": day_learn,
            "waste_hours_day": day_waste,
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
    top_grinder = max((a for a in agents if a.strategy == "grinder"),
                      key=lambda a: a.money, default=None)
    top_schemer = max((a for a in agents if a.strategy == "schemer"),
                      key=lambda a: a.money, default=None)
    strat_counts = {}
    for s in ("gambler", "schemer", "grinder", "scholar", "trader", "worker"):
        strat_counts[s] = sum(1 for a in agents if a.strategy == s)
    lead_changes = sum(1 for i in range(1, len(leader_history))
                       if leader_history[i]["leader"] != leader_history[i - 1]["leader"]
                       and leader_history[i]["leader"] is not None)
    distinct_leaders = len({h["leader"] for h in leader_history if h["leader"]})
    rem_days_money_no1 = sum(1 for r in rem_rank_by_day if r == 1)
    rem_days_top3 = sum(1 for r in rem_rank_by_day if r <= 3)

    def fate(a):
        return {"name": a.name, "strategy": a.strategy, "traits": trait_dict(a),
                "bankrupt": a.bankrupt,
                "bankrupt_day": a.bankrupt_day,
                "final_rank": ranked.index(a) + 1, "final_money": round(a.money),
                "peak_money": round(a.peak_money), "final_rep": round(a.rep, 3),
                "skill_start": round(a.skill_start, 3),
                "skill_end": round(a.skill, 3),
                "skill_gain": round(a.skill - a.skill_start, 3),
                "is_rememberer": a.is_rememberer,
                "lies_spotted": a.lies_spotted,
                "known_liars": len(a.known_liars),
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
                "money_rank_day1": a.money_rank_day1}
    log = {
        "seed": seed, "days": DAYS,
        "premise": "100 start with $100; every morning the 99 forget yesterday (rep decays 90% to 0.5, follow bonds dissolve, crowds forgotten) and ONE agent remembers everything (keeps leader, keeps crowd, keeps a ledger of liars and flops)",
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
        "rememberer": fate(rem),
        "rememberer_money_by_day": rem_money_by_day,
        "rememberer_rank_by_day": rem_rank_by_day,
        "rememberer_days_money_no1": rem_days_money_no1,
        "rememberer_days_top3": rem_days_top3,
        "top_grinder": fate(top_grinder) if top_grinder is not None else None,
        "top_schemer": fate(top_schemer) if top_schemer is not None else None,
        "final_leader": fate(max(agents, key=lambda a: len([x for x in agents if x.leader_id == a.id and not x.bankrupt]))),
        "most_skilled": fate(most_skilled),
        "hardest_worker": fate(hardest),
        "biggest_liar": fate(biggest_liar),
        "most_followed": fate(most_followed),
        "biggest_waster": fate(biggest_waster),
        "biggest_learner": fate(biggest_learner),
        "total_screen_hours": total_hours,
        "total_learn_hours": total_learn,
        "total_waste_hours": total_waste,
        "total_deals": total_deals,
        "total_lies": total_lies, "total_caught": total_caught,
        "total_flops": total_flops,
        "total_bankrupt": sum(1 for a in agents if a.bankrupt),
        "final_mean_rep": daily[-1]["mean_rep"] if daily else 0.0,
        "final_mean_skill": daily[-1]["mean_skill"] if daily else 0.0,
        "median_final_money": round(sorted(a.money for a in agents)[50]),
        "town_avg_learn_per_day": round(total_learn / (DAYS * N), 2),
        "town_avg_waste_per_day": round(total_waste / (DAYS * N), 2),
        "town_avg_screen_per_day": round(total_hours / (DAYS * N), 2),
        "agents": [dict({"id": a.id, "name": a.name}, **fate(a)) for a in agents],
    }
    return log

if __name__ == "__main__":
    log = run()
    with open("sim_log.json", "w") as f:
        json.dump(log, f, indent=1)
    w = log["winner"]
    r = log["rememberer"]
    print("winner:", w["name"], w["strategy"], w["final_money"],
          "| runner-up:", log["runner_up"]["name"], log["runner_up"]["final_money"],
          "| margin:", log["winning_margin"], f"({log['winning_margin_pct']}%)")
    print("REMEMBERER:", r["name"], r["strategy"], "| rank", r["final_rank"],
          "| money", r["final_money"], "| rep", r["final_rep"],
          "| lies spotted", r["lies_spotted"], "| known liars", r["known_liars"],
          "| followers peak", r["followers_peak"], "| days money #1:",
          log["rememberer_days_money_no1"], "| days top3:", log["rememberer_days_top3"])
    print("winner skill:", w["skill_start"], "->", w["skill_end"],
          "| learn/day:", w["learn_per_day"], "| waste/day:", w["waste_per_day"],
          "| leadership income:", w["leadership_income"])
    print("final leader (most followers):", log["final_leader"]["name"],
          log["final_leader"]["final_followers"], "followers")
    print("biggest liar:", log["biggest_liar"]["name"], "lies",
          log["biggest_liar"]["lies_told"], "caught", log["biggest_liar"]["lies_caught"],
          "| rank", log["biggest_liar"]["final_rank"], "| money", log["biggest_liar"]["final_money"])
    print("top schemer:", log["top_schemer"]["name"] if log["top_schemer"] else None,
          "$", log["top_schemer"]["final_money"] if log["top_schemer"] else None,
          "| rank", log["top_schemer"]["final_rank"] if log["top_schemer"] else None,
          "| lies", log["top_schemer"]["lies_told"] if log["top_schemer"] else None)
    print("top grinder:", log["top_grinder"]["name"] if log["top_grinder"] else None,
          "$", log["top_grinder"]["final_money"] if log["top_grinder"] else None,
          "| rank", log["top_grinder"]["final_rank"] if log["top_grinder"] else None)
    print("lies:", log["total_lies"], "caught:", log["total_caught"],
          "flops:", log["total_flops"], "bankrupt:", log["total_bankrupt"])
    print("lead changes:", log["lead_changes"], "distinct leaders:", log["distinct_leaders"])
    print("strategy counts:", log["strategy_counts"])
    print("leader by day:", [(h["day"], h["leader"], h["followers"]) for h in log["leader_history"]])
    print("rememberer rank by day:", log["rememberer_rank_by_day"])
    print("final mean skill:", log["final_mean_skill"], "| final mean rep:", log["final_mean_rep"])
