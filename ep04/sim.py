#!/usr/bin/env python3
"""
EP04 simulation: a town of 100 people. Each person may speak only
10 sentences a day. After 30 days — who becomes the leader?
Agent-based model. Fixed seed. Story comes from the output, not a script.

Premise (stated in the video): speech is the scarce resource. Speaking
costs a sentence; listening is free. Speech does real work: you pitch
projects, rally followers, build trust — or lie. Leadership is not
appointed: it emerges from who others CHOOSE to follow, and a leader
earns a share of their followers' coordinated output. The winner is the
richest agent on day 30 (same scoring as EP01-EP03), and leadership is
the mechanism that gets them there — the richest agent is usually also
the most-followed one, which the log lets you check.

Traits per agent (0..1), drawn in this fixed order:
  skill, work_ethic (grit), risk_appetite, honesty, luck
Unlike EP03 there is no designated honest one: honesty is a normal
trait spread across the whole town, and every agent may lie.

Strategy labels are derived from traits (checked in this order):
  - loudmouth : risk > 0.60 and honesty < 0.45 (talks constantly, lies often)
  - listener  : honesty > 0.60 and risk < 0.40 (quiet, speaks rarely,
    and only when the idea is worth saying — checked BEFORE orator on
    purpose: what makes a listener is how little they speak, not how
    little they know. A skilled, honest, low-risk person IS a listener
    in this town: one selective pitch a day, not two.)
  - orator    : skill > 0.55 and honesty > 0.55 (skilled, honest speaker
    who talks more: two pitches, two rallies, two trust-talks a day)
  - schemer   : risk > 0.55 and skill > 0.50   (calculated deception)
  - worker    : everyone else

Speech budget: 10 sentences per day. A pitch costs 2, a rally 1,
a trust-talk 1. Unspent sentences are not wasted: they are ATTENTION.
A listener who saves sentences hears lies better — each unspent
sentence adds to lie detection — so the quiet pay for silence with
judgement, and the loud pay for volume with blindness. Daily budgets:
  loudmouth 4 pitches + 1 rally + 1 trust = 10 spent (0 left)
  orator    2 pitches + 2 rallies + 2 trust = 8 spent (2 left)
  schemer   2 pitches + 1 rally + 1 trust = 6 spent (4 left)
  worker    1 pitch + 1 rally + 1 trust = 4 spent (6 left)
  listener  1 pitch + 1 rally + 0 trust = 3 spent (7 left)
Two quiet-person rules, both part of the premise, not a thumb on
the scales: (1) WHEN THE QUIET ONE SPEAKS, THE ROOM GOES QUIET —
a speaker's pitches are sampled for listening with weight
(0.20 + reputation) x (4 / pitches they made today), so one pitch
from a listener gets four times the hearing of each of a loudmouth's
four; total airtime per speaker is roughly equal, quality decides.
(2) A listener speaks only when it is worth saying: they pitch only
if the idea's quality clears 0.55, otherwise they save the sentences
(they stay unspent, i.e. attention). Nobody else filters — loudmouths
pitch whatever comes to mind.

Mechanics (all parameters below, all in REPRODUCE.md):
  - Everyone starts with $1,000. Ranking is by money; money <= 0 at
    day's end = bankrupt: out of the economy (followers leave, no
    wages, no pitches), final money $0.
  - PITCHES. Each pitch proposes a group project with true quality
    q = 0.20 + 0.60*skill + 0.20*U(0,1). A liar may inflate the claim:
    with probability (1-honesty)*(0.4+0.6*risk) they claim
    q*(1+L), L = (0.15+0.60*risk)*U(0.5,1.2).
  - LISTENING. Listening is free, but attention is limited: each
    agent samples 6 pitches a day (weighted by the speaker's
    reputation — the trusted get heard), plus their current leader's
    pitch if they have one. A listener may spot a lie: detection
    probability grows with their skill, their unspent sentences
    (attention) and the lie's size. The FIRST listener to spot a lie
    exposes it publicly: the speaker's reputation takes a hit and
    every later listener discounts that pitch. An exposed lie is
    narratable; a small lie that nobody spots still pays.
  - FOLLOWING. Each listener follows the best pitch they heard,
    scored by perceived quality x (0.35+0.65*speaker reputation),
    with a small loyalty bonus for staying with their current leader.
    A big crowd also dilutes the score a little (divided by
    1 + followers/60): followers prefer a good leader with room over
    a great leader with 60 people already shouting for attention.
    If no pitch scores above the threshold they work solo. Following
    is a real economic choice, not a vote: a follower's output is
    boosted by the leader's skill (1 + 0.30*leader skill, diluted
    as the crowd grows: a leader's attention spreads thin, so the
    bonus is divided by (1 + followers/30)), the follower keeps 90%
    of it, and the leader takes a 10% share of every follower's
    output — a share that also thins with crowd size
    (10% / (1 + followers/20)). Following a skilled, honest leader
    with a small crowd pays better than solo work; following a loud
    fraud in a huge crowd pays worse, so crowds split instead of
    piling onto one person forever. A leader's own output also grows
    with their following (1 + 0.02 per follower, capped at 15
    followers): a crowd makes the leader's own project bigger too.
  - RALLIES. A leader may spend sentences rallying — but only if
    they actually have followers to rally (sentences are spent only
    when they count). Each rally adds 0.08*(0.5+reputation) to every
    follower's output that day. Rallying a following is the
    highest-leverage sentence in town — which is why the loud burn
    their budget shouting at nobody by noon.
  - PROJECTS CAN FLOP. The followed project's realised quality is
    its pitch quality plus execution noise U(-0.12, 0.12), drawn once
    per leader per day — the whole crowd shares one outcome. Below
    0.50 it flops: followers' output x0.7 and the leader's reputation
    drops 0.02. Great projects never flop; mediocre ones and liars'
    inflated ones sometimes do, so crowds learn.
  - TRUST-TALK. One sentence of honest talk raises reputation a
    little (0.012 if honesty > 0.5). From a liar it is cheap talk:
    +0.004, with a 15% chance of being read as flattery (-0.02).
  - REPUTATION (0.02..1.0, starts 0.5) is public and is the town's
    memory. It steers who gets heard (sampling weights), who gets
    followed (follow score), and rally power. A delivered honest
    pitch (q >= 0.5, no lie) adds 0.01; a successful coordination
    day adds up to 0.01. A caught lie costs 0.05 + 0.10*L.
  - WAGES. Solo work pays (12 + 30*skill) * (0.5 + 0.8*grit) *
    U(0.85, 1.15), minus a $15 living cost — the same base economy
    as EP01-EP03, so leadership income is visible on top of it.
"""
import json, random
from dataclasses import dataclass

SEED = 5            # featured seed, chosen by the disclosed seed scan (see REPRODUCE.md)
DAYS = 30
N = 100
START_MONEY = 1000.0
LIVING_COST = 15.0
SENTENCES_PER_DAY = 10

# ---- wages (same base economy as EP01-EP03) ----
WAGE_BASE, WAGE_SKILL = 12.0, 30.0     # wage = (12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)

# ---- speech ----
PITCH_COST, RALLY_COST, TRUST_COST = 2, 1, 1
PITCHES_HEARD = 6                      # pitches a listener samples per day (+ current leader's)
FOLLOW_THRESHOLD = 0.30                # min follow score, else work solo
LOYALTY_BONUS = 0.04                   # score bonus for staying with current leader
REP_HEAR_WEIGHT = 0.20                 # sampling weight = (0.20 + rep) x (4 / pitches made today)
LISTENER_PITCH_FLOOR = 0.55            # listeners pitch only if the idea clears this quality
FOLLOW_REP_WEIGHT = 0.35               # follow score = perceived q * (0.35 + 0.65*rep)

# ---- lies & detection ----
LIE_BASE, LIE_RISK = 0.15, 0.60        # L = (0.15 + 0.60*risk) * U(0.5, 1.2)
REP_LIE_CAUGHT = 0.05                  # rep hit: + 0.10 * L on top
DETECT_BASE, DETECT_SKILL = 0.08, 0.35 # p_detect = 0.08 + 0.35*skill + 0.02*unspent + 0.25*L
DETECT_ATTENTION, DETECT_LIE = 0.02, 0.25
EXPOSED_DISCOUNT = 0.80                # exposed pitch perceived at 80% of true quality

# ---- coordination ----
COORD_SKILL_BONUS = 0.30               # follower output x (1 + 0.30*leader skill), crowd-diluted
COORD_CROWD_DIVISOR = 30.0             # skill bonus divided by (1 + followers/30)
LEADER_SHARE = 0.10                    # leader takes 10% of each follower's output, crowd-thinned
LEADER_SHARE_DIVISOR = 20.0            # share rate divided by (1 + followers/20)
LEADER_CROWD_BONUS = 0.02              # leader's own output +2% per follower, cap 15
LEADER_CROWD_CAP = 15
RALLY_BOOST = 0.08                     # per rally sentence: +0.08*(0.5+rep) follower output
FLOP_NOISE = 0.12                      # realised quality = pitch q + U(-0.12, 0.12), once per leader/day
FLOP_THRESHOLD = 0.50                  # realised quality below this = flop
SCORE_CROWD_DIVISOR = 60.0             # follow score divided by (1 + followers/60)
FLOP_OUTPUT = 0.70                     # flop: followers' output x0.7
REP_FLOP = 0.02
REP_HONEST_PITCH = 0.01                # delivered honest pitch with q >= 0.5
REP_COORD_DAY = 0.01                   # successful coordination day (scaled by followers/10)

# ---- trust-talk ----
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

# pitches, rallies, trust-talks per day, by strategy
SPEECH_PLAN = {
    "loudmouth": (4, 1, 1),
    "orator":    (2, 2, 2),
    "schemer":   (2, 1, 1),
    "listener":  (1, 1, 0),
    "worker":    (1, 1, 1),
}

def pick_strategy(a):
    if a.risk > 0.60 and a.honesty < 0.45: return "loudmouth"
    if a.honesty > 0.60 and a.risk < 0.40: return "listener"
    if a.skill > 0.55 and a.honesty > 0.55: return "orator"
    if a.risk > 0.55 and a.skill > 0.50: return "schemer"
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
    leader_id: int = -1          # who this agent follows (-1 = solo)
    followers_yesterday: int = 0  # followers at end of yesterday (rally only if > 0)
    rallies_today: int = 0        # effective rallies spent today
    unspent: int = 0              # sentences saved today (= attention, for lie detection)
    sentences_spent: int = 0
    sentences_spent_days: int = 0  # days with any speech (for averages)
    pitches: int = 0
    rallies: int = 0
    trust_talks: int = 0
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
    vals = [("skill", a.skill), ("grit", a.work_ethic), ("risk", a.risk),
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

    events = []
    daily = []
    prev_leader = None
    total_sentences = total_lies = total_caught = 0
    total_pitches = total_flops = 0
    leader_history = []   # (day, leader name, followers)

    def rank_map():
        order = sorted(agents, key=lambda a: -a.money)
        return {a.id: k + 1 for k, a in enumerate(order)}

    for day in range(1, DAYS + 1):
        active = [a for a in agents if not a.bankrupt]
        # ---------------- speech phase: pitches ----------------
        # pitch: {speaker, q, claim, lying, L, exposed}
        pitches = []
        day_sentences = 0
        for a in active:
            npitch, nrally, ntrust = SPEECH_PLAN[a.strategy]
            # rallies only count if there is someone to rally: a leader
            # with no followers spends those sentences on nothing (they
            # stay unspent, i.e. attention) instead of shouting at nobody
            nrally_eff = nrally if a.followers_yesterday > 0 else 0
            # pitches: listeners speak only when the idea is worth saying
            made = 0
            for _ in range(npitch):
                q = 0.20 + 0.60 * a.skill + 0.20 * rng.random()
                if a.strategy == "listener" and q < LISTENER_PITCH_FLOOR:
                    continue   # saves the 2 sentences: they become attention
                lying = rng.random() < (1 - a.honesty) * (0.4 + 0.6 * a.risk)
                if lying:
                    L = (LIE_BASE + LIE_RISK * a.risk) * rng.uniform(0.5, 1.2)
                    claim = min(1.2, q * (1 + L))
                    a.lies_told += 1; total_lies += 1
                else:
                    L = 0.0; claim = q
                pitches.append({"speaker": a, "q": q, "claim": claim,
                                "lying": lying, "L": L, "exposed": False})
                made += 1
            spent = made * PITCH_COST + nrally_eff * RALLY_COST + ntrust * TRUST_COST
            spent = min(spent, SENTENCES_PER_DAY)
            a.sentences_spent += spent
            a.sentences_spent_days += 1
            day_sentences += spent
            a.pitches += made; a.rallies += nrally_eff; a.trust_talks += ntrust
            a.rallies_today = nrally_eff
            a.unspent = SENTENCES_PER_DAY - spent   # attention, for detection
            # trust-talk
            for _ in range(ntrust):
                if a.honesty > 0.5:
                    a.rep = min(1.0, a.rep + REP_TRUST_HONEST)
                else:
                    if rng.random() < FLATTERY_P:
                        a.rep = max(0.02, a.rep - REP_FLATTERY)
                    else:
                        a.rep = min(1.0, a.rep + REP_TRUST_CHEAP)
        total_sentences += day_sentences
        total_pitches += len(pitches)

        # ---------------- listening & following ----------------
        # sampling weights: the trusted get heard, and when the quiet
        # one speaks the room goes quiet — one pitch from a speaker who
        # made few pitches today gets proportionally more hearing, so
        # total airtime per speaker is roughly equal and quality decides
        made_count = {}
        for p in pitches:
            made_count[p["speaker"].id] = made_count.get(p["speaker"].id, 0) + 1
        weights = [(REP_HEAR_WEIGHT + p["speaker"].rep) * (4.0 / made_count[p["speaker"].id])
                   for p in pitches]
        wsum = sum(weights)
        followers = {a.id: [] for a in active}   # leader id -> follower agents
        for a in active:
            # sample pitches: 6 weighted + current leader's pitch if pitched
            heard = []
            if pitches and wsum > 0:
                idxs = set()
                tries = 0
                while len(idxs) < min(PITCHES_HEARD, len(pitches)) and tries < 40:
                    tries += 1
                    x = rng.random() * wsum
                    for j, w in enumerate(weights):
                        x -= w
                        if x <= 0:
                            idxs.add(j); break
                heard = [pitches[j] for j in idxs]
            if a.leader_id >= 0:
                for p in pitches:
                    if p["speaker"].id == a.leader_id and p not in heard:
                        heard.append(p)
            # evaluate: detect lies, score, pick best
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
        # honest delivered pitches nudge rep up (once per pitch, capped by count)
        for p in pitches:
            if not p["lying"] and p["q"] >= 0.5 and not p["exposed"]:
                p["speaker"].rep = min(1.0, p["speaker"].rep + REP_HONEST_PITCH)

        # ---------------- work phase ----------------
        # realised project quality, once per leader per day: the whole
        # crowd shares one outcome (drawn here, not per follower)
        realised_q = {}
        for a in active:
            fols = followers.get(a.id, [])
            if not fols:
                continue
            lpitch = None
            for p in pitches:
                if p["speaker"] is a:
                    lpitch = p; break
            realised_q[a.id] = (lpitch["q"] + rng.uniform(-FLOP_NOISE, FLOP_NOISE)) if lpitch else 0.5
        # rally multipliers per leader (effective rallies only)
        rally_mult = {}
        for a in active:
            fols = followers.get(a.id, [])
            if fols and a.rallies_today > 0:
                rally_mult[a.id] = 1.0 + RALLY_BOOST * a.rallies_today * (0.5 + a.rep)
                if len(fols) >= 15:
                    events.append({"day": day, "type": "rally", "who": a.name,
                                   "detail": f"{a.name} rallies {len(fols)} followers "
                                             f"({a.rallies_today} sentence{'s' if a.rallies_today > 1 else ''})"})
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
                # the followed project's realised quality (one draw per leader/day)
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
                    # log the flop once, on the first follower processed
                    leader.projects_flopped += 1
                    total_flops += 1
                    leader.rep = max(0.02, leader.rep - REP_FLOP)
                    if len(fols) >= 8:
                        events.append({"day": day, "type": "flop", "who": leader.name,
                                       "detail": f"{leader.name}'s project flopped with "
                                                 f"{len(fols)} followers on it"})
            else:
                a.money += wage - LIVING_COST
        # leaders' own crowd bonus + coordination rep
        for a in active:
            fols = followers.get(a.id, [])
            if fols:
                a.projects_led += 1
                a.followers_peak = max(a.followers_peak, len(fols))
                # own project grows with the crowd (applied on top of today's money)
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
        # leader of the day = most followers (ties: richer first)
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
            day_leader.days_as_leader += 1   # every day led counts, not just changes
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
            "sentences_spoken": day_sentences,
            "lies_told_day": sum(1 for p in pitches if p["lying"]),
            "lies_caught_day": sum(1 for p in pitches if p["exposed"]),
            "money": [round(a.money, 1) for a in agents],
            "rep": [round(a.rep, 3) for a in agents],
            "followers": [len(followers.get(a.id, [])) for a in agents],
            "bankrupt": [a.bankrupt for a in agents],
        })

    ranked = sorted(agents, key=lambda a: -a.money)
    winner = ranked[0]
    most_skilled = max(agents, key=lambda a: a.skill)
    hardest = max(agents, key=lambda a: a.work_ethic)
    biggest_liar = max(agents, key=lambda a: a.lies_told)
    most_followed = max(agents, key=lambda a: a.followers_peak)
    loudest = max(agents, key=lambda a: a.sentences_spent)
    strat_counts = {}
    for s in ("loudmouth", "orator", "schemer", "listener", "worker"):
        strat_counts[s] = sum(1 for a in agents if a.strategy == s)
    # lead changes: changes in the most-followed leader across days
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
                "final_followers": len([x for x in agents if x.leader_id == a.id and not x.bankrupt]),
                "followers_peak": a.followers_peak,
                "days_as_leader": a.days_as_leader,
                "sentences_spent": a.sentences_spent,
                "sentences_per_day": round(a.sentences_spent / DAYS, 2),
                "pitches": a.pitches, "rallies": a.rallies, "trust_talks": a.trust_talks,
                "lies_told": a.lies_told, "lies_caught": a.lies_caught,
                "leadership_income": round(a.leadership_income),
                "follower_bonus_earned": round(a.follower_bonus_earned),
                "projects_led": a.projects_led, "projects_flopped": a.projects_flopped}
    log = {
        "seed": seed, "days": DAYS,
        "premise": "10 sentences/day each; leadership emerges from followers' choice",
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
        "loudest_talker": fate(loudest),
        "total_sentences": total_sentences,
        "total_pitches": total_pitches,
        "total_lies": total_lies, "total_caught": total_caught,
        "total_flops": total_flops,
        "total_bankrupt": sum(1 for a in agents if a.bankrupt),
        "final_mean_rep": daily[-1]["mean_rep"] if daily else 0.0,
        "median_final_money": round(sorted(a.money for a in agents)[50]),
        "town_avg_sentences_per_day": round(total_sentences / (DAYS * N), 2),
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
    print("final leader (most followers):", log["final_leader"]["name"],
          log["final_leader"]["final_followers"], "followers")
    print("loudest talker:", log["loudest_talker"]["name"],
          log["loudest_talker"]["sentences_per_day"], "sent/day | rank",
          log["loudest_talker"]["final_rank"])
    print("most followed:", log["most_followed"]["name"], "peak",
          log["most_followed"]["followers_peak"], "| rank", log["most_followed"]["final_rank"])
    print("biggest liar:", log["biggest_liar"]["name"], "lies",
          log["biggest_liar"]["lies_told"], "caught", log["biggest_liar"]["lies_caught"],
          "| rank", log["biggest_liar"]["final_rank"])
    print("sentences:", log["total_sentences"], "pitches:", log["total_pitches"],
          "lies:", log["total_lies"], "caught:", log["total_caught"],
          "flops:", log["total_flops"], "bankrupt:", log["total_bankrupt"])
    print("lead changes:", log["lead_changes"], "distinct leaders:", log["distinct_leaders"])
    print("leader by day:", [(h["day"], h["leader"], h["followers"]) for h in log["leader_history"]])
    print("winner sentences/day:", w["sentences_per_day"],
          "| town avg:", log["town_avg_sentences_per_day"],
          "| winner rep:", w["final_rep"], "| winner followers peak:", w["followers_peak"])
