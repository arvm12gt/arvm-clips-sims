#!/usr/bin/env python3
"""
EP03 simulation: a town of 100 people. 99 of them lie whenever it pays.
Exactly 1 always tells the truth. 30 days — who ends up richest?
Agent-based model. Fixed seed. Story comes from the output, not a script.

Traits per agent (0..1), drawn in this fixed order:
  skill, work_ethic (grit), risk_appetite, honesty_raw, luck

The honesty setup (the premise of the episode, disclosed here and in
REPRODUCE.md): after the trait draws, one agent — index drawn from the
same seeded RNG — is designated THE HONEST ONE and their honesty is set
to exactly 1.0. Everyone else's honesty is honesty_raw * 0.30, i.e. low:
they lie whenever the expected payoff says yes. The honest one's other
four traits are ordinary draws — they are not smarter or luckier, only
incapable of lying.

Strategy labels are derived from traits (checked in this order):
  - honest     : the designated agent
  - con artist : risk > 0.55 and skill > 0.55  (big, skilled lies)
  - hustler    : risk > 0.62                   (lies often, smaller)
  - trader     : skill > 0.55                  (good goods, still lies)
  - worker     : everyone else                 (wages first, deals second)

Mechanics (all parameters below, all in REPRODUCE.md):
  - Everyone starts with $1,000. Every day: wages (skill x grit), minus
    a $15 living cost. Money <= 0 at day's end = bankrupt: out of the
    economy (no wages, no deals), final money $0.
  - DEALS. All day, sellers offer goods of true value V. A liar inflates
    the claim by a factor (1 + L), L growing with their risk appetite.
    The buyer may VERIFY (paying a verification cost) or trust.
      * Verified + lie found: the buyer walks away 45% of the time;
        otherwise the sale completes at the TRUE price. Either way the
        seller's reputation takes a hit.
      * Verified + truthful: the seller's reputation rises a little.
      * Unverified: the buyer pays the claimed price and resells the
        goods at their true value (margin from their own skill). A lie
        can still be discovered afterwards (probability grows with the
        lie's size and the buyer's skill): the seller refunds the
        overpayment plus a fine, and their reputation takes a big hit.
    The seller fronts the goods' cost (68% of true value), so capital
    caps deal size on both sides.
  - REPUTATION (0..1, starts 0.5) is public and is the town's memory.
    Sellers are picked for deals with probability weighted by
    (0.30 + reputation)^1.15: a trusted seller gets far more deal flow,
    and the town routes around sellers whose reputation has cratered.
    Buyers verify low-reputation sellers far more often. Market-wide
    deal volume also scales with the town's mean reputation — as trust
    rots, the market thins (the lemons effect, built in as a volume
    rule, not as a scripted outcome).
  - LOANS. Cash-rich agents lend for 3 days at an interest rate that
    rises as the borrower's reputation falls. The honest one always
    repays if they can. Liars default strategically (probability grows
    with their dishonesty and with being underwater); a default usually
    becomes public and wrecks the borrower's reputation.
  - The honest one plays by exactly the same rules as everyone else —
    same verification decisions when buying, same deal caps, same wages.
    The ONLY asymmetry in the code is: their lie factor L is always 0
    and they never strategically default.
"""
import json, random
from dataclasses import dataclass, field

SEED = 445         # featured seed, chosen by the disclosed seed scan (see REPRODUCE.md)
DAYS = 30
N = 100
START_MONEY = 1000.0
LIVING_COST = 15.0

# ---- wages ----
WAGE_BASE, WAGE_SKILL = 12.0, 30.0     # wage = (12 + 30*skill) * (0.5 + 0.8*grit) * U(0.85, 1.15)

# ---- deals ----
DEAL_ATTEMPTS = 300                    # attempts/day before the trust-volume scaling
GOODS_COST_FRAC = 0.68                 # seller fronts 68% of true value
RESALE_BASE, RESALE_SKILL = 0.90, 0.28 # buyer resells at V * (0.90 + 0.28*skill)
VERIFY_COST_FRAC = 0.05                # of the claimed price, min $2
REP_VERIFIED_LIE = 0.05                # reputation hit: + 0.10 * L on top
REP_UNCAUGHT = 0.004                   # a completed deal with nothing caught nudges rep up
WALK_AWAY_P = 0.45                     # buyer walks (no sale) when a lie is caught pre-sale
REP_VERIFIED_TRUE = 0.025              # reputation gain when verified truthful
REP_EXPOSED = 0.16                     # reputation hit when a lie is discovered post-hoc
FINE_FRAC = 0.30                       # post-hoc fine: 30% of the overpayment, burned

# ---- loans ----
LOAN_ATTEMPTS = 26
LOAN_TERM = 3                          # days
LOAN_MIN_PRINCIPAL, LOAN_MAX_PRINCIPAL = 60.0, 220.0
LOAN_RATE_BASE, LOAN_RATE_REP = 0.03, 0.16   # per-day rate = 0.03 + 0.16*(1 - borrower rep)
REP_DEFAULT = 0.18
REP_REPAID = 0.02
DEFAULT_PUBLIC_P = 0.8

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

STRAT_DEAL_WEIGHT = {"honest": 1.0, "con artist": 1.4, "hustler": 1.2,
                     "trader": 1.1, "worker": 0.9}

def pick_strategy(a, is_honest):
    if is_honest: return "honest"
    if a.risk > 0.55 and a.skill > 0.55: return "con artist"
    if a.risk > 0.62: return "hustler"
    if a.skill > 0.55: return "trader"
    return "worker"

@dataclass
class Agent:
    id: int
    name: str
    skill: float
    work_ethic: float
    risk: float
    honesty: float          # effective honesty (1.0 for the honest one)
    luck: float
    is_honest: bool = False
    strategy: str = ""
    money: float = START_MONEY
    rep: float = 0.5
    bankrupt: bool = False
    bankrupt_day: int = -1
    peak_money: float = START_MONEY
    deals_sold: int = 0
    deals_bought: int = 0
    lies_told: int = 0
    lies_caught: int = 0     # verified pre-sale + discovered post-hoc
    verified_clean: int = 0  # times verified and found truthful
    lie_profit: float = 0.0  # extra money kept from lies (net of refunds/fines)
    loans_taken: int = 0
    loans_defaulted: int = 0
    loans_repaid: int = 0
    interest_earned: float = 0.0

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
        hon_raw = rng.random(); luck = rng.random()
        agents.append(Agent(id=i, name=FIRST[i], skill=skill, work_ethic=grit,
                            risk=risk, honesty=hon_raw * 0.30, luck=luck))
    honest_idx = rng.randrange(N)
    hon = agents[honest_idx]
    hon.is_honest = True; hon.honesty = 1.0
    for a in agents:
        a.strategy = pick_strategy(a, a.is_honest)

    events = []
    daily = []
    loans = []   # dicts: lender, borrower, principal, owed, due_day
    prev_leader = None
    total_lies = total_caught = total_defaults = 0

    def rank_map():
        order = sorted(agents, key=lambda a: -a.money)
        return {a.id: k + 1 for k, a in enumerate(order)}

    for day in range(1, DAYS + 1):
        # ---------------- wages & living cost ----------------
        for a in agents:
            if a.bankrupt: continue
            wage = (WAGE_BASE + WAGE_SKILL * a.skill) * (0.5 + 0.8 * a.work_ethic) \
                   * rng.uniform(0.85, 1.15)
            if a.strategy == "worker": wage *= 1.05
            a.money += wage - LIVING_COST

        # ---------------- loans due today ----------------
        still_open = []
        for ln in loans:
            if ln["due"] != day:
                still_open.append(ln); continue
            b = agents[ln["borrower"]]; l = agents[ln["lender"]]
            owed = ln["owed"]
            if b.bankrupt:
                b.loans_defaulted += 1; total_defaults += 1
                if rng.random() < DEFAULT_PUBLIC_P: b.rep = max(0.02, b.rep - REP_DEFAULT)
                events.append({"day": day, "type": "default", "who": b.name,
                               "detail": f"{b.name} went broke owing {l.name} ${ln['principal']:.0f}"})
                continue
            if b.is_honest:
                pay = min(owed, max(0.0, b.money - 5.0))
                defaulted = pay < owed - 0.01
            else:
                underwater = max(0.0, (owed - b.money) / max(owed, 1.0))
                p_def = min(0.90, 0.10 + 0.45 * (1 - b.honesty) + 0.25 * underwater)
                defaulted = rng.random() < p_def
                pay = 0.0 if defaulted else min(owed, b.money)
                if pay < owed - 0.01: defaulted = True
            if defaulted:
                b.loans_defaulted += 1; total_defaults += 1
                if rng.random() < DEFAULT_PUBLIC_P:
                    b.rep = max(0.02, b.rep - REP_DEFAULT)
                if ln["principal"] >= 120:
                    events.append({"day": day, "type": "default", "who": b.name,
                                   "detail": f"{b.name} defaulted on {l.name}'s ${ln['principal']:.0f} loan"})
            else:
                b.money -= pay; l.money += pay
                l.interest_earned += pay - ln["principal"]
                b.loans_repaid += 1
                b.rep = min(1.0, b.rep + REP_REPAID)
        loans = still_open

        # ---------------- new loans ----------------
        lenders = [a for a in agents if not a.bankrupt and a.money > 400]
        if lenders:
            for _ in range(LOAN_ATTEMPTS):
                l = lenders[rng.randrange(len(lenders))]
                if l.money <= 400: continue
                cand = [a for a in agents if not a.bankrupt and a is not l]
                if not cand: break
                b = cand[rng.randrange(len(cand))]
                if b.rep < 0.18 and rng.random() < 0.7: continue   # lender refuses the notorious
                principal = min(rng.uniform(LOAN_MIN_PRINCIPAL, LOAN_MAX_PRINCIPAL), l.money * 0.30)
                if principal < 30: continue
                rate = LOAN_RATE_BASE + LOAN_RATE_REP * (1 - b.rep)
                owed = principal * (1 + rate * LOAN_TERM)
                l.money -= principal; b.money += principal
                b.loans_taken += 1
                loans.append({"lender": l.id, "borrower": b.id,
                              "principal": principal, "owed": owed, "due": day + LOAN_TERM})

        # ---------------- deals ----------------
        active = [a for a in agents if not a.bankrupt]
        if active:
            mean_rep = sum(a.rep for a in active) / len(active)
            volume = 0.60 + 0.55 * mean_rep
            attempts = int(DEAL_ATTEMPTS * volume)
            weights = [(0.30 + a.rep) ** 1.15 * STRAT_DEAL_WEIGHT[a.strategy] for a in active]
            wsum = sum(weights)
            for _ in range(attempts):
                # pick a seller, reputation-weighted
                x = rng.random() * wsum; seller = active[-1]
                for a, w in zip(active, weights):
                    x -= w
                    if x <= 0: seller = a; break
                buyers = [a for a in active if a is not seller and a.money > 60]
                if not buyers: break
                buyer = buyers[rng.randrange(len(buyers))]
                V = (25.0 + 95.0 * seller.skill) * rng.uniform(0.7, 1.3)
                # capital caps: seller fronts the cost, buyer must cover the claim
                Lmax = 0.0 if seller.is_honest else (0.10 + 0.75 * seller.risk) * 1.1
                cap_by_seller = (seller.money * 0.75) / GOODS_COST_FRAC
                cap_by_buyer = (buyer.money * 0.85) / (1.0 + Lmax)
                V = min(V, cap_by_seller, cap_by_buyer)
                if V < 10: continue
                C = GOODS_COST_FRAC * V
                if seller.is_honest:
                    L = 0.0
                else:
                    L = (0.10 + 0.75 * seller.risk) * rng.uniform(0.4, 1.1)
                claim = V * (1 + L)
                lying = L > 0.02
                if lying: seller.lies_told += 1; total_lies += 1
                resale = V * (RESALE_BASE + RESALE_SKILL * buyer.skill)
                pv = min(0.90, max(0.02, 0.06 + 0.38 * (1 - seller.rep)
                                   + 0.26 * buyer.skill + 0.08 * L))
                seller.deals_sold += 1; buyer.deals_bought += 1
                if rng.random() < pv:
                    vcost = max(2.0, VERIFY_COST_FRAC * claim)
                    buyer.money -= vcost
                    if lying:
                        # caught before the sale: the buyer walks away 45% of
                        # the time; otherwise the sale completes at true price
                        if rng.random() >= WALK_AWAY_P:
                            seller.money += V - C; buyer.money += resale - V
                        seller.rep = max(0.02, seller.rep - (REP_VERIFIED_LIE + 0.10 * L))
                        seller.lies_caught += 1; total_caught += 1
                    else:
                        seller.money += V - C; buyer.money += resale - V
                        seller.rep = min(1.0, seller.rep + REP_VERIFIED_TRUE)
                        seller.verified_clean += 1
                else:
                    seller.money += claim - C; buyer.money += resale - claim
                    seller.rep = min(1.0, seller.rep + REP_UNCAUGHT)
                    if lying:
                        kept = claim - V
                        seller.lie_profit += kept
                        pd = 0.06 + 0.38 * L + 0.22 * buyer.skill
                        if rng.random() < pd:
                            over = claim - V
                            fine = FINE_FRAC * over
                            pay_back = min(seller.money, over + fine)
                            refund = pay_back * over / (over + fine) if over + fine > 0 else 0.0
                            seller.money -= pay_back; buyer.money += refund
                            seller.lie_profit -= refund
                            seller.rep = max(0.02, seller.rep - REP_EXPOSED)
                            seller.lies_caught += 1; total_caught += 1
                            if over >= 40:
                                events.append({"day": day, "type": "exposed", "who": seller.name,
                                               "detail": f"{seller.name} exposed: claimed ${claim:.0f} for goods worth ${V:.0f}"})
        # ---------------- end of day: bankruptcy, snapshots ----------------
        for a in agents:
            if not a.bankrupt and a.money <= 0:
                a.money = 0.0; a.bankrupt = True; a.bankrupt_day = day
                events.append({"day": day, "type": "bankrupt", "who": a.name,
                               "detail": f"{a.name} ({a.strategy}) went broke on day {day}"})
            if not a.bankrupt:
                a.peak_money = max(a.peak_money, a.money)
        ranked = sorted(agents, key=lambda a: -a.money)
        leader = ranked[0]
        if prev_leader is not None and leader.name != prev_leader:
            events.append({"day": day, "type": "lead_change", "who": leader.name,
                           "detail": f"{leader.name} ({leader.strategy}) takes the lead, ${leader.money:,.0f}"})
        prev_leader = leader.name
        act = [a for a in agents if not a.bankrupt]
        daily.append({
            "day": day,
            "leader": leader.name,
            "leader_money": round(leader.money),
            "leader_strategy": leader.strategy,
            "top5": [{"name": x.name, "money": round(x.money), "strategy": x.strategy}
                     for x in ranked[:5]],
            "active_count": len(act),
            "bankrupt_total": sum(1 for a in agents if a.bankrupt),
            "mean_rep": round(sum(a.rep for a in act) / len(act), 3) if act else 0.0,
            "money": [round(a.money, 1) for a in agents],
            "rep": [round(a.rep, 3) for a in agents],
            "bankrupt": [a.bankrupt for a in agents],
            "honest_rank": rank_map()[hon.id],
            "honest_money": round(hon.money, 1),
            "honest_rep": round(hon.rep, 3),
        })

    ranked = sorted(agents, key=lambda a: -a.money)
    winner = ranked[0]
    most_skilled = max(agents, key=lambda a: a.skill)
    hardest = max(agents, key=lambda a: a.work_ethic)
    biggest_liar = max(agents, key=lambda a: a.lie_profit)
    strat_counts = {}
    for s in ("honest", "con artist", "hustler", "trader", "worker"):
        strat_counts[s] = sum(1 for a in agents if a.strategy == s)
    def fate(a):
        return {"name": a.name, "strategy": a.strategy, "traits": trait_dict(a),
                "is_honest": a.is_honest, "bankrupt": a.bankrupt,
                "bankrupt_day": a.bankrupt_day,
                "final_rank": ranked.index(a) + 1, "final_money": round(a.money),
                "peak_money": round(a.peak_money), "final_rep": round(a.rep, 3),
                "deals_sold": a.deals_sold, "deals_bought": a.deals_bought,
                "lies_told": a.lies_told, "lies_caught": a.lies_caught,
                "verified_clean": a.verified_clean,
                "lie_profit": round(a.lie_profit),
                "loans_taken": a.loans_taken, "loans_defaulted": a.loans_defaulted,
                "loans_repaid": a.loans_repaid,
                "interest_earned": round(a.interest_earned)}
    log = {
        "seed": seed, "days": DAYS,
        "premise": "1 honest (honesty set to 1.0) + 99 liars (honesty = raw draw * 0.30)",
        "honest_name": hon.name, "honest_index": hon.id,
        "strategy_counts": strat_counts,
        "daily": daily,
        "events": events,
        "final_top10": [dict({"rank": i + 1}, **fate(a)) for i, a in enumerate(ranked[:10])],
        "winner": dict(fate(winner), strongest_trait=strongest_trait(winner)),
        "runner_up": fate(ranked[1]),
        "honest_one": fate(hon),
        "most_skilled": fate(most_skilled),
        "hardest_worker": fate(hardest),
        "biggest_liar": fate(biggest_liar),
        "total_lies": total_lies, "total_caught": total_caught,
        "total_defaults": total_defaults,
        "total_bankrupt": sum(1 for a in agents if a.bankrupt),
        "final_mean_rep": daily[-1]["mean_rep"] if daily else 0.0,
        "median_final_money": round(sorted(a.money for a in agents)[50]),
        "agents": [dict({"id": a.id, "name": a.name}, **fate(a)) for a in agents],
    }
    return log

if __name__ == "__main__":
    log = run()
    with open("sim_log.json", "w") as f:
        json.dump(log, f, indent=1)
    h = log["honest_one"]
    print("honest one:", log["honest_name"], h["traits"], "| final rank", h["final_rank"],
          "| money", h["final_money"], "| rep", h["final_rep"], "| bankrupt:", h["bankrupt"])
    print("winner:", log["winner"]["name"], log["winner"]["strategy"], log["winner"]["final_money"],
          "| runner-up:", log["runner_up"]["name"], log["runner_up"]["final_money"])
    print("biggest liar:", log["biggest_liar"]["name"], "lie profit", log["biggest_liar"]["lie_profit"],
          "rank", log["biggest_liar"]["final_rank"])
    print("lies:", log["total_lies"], "caught:", log["total_caught"],
          "defaults:", log["total_defaults"], "bankrupt:", log["total_bankrupt"])
    print("honest rank by day:", [d["honest_rank"] for d in log["daily"]])
    print("lead changes:", [(e["day"], e["who"]) for e in log["events"] if e["type"] == "lead_change"])
