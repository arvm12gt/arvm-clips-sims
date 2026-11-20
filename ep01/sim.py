#!/usr/bin/env python3
"""
EP01 simulation: 100 people, $10,000 each, 30 days, no rules.
Agent-based model. Fixed seed. Story comes from the output, not a script.

Traits per agent (0..1): skill, work_ethic, risk_appetite, honesty, luck
Strategy is derived from traits each run (not assigned by hand):
  - gambler : risk > 0.78
  - thief   : honesty < 0.25 and risk > 0.55
  - builder : skill > 0.62 and risk between 0.35 and 0.78 (business bets)
  - lender  : honesty > 0.65 and skill > 0.45 (loans + steady work)
  - worker  : everyone else (steady work, small safe interest)
Daily living cost applies to everyone. Theft can be caught -> fine + jail days.
Loans: lenders lend to builders/gamblers; default probability depends on
borrower honesty and whether their bet failed.
"""
import json, random, math
from dataclasses import dataclass, field

SEED = 20261120
DAYS = 30
START = 10_000.0
LIVING_COST = 95.0  # per day

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

@dataclass
class Agent:
    id: int
    name: str
    skill: float
    work_ethic: float
    risk: float
    honesty: float
    luck: float
    money: float = START
    strategy: str = ""
    jailed_days: int = 0
    bankrupt_day: int = -1
    peak: float = START
    total_stolen: float = 0.0
    total_earned_work: float = 0.0

    def trait_label(self):
        t = []
        if self.work_ethic > 0.8: t.append("hardest worker")
        if self.skill > 0.8: t.append("highly skilled")
        if self.risk > 0.8: t.append("big risk-taker")
        if self.honesty > 0.85: t.append("very honest")
        if self.honesty < 0.2: t.append("dishonest")
        if self.luck > 0.85: t.append("very lucky")
        if self.luck < 0.15: t.append("unlucky")
        return ", ".join(t) if t else "average on every trait"

def pick_strategy(a: Agent) -> str:
    if a.honesty < 0.25 and a.risk > 0.55: return "thief"
    if a.risk > 0.78: return "gambler"
    if a.skill > 0.62 and a.risk > 0.35: return "builder"
    if a.honesty > 0.65 and a.skill > 0.45: return "lender"
    return "worker"

def run(seed=SEED):
    rng = random.Random(seed)
    agents = []
    for i in range(100):
        a = Agent(id=i, name=FIRST[i],
                  skill=rng.random(), work_ethic=rng.random(),
                  risk=rng.random(), honesty=rng.random(), luck=rng.random())
        a.strategy = pick_strategy(a)
        agents.append(a)

    events = []
    daily = []
    prev_leader = None

    for day in range(1, DAYS + 1):
        # --- theft phase (thieves pick a rich target) ---
        for a in agents:
            if a.strategy != "thief" or a.jailed_days > 0 or a.money <= 0:
                continue
            target = max((x for x in agents if x is not a and x.money > 500),
                         key=lambda x: x.money, default=None)
            if target is None: continue
            caught = rng.random() < 0.16 + 0.25 * (1 - a.skill)
            if caught:
                fine = min(a.money, 1200 + rng.random() * 800)
                a.money -= fine
                a.jailed_days = 3
                events.append({"day": day, "type": "caught",
                               "who": a.name, "detail": f"{a.name} caught stealing, fined ${fine:,.0f}, jailed 3 days"})
            else:
                amt = target.money * (0.04 + 0.08 * rng.random()) * (0.5 + a.luck)
                target.money -= amt
                a.money += amt
                a.total_stolen += amt
                if amt > 900:
                    events.append({"day": day, "type": "theft",
                                   "who": a.name, "detail": f"{a.name} stole ${amt:,.0f} from {target.name}"})
        # --- main daily actions ---
        loan_pool = []  # (lender, amount available)
        for a in agents:
            if a.jailed_days > 0:
                a.jailed_days -= 1
                a.money -= LIVING_COST
                continue
            if a.money <= 0:
                continue
            m = a.money
            if a.strategy == "worker":
                earn = (140 + 260 * a.skill) * (0.4 + a.work_ethic) * (0.85 + 0.3 * rng.random())
                a.money += earn; a.total_earned_work += earn
                a.money += a.money * 0.0015  # safe interest
            elif a.strategy == "lender":
                earn = (120 + 200 * a.skill) * (0.4 + a.work_ethic) * (0.85 + 0.3 * rng.random())
                a.money += earn; a.total_earned_work += earn
                loan_pool.append(a)
            elif a.strategy == "builder":
                earn = (80 + 140 * a.skill) * (0.4 + a.work_ethic)
                a.money += earn; a.total_earned_work += earn
                stake = m * (0.10 + 0.25 * a.risk)
                p_win = 0.30 + 0.38 * a.skill + 0.14 * a.luck
                if rng.random() < p_win:
                    a.money += stake * (0.25 + 0.75 * rng.random())
                else:
                    a.money -= stake * (0.35 + 0.55 * rng.random())
            elif a.strategy == "gambler":
                earn = 60 * a.work_ethic
                a.money += earn
                stake = m * (0.15 + 0.45 * a.risk)
                roll = rng.random()
                if roll < 0.06 + 0.10 * a.luck:
                    a.money += stake * 2.2  # jackpot
                    events.append({"day": day, "type": "jackpot", "who": a.name,
                                   "detail": f"{a.name} hit a jackpot, +${stake*2.2:,.0f}"})
                elif roll < 0.46:
                    a.money += stake * 0.4
                else:
                    a.money -= stake * (0.5 + 0.5 * rng.random())
            elif a.strategy == "thief":
                earn = 50 * a.work_ethic
                a.money += earn
            a.money -= LIVING_COST
        # --- lending phase: lenders fund builders/gamblers for 1 day at interest ---
        borrowers = [x for x in agents if x.strategy in ("builder", "gambler")
                     and x.jailed_days == 0 and x.money > 200]
        rng.shuffle(borrowers)
        for lender in loan_pool:
            if lender.money < 1500 or not borrowers: continue
            b = borrowers.pop()
            amt = min(lender.money * 0.18, 600 + 1400 * rng.random())
            interest = amt * 0.06
            lender.money -= amt
            # borrower invests it with same-day swing; default if swing is bad & dishonest
            swing = rng.uniform(-0.45, 0.55) + 0.18 * b.skill
            b.money += amt * swing
            default_p = 0.08 + (0.35 if swing < -0.15 else 0.0) + 0.30 * (1 - b.honesty)
            if rng.random() < default_p:
                events.append({"day": day, "type": "default", "who": b.name,
                               "detail": f"{b.name} defaulted on {lender.name}'s loan of ${amt:,.0f}"})
                # lender loses principal
            else:
                lender.money += amt + interest
        # --- bookkeeping ---
        for a in agents:
            a.peak = max(a.peak, a.money)
            if a.money <= 0 and a.bankrupt_day < 0:
                a.bankrupt_day = day
                events.append({"day": day, "type": "bankrupt", "who": a.name,
                               "detail": f"{a.name} ({a.strategy}) went bankrupt on day {day}"})
        ranked = sorted(agents, key=lambda x: -x.money)
        leader = ranked[0]
        if prev_leader is not None and leader.name != prev_leader:
            events.append({"day": day, "type": "lead_change", "who": leader.name,
                           "detail": f"{leader.name} ({leader.strategy}) takes the lead with ${leader.money:,.0f}"})
        prev_leader = leader.name
        daily.append({
            "day": day,
            "leader": leader.name, "leader_money": round(leader.money),
            "leader_strategy": leader.strategy,
            "top5": [{"name": x.name, "money": round(x.money), "strategy": x.strategy} for x in ranked[:5]],
            "bankrupt_count": sum(1 for x in agents if x.money <= 0),
            "total_wealth": round(sum(max(x.money, 0) for x in agents)),
            "balances": [round(x.money) for x in agents],
        })

    ranked = sorted(agents, key=lambda x: -x.money)
    winner = ranked[0]
    hardest = max(agents, key=lambda x: x.work_ethic)
    most_skilled = max(agents, key=lambda x: x.skill)
    log = {
        "seed": seed, "days": DAYS, "start_money": START,
        "strategy_counts": {s: sum(1 for a in agents if a.strategy == s)
                            for s in ("worker", "builder", "gambler", "lender", "thief")},
        "daily": daily,
        "events": events,
        "final_top10": [{"rank": i + 1, "name": a.name, "money": round(a.money),
                         "strategy": a.strategy,
                         "traits": {"skill": round(a.skill, 2), "work_ethic": round(a.work_ethic, 2),
                                    "risk": round(a.risk, 2), "honesty": round(a.honesty, 2),
                                    "luck": round(a.luck, 2)},
                         "peak": round(a.peak), "total_stolen": round(a.total_stolen)}
                        for i, a in enumerate(ranked[:10])],
        "final_bottom5": [{"name": a.name, "money": round(a.money), "strategy": a.strategy,
                           "bankrupt_day": a.bankrupt_day} for a in ranked[-5:]],
        "winner": {"name": winner.name, "money": round(winner.money), "strategy": winner.strategy,
                   "traits": {"skill": round(winner.skill, 2), "work_ethic": round(winner.work_ethic, 2),
                              "risk": round(winner.risk, 2), "honesty": round(winner.honesty, 2),
                              "luck": round(winner.luck, 2)},
                   "trait_label": winner.trait_label(), "peak": round(winner.peak)},
        "hardest_worker": {"name": hardest.name, "work_ethic": round(hardest.work_ethic, 2),
                           "final_money": round(hardest.money), "strategy": hardest.strategy,
                           "final_rank": ranked.index(hardest) + 1, "bankrupt_day": hardest.bankrupt_day},
        "most_skilled": {"name": most_skilled.name, "skill": round(most_skilled.skill, 2),
                         "final_money": round(most_skilled.money), "strategy": most_skilled.strategy,
                         "final_rank": ranked.index(most_skilled) + 1},
        "total_bankrupt": sum(1 for a in agents if a.money <= 0),
        "median_final": round(sorted(a.money for a in agents)[50]),
    }
    return log

if __name__ == "__main__":
    log = run()
    with open("sim_log.json", "w") as f:
        json.dump(log, f, indent=1)
    print("strategies:", log["strategy_counts"])
    print("winner:", log["winner"])
    print("hardest worker:", log["hardest_worker"])
    print("most skilled:", log["most_skilled"])
    print("bankrupt total:", log["total_bankrupt"], "median final:", log["median_final"])
    print("lead changes:", [e for e in log["events"] if e["type"] == "lead_change"])
    print("final top5:", [(x["name"], x["money"], x["strategy"]) for x in log["final_top10"][:5]])
