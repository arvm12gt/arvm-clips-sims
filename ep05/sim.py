#!/usr/bin/env python3
"""
EP05 simulation: a Roman-era market town of 100 people. Each person is
given a modern smartphone — charged, with a preloaded offline library
(encyclopedia, maps, calculator, camera, notes, games), and a local mesh
chat so phones can message nearby phones. NO internet: nothing arrives
from the outside world; everything the phone can do, it does offline.
After 30 days — who wins?

Agent-based model. Fixed seed. Story comes from the output, not a script.

Premise (stated in the video): the phone is a tool or a trap depending
on where the hours go. Each person has 6 phone hours a day, after work.
Phone time does real work: you STUDY the encyclopedia (skill grows),
you post OFFERS on the mesh (trade), you MESSAGE people (coordinate,
rally followers), you share helpful TIPS (build trust) — or you SCROLL
games and photos (nothing), or SPREAD rumours (mislead rivals, get
caught). Leadership is not appointed: it emerges from who others CHOOSE
to follow, and a leader earns a share of their followers' coordinated
output. The winner is the richest agent on day 30 (same scoring as
EP01-EP04).

Traits per agent (0..1), drawn in this fixed order:
  skill, work_ethic (grit), risk_appetite, honesty, luck
Honesty is an ordinary trait spread across the whole town; anyone may lie.

Strategy labels are derived from traits (checked in this order):
  - doomscroller : grit < 0.25 and risk > 0.40 (can't focus; the phone
    eats the day — 5 hours scrolling, 1 hour messaging, nothing else)
  - scholar      : skill > 0.55 and grit > 0.55 (studies the library:
    3 study hours a day, skill grows)
  - influencer   : risk > 0.55 and honesty > 0.55 (bold, trusted: talks
    to the whole mesh, 2 message hours a day)
  - schemer      : risk > 0.55 and honesty < 0.45 (spreads rumours:
    lies in offers, 2 scroll hours to watch the damage)
  - merchant     : skill > 0.50 (trades: 2 offers a day)
  - worker       : everyone else (a bit of everything)

Phone plan (study, offer, message, tip, scroll) in hours per day:
  doomscroller (0, 0, 1, 0, 5) = 6 spent, 0 left
  scholar      (3, 1, 0, 1, 0) = 5 spent, 1 left
  influencer   (0, 1, 2, 1, 0) = 4 spent, 2 left
  schemer      (0, 2, 1, 0, 2) = 5 spent, 1 left
  merchant     (1, 2, 1, 1, 0) = 5 spent, 1 left
  worker       (1, 1, 1, 1, 1) = 5 spent, 1 left
Unspent hours are OFFLINE time: attention. A person with hours left
over spots lies better — the doomscroller, phone in hand all day,
spots almost nothing. Scrolling counts as spent: it consumes attention
too, it just produces nothing.

Mechanics (all parameters below, all in REPRODUCE.md):
  - Everyone starts with $1,000. Ranking is by money; money <= 0 at
    day's end = bankrupt: out of the economy (followers leave, no
    wages, no offers), final money $0.
  - STUDY. Each study hour raises skill by 0.008 * (0.5 + grit),
    capped at 1.0. Skill is the town's only durable asset: it raises
    wages and offer quality. A scholar studying 3 hours a day gains
    roughly 0.02 skill a day — about +0.6 over the month if they keep
    at it. Learning compounds; scrolling does not.
  - OFFERS. Each offer proposes a group project with true quality
    q = 0.20 + 0.60*skill + 0.20*U(0,1). A liar may inflate the claim:
    with probability (1-honesty)*(0.4+0.6*risk) they claim
    q*(1+L), L = (0.15+0.60*risk)*U(0.5,1.2). Scholars post only if
    the idea clears 0.55 — they put their name on good ideas only.
  - LISTENING. Each agent samples 6 offers a day (weighted by the
    speaker's reputation — the trusted get heard), plus their current
    leader's offer if they have one. A listener may spot a lie:
    detection probability grows with their skill, their unspent hours
    (attention) and the lie's size. The FIRST listener to spot a lie
    exposes it publicly: the speaker's reputation takes a hit and
    every later listener discounts that offer. An exposed lie is
    narratable; a small lie that nobody spots still pays.
  - FOLLOWING. Each listener follows the best offer they heard,
    scored by perceived quality x (0.35+0.65*speaker reputation),
    with a small loyalty bonus for staying with their current leader.
    A big crowd also dilutes the score a little (divided by
    1 + followers/60). If no offer scores above the threshold they
    work solo. Following is a real economic choice: a follower's
    output is boosted by the leader's skill (1 + 0.30*leader skill,
    diluted as the crowd grows), the follower keeps 90% of it, and
    the leader takes a 10% share of every follower's output — a share
    that also thins with crowd size. A leader's own output also grows
    with their following (1 + 0.02 per follower, capped at 15).
  - MESSAGES. A leader may spend hours messaging — but only if they
    actually have followers to message. Each message hour adds
    0.08*(0.5+reputation) to every follower's output that day.
  - PROJECTS CAN FLOP. The followed project's realised quality is
    its offer quality plus execution noise U(-0.12, 0.12), drawn once
    per leader per day. Below 0.50 it flops: followers' output x0.7
    and the leader's reputation drops 0.02.
  - TIPS. One hour of helpful tips raises reputation a little
    (0.012 if honesty > 0.5). From a liar it is cheap talk: +0.004,
    with a 15% chance of being read as flattery (-0.02).
  - REPUTATION (0.02..1.0, starts 0.5) is public and is the town's
    memory. It steers who gets heard (sampling weights), who gets
    followed (follow score), and message power. A delivered honest
    offer (q >= 0.5, no lie) adds 0.01; a successful coordination
    day adds up to 0.01. A caught lie costs 0.05 + 0.10*L.
  - WAGES. Solo work pays (12 + 30*skill) * (0.5 + 0.8*grit) *
    U(0.85, 1.15), minus a $15 living cost — the same base economy
    as EP01-EP04, so learning and leadership income are visible on
    top of it. Skill grows through the month, so wages grow with it.
"""
import json, random
from dataclasses import dataclass

SEED = 55           # placeholder; featured seed chosen by the disclosed seed scan (see REPRODUCE.md)
DAYS = 30
N = 100
START_MONEY = 1000.0
LIVING_COST = 15.0
PHONE_HOURS = 6

# ---- wages (same base economy as EP01-EP04) ----
WAGE_BASE, WAGE_SKILL = 12.0, 30.0     # wage = (12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)

# ---- study ----
STUDY_RATE = 0.008                     # skill gain per study hour: * (0.5 + grit), cap 1.0
SCHOLAR_OFFER_FLOOR = 0.55             # scholars post only if the idea clears this quality

# ---- offers (same machinery as EP04 pitches) ----
OFFER_COST = 1                         # 1 phone hour per offer
OFFERS_HEARD = 6                       # offers a listener samples per day (+ current leader's)
FOLLOW_THRESHOLD = 0.30                # min follow score, else work solo
LOYALTY_BONUS = 0.04                   # score bonus for staying with current leader
REP_HEAR_WEIGHT = 0.20                 # sampling weight = (0.20 + rep) x (4 / offers made today)
FOLLOW_REP_WEIGHT = 0.35               # follow score = perceived q * (0.35 + 0.65*rep)

# ---- lies & detection ----
LIE_BASE, LIE_RISK = 0.15, 0.60        # L = (0.15 + 0.60*risk) * U(0.5, 1.2)
REP_LIE_CAUGHT = 0.05                  # rep hit: + 0.10 * L on top
DETECT_BASE, DETECT_SKILL = 0.08, 0.35 # p_detect = 0.08 + 0.35*skill + 0.02*unspent + 0.25*L
DETECT_ATTENTION, DETECT_LIE = 0.02, 0.25
EXPOSED_DISCOUNT = 0.80                # exposed offer perceived at 80% of true quality

# ---- coordination ----
COORD_SKILL_BONUS = 0.30               # follower output x (1 + 0.30*leader skill), crowd-diluted
COORD_CROWD_DIVISOR = 30.0             # skill bonus divided by (1 + followers/30)
LEADER_SHARE = 0.10                    # leader takes 10% of each follower's output, crowd-thinned
LEADER_SHARE_DIVISOR = 20.0            # share rate divided by (1 + followers/20)
LEADER_CROWD_BONUS = 0.02              # leader's own output +2% per follower, cap 15
LEADER_CROWD_CAP = 15
RALLY_BOOST = 0.08                     # per message hour: +0.08*(0.5+rep) follower output
FLOP_NOISE = 0.12                      # realised quality = offer q + U(-0.12, 0.12), once per leader/day
FLOP_THRESHOLD = 0.50                  # realised quality below this = flop
SCORE_CROWD_DIVISOR = 60.0             # follow score divided by (1 + followers/60)
FLOP_OUTPUT = 0.70                     # flop: followers' output x0.7
REP_FLOP = 0.02
REP_HONEST_OFFER = 0.01                # delivered honest offer with q >= 0.5
REP_COORD_DAY = 0.01                   # successful coordination day (scaled by followers/10)

# ---- tips ----
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

# phone plan (study, offer, message, tip, scroll) in hours per day, by strategy
PHONE_PLAN = {
    "doomscroller": (0, 0, 1, 0, 5),
    "scholar":      (3, 1, 0, 1, 0),
    "influencer":   (0, 1, 2, 1, 0),
    "schemer":      (0, 2, 1, 0, 2),
    "merchant":     (1, 2, 1, 1, 0),
    "worker":       (1, 1, 1, 1, 1),
}

def pick_strategy(a):
    if a.work_ethic < 0.25 and a.risk > 0.40: return "doomscroller"
    if a.skill > 0.55 and a.work_ethic > 0.55: return "scholar"
    if a.risk > 0.55 and a.honesty > 0.55: return "influencer"
    if a.risk > 0.55 and a.honesty < 0.45: return "schemer"
    if a.skill > 0.50: return "merchant"
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
    leader_id: int = -1          # who this agent follows (-1 = solo)
    followers_yesterday: int = 0  # followers at end of yesterday (message only if > 0)
    messages_today: int = 0       # effective message hours spent today
    unspent: int = 0              # phone hours left over today (= offline attention, for lie detection)
    hours_spent: int = 0
    study_hours: int = 0
    scroll_hours: int = 0
    offers: int = 0
    messages: int = 0
    tips: int = 0
    lies_told: int = 0
    lies_caught: int = 0
    followers_peak: int = 0
    days_as_leader: int = 0      # days as the town's most-followed leader
    leadership_income: float = 0.0  # share collected from followers
    follower_bonus_earned: float = 0.0  # extra output earned by following vs solo
    projects_led: int = 0        # days leading >=1 follower
    projects_flopped: int = 0

def trait_dict(a):
    return {"skill": round(a.skill, 2), "work_ethic": round(a.work_ethic, 2),
            "risk": round(a.risk, 2), "honesty": round(a.honesty, 2),
            "luck": round(a.luck, 2)}

def strongest_trait(a):
    # EP05: skill GROWS through the month (study), so the honest grouping
    # is by the traits the winner STARTED with — end-state skill is ~1.0
    # for every scholar and would make the grouping degenerate (skill
    # 100/100, an artifact of the cap, not a finding). EP01-EP04 traits
    # never changed, so start == end there; here only the start grouping
    # says anything about who wins.
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
        a.strategy = pick_strategy(a)
        a.skill_start = a.skill

    events = []
    daily = []
    prev_leader = None
    total_hours = total_study = total_scroll = 0
    total_lies = total_caught = 0
    total_offers = total_flops = 0
    leader_history = []   # (day, leader name, followers)

    for day in range(1, DAYS + 1):
        active = [a for a in agents if not a.bankrupt]
        # ---------------- phone phase: study + offers ----------------
        offers = []
        day_hours = day_study = day_scroll = 0
        for a in active:
            nstudy, noffer, nmsg, ntip, nscroll = PHONE_PLAN[a.strategy]
            # study: skill grows, capped at 1.0
            if nstudy:
                a.skill = min(1.0, a.skill + STUDY_RATE * nstudy * (0.5 + a.work_ethic))
                a.study_hours += nstudy; day_study += nstudy
            # messages only count if there is someone to message: a leader
            # with no followers spends those hours on nothing (they stay
            # unspent, i.e. offline attention) instead of shouting at nobody
            nmsg_eff = nmsg if a.followers_yesterday > 0 else 0
            # offers: scholars post only when the idea is worth posting
            made = 0
            for _ in range(noffer):
                q = 0.20 + 0.60 * a.skill + 0.20 * rng.random()
                if a.strategy == "scholar" and q < SCHOLAR_OFFER_FLOOR:
                    continue   # saves the hour: it becomes offline attention
                lying = rng.random() < (1 - a.honesty) * (0.4 + 0.6 * a.risk)
                if lying:
                    L = (LIE_BASE + LIE_RISK * a.risk) * rng.uniform(0.5, 1.2)
                    claim = min(1.2, q * (1 + L))
                    a.lies_told += 1; total_lies += 1
                else:
                    L = 0.0; claim = q
                offers.append({"speaker": a, "q": q, "claim": claim,
                               "lying": lying, "L": L, "exposed": False})
                made += 1
            spent = nstudy + made * OFFER_COST + nmsg_eff + ntip + nscroll
            spent = min(spent, PHONE_HOURS)
            a.hours_spent += spent
            day_hours += spent
            a.scroll_hours += nscroll; day_scroll += nscroll
            a.offers += made; a.messages += nmsg_eff; a.tips += ntip
            a.messages_today = nmsg_eff
            a.unspent = PHONE_HOURS - spent   # offline attention, for detection
            # tips
            for _ in range(ntip):
                if a.honesty > 0.5:
                    a.rep = min(1.0, a.rep + REP_TRUST_HONEST)
                else:
                    if rng.random() < FLATTERY_P:
                        a.rep = max(0.02, a.rep - REP_FLATTERY)
                    else:
                        a.rep = min(1.0, a.rep + REP_TRUST_CHEAP)
        total_hours += day_hours
        total_study += day_study
        total_scroll += day_scroll
        total_offers += len(offers)

        # ---------------- listening & following ----------------
        made_count = {}
        for p in offers:
            made_count[p["speaker"].id] = made_count.get(p["speaker"].id, 0) + 1
        weights = [(REP_HEAR_WEIGHT + p["speaker"].rep) * (4.0 / made_count[p["speaker"].id])
                   for p in offers]
        wsum = sum(weights)
        followers = {a.id: [] for a in active}   # leader id -> follower agents
        for a in active:
            heard = []
            if offers and wsum > 0:
                idxs = set()
                tries = 0
                while len(idxs) < min(OFFERS_HEARD, len(offers)) and tries < 40:
                    tries += 1
                    x = rng.random() * wsum
                    for j, w in enumerate(weights):
                        x -= w
                        if x <= 0:
                            idxs.add(j); break
                heard = [offers[j] for j in idxs]
            if a.leader_id >= 0:
                for p in offers:
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
        for p in offers:
            if not p["lying"] and p["q"] >= 0.5 and not p["exposed"]:
                p["speaker"].rep = min(1.0, p["speaker"].rep + REP_HONEST_OFFER)

        # ---------------- work phase ----------------
        realised_q = {}
        for a in active:
            fols = followers.get(a.id, [])
            if not fols:
                continue
            loffer = None
            for p in offers:
                if p["speaker"] is a:
                    loffer = p; break
            realised_q[a.id] = (loffer["q"] + rng.uniform(-FLOP_NOISE, FLOP_NOISE)) if loffer else 0.5
        rally_mult = {}
        for a in active:
            fols = followers.get(a.id, [])
            if fols and a.messages_today > 0:
                rally_mult[a.id] = 1.0 + RALLY_BOOST * a.messages_today * (0.5 + a.rep)
                if len(fols) >= 15:
                    events.append({"day": day, "type": "rally", "who": a.name,
                                   "detail": f"{a.name} messages {len(fols)} followers "
                                             f"({a.messages_today} hour{'s' if a.messages_today > 1 else ''})"})
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

        # ---------------- end of day: bankruptcy, snapshots ----------------
        for a in agents:
            if not a.bankrupt and a.money <= 0:
                a.money = 0.0; a.bankrupt = True; a.bankrupt_day = day
                events.append({"day": day, "type": "bankrupt", "who": a.name,
                               "detail": f"{a.name} ({a.strategy}) went broke on day {day}"})
            if not a.bankrupt:
                a.peak_money = max(a.peak_money, a.money)
        ranked = sorted(agents, key=lambda a: -a.money)
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
            "screen_hours": day_hours,
            "study_hours_day": day_study,
            "scroll_hours_day": day_scroll,
            "lies_told_day": sum(1 for p in offers if p["lying"]),
            "lies_caught_day": sum(1 for p in offers if p["exposed"]),
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
    biggest_scroller = max(agents, key=lambda a: a.scroll_hours)
    biggest_learner = max(agents, key=lambda a: a.study_hours)
    strat_counts = {}
    for s in ("doomscroller", "scholar", "influencer", "schemer", "merchant", "worker"):
        strat_counts[s] = sum(1 for a in agents if a.strategy == s)
    lead_changes = sum(1 for i in range(1, len(leader_history))
                       if leader_history[i]["leader"] != leader_history[i - 1]["leader"]
                       and leader_history[i]["leader"] is not None)
    distinct_leaders = len({h["leader"] for h in leader_history if h["leader"]})

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
                "study_hours": a.study_hours,
                "study_per_day": round(a.study_hours / DAYS, 2),
                "scroll_hours": a.scroll_hours,
                "scroll_per_day": round(a.scroll_hours / DAYS, 2),
                "offers": a.offers, "messages": a.messages, "tips": a.tips,
                "lies_told": a.lies_told, "lies_caught": a.lies_caught,
                "leadership_income": round(a.leadership_income),
                "follower_bonus_earned": round(a.follower_bonus_earned),
                "projects_led": a.projects_led, "projects_flopped": a.projects_flopped}
    log = {
        "seed": seed, "days": DAYS,
        "premise": "smartphones, no internet; 6 phone hours/day; skill grows by study",
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
        "biggest_scroller": fate(biggest_scroller),
        "biggest_learner": fate(biggest_learner),
        "total_screen_hours": total_hours,
        "total_study_hours": total_study,
        "total_scroll_hours": total_scroll,
        "total_offers": total_offers,
        "total_lies": total_lies, "total_caught": total_caught,
        "total_flops": total_flops,
        "total_bankrupt": sum(1 for a in agents if a.bankrupt),
        "final_mean_rep": daily[-1]["mean_rep"] if daily else 0.0,
        "final_mean_skill": daily[-1]["mean_skill"] if daily else 0.0,
        "median_final_money": round(sorted(a.money for a in agents)[50]),
        "town_avg_study_per_day": round(total_study / (DAYS * N), 2),
        "town_avg_scroll_per_day": round(total_scroll / (DAYS * N), 2),
        "town_avg_screen_per_day": round(total_hours / (DAYS * N), 2),
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
          "| study/day:", w["study_per_day"], "| scroll/day:", w["scroll_per_day"],
          "| town avg study:", log["town_avg_study_per_day"],
          "| town avg scroll:", log["town_avg_scroll_per_day"])
    print("final leader (most followers):", log["final_leader"]["name"],
          log["final_leader"]["final_followers"], "followers")
    print("biggest scroller:", log["biggest_scroller"]["name"],
          log["biggest_scroller"]["scroll_per_day"], "hrs/day | rank",
          log["biggest_scroller"]["final_rank"], "| money", log["biggest_scroller"]["final_money"])
    print("biggest learner:", log["biggest_learner"]["name"],
          log["biggest_learner"]["study_per_day"], "hrs/day | rank",
          log["biggest_learner"]["final_rank"])
    print("most followed:", log["most_followed"]["name"], "peak",
          log["most_followed"]["followers_peak"], "| rank", log["most_followed"]["final_rank"])
    print("biggest liar:", log["biggest_liar"]["name"], "lies",
          log["biggest_liar"]["lies_told"], "caught", log["biggest_liar"]["lies_caught"],
          "| rank", log["biggest_liar"]["final_rank"])
    print("screen hrs:", log["total_screen_hours"], "study:", log["total_study_hours"],
          "scroll:", log["total_scroll_hours"], "offers:", log["total_offers"],
          "lies:", log["total_lies"], "caught:", log["total_caught"],
          "flops:", log["total_flops"], "bankrupt:", log["total_bankrupt"])
    print("lead changes:", log["lead_changes"], "distinct leaders:", log["distinct_leaders"])
    print("strategy counts:", log["strategy_counts"])
    print("leader by day:", [(h["day"], h["leader"], h["followers"]) for h in log["leader_history"]])
    print("final mean skill:", log["final_mean_skill"], "| final mean rep:", log["final_mean_rep"])
