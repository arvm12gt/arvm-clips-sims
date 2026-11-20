#!/usr/bin/env python3
"""
EP02 simulation: 100 people wash up on a desert island. Only 10 tools.
30 days — who thrives?
Agent-based model. Fixed seed. Story comes from the output, not a script.

Traits per agent (0..1), drawn in this fixed order:
  skill, work_ethic (grit), risk_appetite, honesty, luck

Strategy is derived from traits each run (not assigned by hand), in this order:
  - thief      : honesty < 0.25 and risk > 0.55
  - leader     : skill >= 0.72 and honesty >= 0.60  (founds a group)
  - hoarder    : honesty < 0.40 and work_ethic >= 0.55
  - loner      : risk >= 0.72
  - cooperator : honesty >= 0.52  (joins a group, shares fully)
  - survivor   : everyone else    (joins a group if there is room)

Island mechanics (all parameters below, all in REPRODUCE.md):
  - Every agent starts with health 85-100, no food, no shelter.
  - 10 tools exist, one each, dealt to 10 distinct random agents:
    axe, saw, fishing net, hook set, knife, rope, cooking pot,
    firestarter, tarp, medicine kit. Tool effects are in TOOL_FX.
  - Each day an agent has an effort budget E = (8 + 6*grit) scaled by
    health. Water costs effort (2.0 solo, 0.8 per member in a group —
    shared carrying). One main action per day (forage / fish / hunt /
    build / rest / tend), leftover effort goes to building or extra forage.
  - Forage, fish and game stocks are finite island commons: they deplete
    with use and regenerate daily. Storm days (p=0.13) block fishing,
    halve foraging and double night exposure.
  - Groups (leader + up to 8) pool food, share tools and shelter, split
    water duty and get a coordination bonus while their leader lives.
    Solo agents keep their own stores — higher ceiling, lower floor.
    Trade exists in one simple form: a solo agent with food to spare can
    rent a solo tool-holder's fishing gear for 0.5 food a day.
  - Night: everyone eats (1.0 food, less with fire/pot), stored food
    spoils (14%/night, 8% with a fire — no refrigeration on an island),
    the unsheltered lose health to exposure, thieves steal (caught =
    beaten and 60% of their stash confiscated back to the victim),
    the fed recover a little.
    Health <= 0 is death. A dead group member's tools stay with the
    group; a dead solo agent's tool washes up and may be found.
  - Group gatherers keep a 15% personal stash and pool the rest; at the
    meal a member whose pool share falls short dips into their stash
    before going hungry. Robbing a camp is riskier than robbing a loner
    (+0.15 catch probability — more eyes on the stores).
  - Thriving score (day 30, living agents): health + 5 * stored food
    (group members count their personal stash + per-capita pool share)
    + 10 * shelter level. Dead agents score 0.
"""
import json, random
from dataclasses import dataclass, field

SEED = 42
DAYS = 30
N = 100

# ---- needs & effort ----
EFFORT_BASE, EFFORT_GRIT = 8.0, 6.0
WATER_SOLO, WATER_GROUP = 2.0, 0.8
COST = {"forage": 4.0, "fish": 5.0, "hunt": 6.0, "build": 5.0, "rest": 0.0, "tend": 4.0}
FOOD_NEED = 1.0            # per person per day
NEED_FIRE = 0.90           # with a firestarter (cooked food goes further)
NEED_FIRE_POT = 0.80       # firestarter + cooking pot
NO_FOOD_HEALTH = 9.0       # health lost per full day unfed (scaled by shortfall)
NO_WATER_HEALTH = 6.0
FED_REGEN = 2.5            # nightly recovery when fed and watered
REST_HEAL = 6.0
EXPOSURE_BASE = 5.5        # nightly health drain at shelter level 0
EXPOSURE_PER_SHELTER = 1.3
SPOILAGE = 0.14            # stored food lost nightly (no refrigeration)
SPOILAGE_FIRE = 0.08       # ... less with a fire (smoking / preserving)
STASH_SHARE = 0.15         # group gatherers keep 15% of their catch as a
                           # personal stash; the rest goes to the pool
GROUP_THEFT_CAUGHT = 0.15  # extra catch probability when robbing a camp
                           # (more eyes watching the stores)
FIRE_EXPOSURE_MULT = 0.7
STORM_P = 0.13

# ---- island commons ----
FORAGE_START, FORAGE_CAP, FORAGE_REGEN = 700.0, 800.0, 30.0
FISH_START, FISH_CAP, FISH_REGEN = 450.0, 550.0, 22.0
GAME_START, GAME_CAP, GAME_REGEN = 300.0, 380.0, 12.0

# ---- tools ----
TOOLS = ["axe", "saw", "net", "hook set", "knife", "rope",
         "cooking pot", "firestarter", "tarp", "medicine kit"]
# effects are applied where the action happens; see action code + REPRODUCE.md

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

def pick_strategy(a):
    if a.honesty < 0.25 and a.risk > 0.55: return "thief"
    if a.skill >= 0.72 and a.honesty >= 0.60: return "leader"
    if a.honesty < 0.40 and a.work_ethic >= 0.55: return "hoarder"
    if a.risk >= 0.72: return "loner"
    if a.honesty >= 0.52: return "cooperator"
    return "survivor"

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
    health: float = 100.0
    food: float = 0.0            # personal stores (solo agents)
    shelter_prog: float = 0.0    # personal shelter progress (solo)
    tools: list = field(default_factory=list)
    group: int = -1              # group index or -1 (solo)
    alive: bool = True
    death_day: int = -1
    peak_score: float = 0.0
    days_hungry: int = 0
    total_gathered: float = 0.0
    total_stolen: float = 0.0

    @property
    def shelter_level(self):
        return min(5, int(self.shelter_prog))

@dataclass
class Group:
    id: int
    leader_id: int
    members: list = field(default_factory=list)   # agent ids, alive or not
    food: float = 0.0                              # shared pool
    shelter_prog: float = 0.0                      # shared shelter

    def alive_members(self, agents):
        return [agents[i] for i in self.members if agents[i].alive]

    def tools(self, agents):
        t = set()
        for i in self.members:
            if agents[i].alive: t.update(agents[i].tools)
        return t

    @property
    def shelter_level(self):
        return min(5, int(self.shelter_prog))

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
    # --- setup: traits first (5 draws per agent, fixed order) ---
    agents = []
    for i in range(N):
        a = Agent(id=i, name=FIRST[i],
                  skill=rng.random(), work_ethic=rng.random(),
                  risk=rng.random(), honesty=rng.random(), luck=rng.random())
        a.strategy = pick_strategy(a)
        agents.append(a)
    for a in agents:
        a.health = 85.0 + 15.0 * rng.random()
    # --- the 10 tools, one per distinct random agent ---
    holders = rng.sample(range(N), len(TOOLS))
    for tool, hi in zip(TOOLS, holders):
        agents[hi].tools.append(tool)
        if tool == "tarp":
            agents[hi].shelter_prog = 2.0   # a tarp is instant shelter
    # --- groups: leaders found, cooperators/survivors join ---
    groups = []
    leaders = sorted((a for a in agents if a.strategy == "leader"),
                     key=lambda a: -a.skill)
    for ld in leaders:
        g = Group(id=len(groups), leader_id=ld.id, members=[ld.id])
        ld.group = g.id
        groups.append(g)
    joiners = [a for a in agents if a.strategy in ("cooperator", "survivor")]
    rng.shuffle(joiners)
    for a in joiners:
        open_groups = [g for g in groups if len(g.members) < 9]
        if not open_groups: break
        g = open_groups[rng.randrange(len(open_groups))]  # join a random camp with room
        g.members.append(a.id); a.group = g.id
    for g in groups:  # tarp benefit is shared once grouped
        if any("tarp" in agents[i].tools for i in g.members):
            g.shelter_prog = max(g.shelter_prog, 2.0)

    stocks = {"forage": FORAGE_START, "fish": FISH_START, "game": GAME_START}
    events = []
    daily = []
    lost_tools = []
    prev_leader = None

    def eff_food(a):
        if a.group >= 0:
            g = groups[a.group]
            n = max(1, len(g.alive_members(agents)))
            return a.food + g.food / n   # personal stash + per-capita pool share
        return a.food

    def shelter_of(a):
        if a.group >= 0: return groups[a.group].shelter_level
        return a.shelter_level

    def score_of(a):
        if not a.alive: return 0.0
        return a.health + 5.0 * eff_food(a) + 10.0 * shelter_of(a)

    def has_tool(a, tool):
        if tool in a.tools: return True
        if a.group >= 0: return tool in groups[a.group].tools(agents)
        return False

    def toolset(a):
        if a.group >= 0: return groups[a.group].tools(agents)
        return set(a.tools)

    for day in range(1, DAYS + 1):
        storm = rng.random() < STORM_P
        # washed-up tools get found (50%) by a random living agent
        still_lost = []
        for tool in lost_tools:
            if rng.random() < 0.5:
                cand = [a for a in agents if a.alive]
                if cand:
                    w = cand[rng.randrange(len(cand))]
                    w.tools.append(tool)
                    events.append({"day": day, "type": "tool_found", "who": w.name,
                                   "detail": f"{w.name} found the washed-up {tool}"})
                    continue
            still_lost.append(tool)
        lost_tools = still_lost

        # ---------------- tool rental (before actions) ----------------
        # A solo agent with food to spare and no fishing gear can rent a solo
        # holder's net/hook set for the day: 0.5 food changes hands, the
        # renter fishes with the hook-set bonus today. One renter per holder.
        rented_gear = set()
        solo_holders = [a for a in agents if a.alive and a.group < 0
                        and ("net" in a.tools or "hook set" in a.tools)]
        holder_busy = set()
        for a in agents:
            if not a.alive or a.group >= 0: continue
            if "net" in a.tools or "hook set" in a.tools: continue
            if a.food < 2.5 or a.skill < 0.5 or a.health < 35: continue
            for h in solo_holders:
                if h.id in holder_busy or h is a: continue
                a.food -= 0.5; h.food += 0.5
                rented_gear.add(a.id); holder_busy.add(h.id)
                break

        # ---------------- daytime actions ----------------
        gathered = {}   # agent id -> food gathered today
        # group role assignment first (needs group context)
        def group_action(a, g):
            ts = g.tools(agents)
            alive = g.alive_members(agents)
            if a.health < 35: return "rest"
            if "medicine kit" in a.tools and any(m.health < 72 for m in alive): return "tend"
            if "net" in a.tools or "hook set" in a.tools: return "fish"
            if ("axe" in a.tools or "saw" in a.tools) and g.shelter_level < 4: return "build"
            if day <= 6 and g.shelter_level < 4 and rng.random() < 0.5: return "build"
            if a.skill >= 0.55: return "fish" if rng.random() < 0.6 else "hunt"
            return "forage"

        def solo_action(a):
            if a.health < 35: return "rest"
            if "medicine kit" in a.tools and a.health < 72: return "rest"  # self-tend = rest+
            if day <= 4 and shelter_of(a) < 2 and rng.random() < 0.55: return "build"
            if a.strategy == "loner":
                return "hunt" if a.health > 55 else "forage"
            if a.strategy == "thief":
                return "forage" if rng.random() < 0.7 else "hunt"
            if a.skill >= 0.55 and rng.random() < 0.55: return "fish"
            return "forage"

        for a in agents:
            if not a.alive: continue
            E = (EFFORT_BASE + EFFORT_GRIT * a.work_ethic) * (0.35 + 0.65 * a.health / 100.0)
            water_cost = WATER_GROUP if a.group >= 0 else WATER_SOLO
            if E < water_cost:
                a.health -= NO_WATER_HEALTH   # too weak to fetch water
                water_paid = False
            else:
                E -= water_cost; water_paid = True
            act = group_action(a, groups[a.group]) if a.group >= 0 else solo_action(a)
            if COST[act] > E: act = "forage" if E >= COST["forage"] else "rest"
            E -= COST[act]
            ts = toolset(a)
            coord = 1.08 if (a.group >= 0 and agents[groups[a.group].leader_id].alive) else 1.0
            gain = 0.0
            if act == "forage":
                if stocks["forage"] > 0:
                    y = (1.3 + 2.2 * a.skill) * rng.uniform(0.6, 1.35)
                    y *= stocks["forage"] / (stocks["forage"] + 150.0)
                    if storm: y *= 0.5
                    y = min(y, stocks["forage"]) * coord
                    stocks["forage"] -= y; gain = y
            elif act == "fish":
                if not storm and stocks["fish"] > 0:
                    y = (1.0 + 2.4 * a.skill) * rng.uniform(0.6, 1.3)
                    y *= stocks["fish"] / (stocks["fish"] + 120.0)
                    if "net" in ts: y *= 1.9
                    elif "hook set" in ts or a.id in rented_gear: y *= 1.45
                    y = min(y, stocks["fish"]) * coord
                    stocks["fish"] -= y; gain = y
            elif act == "hunt":
                if stocks["game"] > 0:
                    p = 0.22 + 0.33 * a.skill + 0.18 * a.luck
                    if "knife" in ts: p += 0.12
                    if "axe" in ts: p += 0.08
                    if rng.random() < p:
                        y = rng.uniform(3.5, 6.5) * coord
                        y = min(y, stocks["game"]); stocks["game"] -= y; gain = y
                    if rng.random() < 0.07 + 0.10 * a.risk:
                        inj = rng.uniform(6, 14); a.health -= inj
                        events.append({"day": day, "type": "injury", "who": a.name,
                                       "detail": f"{a.name} was hurt hunting (-{inj:.0f} health)"})
            elif act == "build":
                prog = (0.5 + a.skill)
                if "axe" in ts: prog *= 1.5
                if "saw" in ts: prog *= 1.6
                if "rope" in ts: prog *= 1.25
                if a.group >= 0: groups[a.group].shelter_prog = min(5.0, groups[a.group].shelter_prog + prog * 0.34)
                else: a.shelter_prog = min(5.0, a.shelter_prog + prog * 0.34)
            elif act == "tend":
                g = groups[a.group]
                patient = min(g.alive_members(agents), key=lambda m: m.health)
                patient.health = min(100.0, patient.health + 9.0)
                if patient.health < 30:
                    events.append({"day": day, "type": "rescue", "who": patient.name,
                                   "detail": f"{a.name}'s medicine kit pulled {patient.name} back from the edge"})
            elif act == "rest":
                heal = REST_HEAL + (4.0 if "medicine kit" in a.tools else 0.0)
                a.health = min(100.0, a.health + heal)
            # leftover effort: build if unsheltered, else extra forage
            if E >= 3.0 and act not in ("build", "rest"):
                if shelter_of(a) < 4:
                    prog = (0.5 + a.skill) * (1.5 if "axe" in ts else 1.0) * (1.6 if "saw" in ts else 1.0)
                    if a.group >= 0: groups[a.group].shelter_prog = min(5.0, groups[a.group].shelter_prog + prog * 0.2)
                    else: a.shelter_prog = min(5.0, a.shelter_prog + prog * 0.2)
                elif stocks["forage"] > 0:
                    y = (1.3 + 2.2 * a.skill) * rng.uniform(0.3, 0.6)
                    y *= stocks["forage"] / (stocks["forage"] + 150.0)
                    y = min(y, stocks["forage"]); stocks["forage"] -= y; gain += y
            gathered[a.id] = gain
            a.total_gathered += gain

        # gathered food lands: group members stash 15% and pool the rest;
        # solo agents keep everything
        for a in agents:
            if not a.alive: continue
            gfood = gathered.get(a.id, 0.0)
            if a.group >= 0:
                a.food += gfood * STASH_SHARE
                groups[a.group].food += gfood * (1 - STASH_SHARE)
            else: a.food += gfood

        # ---------------- evening meal ----------------
        for g in groups:
            alive = g.alive_members(agents)
            if not alive: continue
            ts = g.tools(agents)
            need = FOOD_NEED
            if "firestarter" in ts: need = NEED_FIRE
            if "firestarter" in ts and "cooking pot" in ts: need = NEED_FIRE_POT
            total_need = need * len(alive)
            if g.food >= total_need:
                g.food -= total_need
                for m in alive: m._fed = True
            else:
                share = g.food / len(alive) if alive else 0.0
                g.food = 0.0
                for m in alive:
                    short = need - share
                    cover = min(m.food, short)   # dip into the personal stash
                    m.food -= cover; short -= cover
                    if short <= 0.01:
                        m._fed = True
                    else:
                        m._fed = False
                        m.health -= NO_FOOD_HEALTH * (short / need)
                        m.days_hungry += 1
        for a in agents:
            if not a.alive or a.group >= 0: continue
            need = FOOD_NEED
            if "firestarter" in a.tools: need = NEED_FIRE
            if "firestarter" in a.tools and "cooking pot" in a.tools: need = NEED_FIRE_POT
            if a.food >= need:
                a.food -= need; a._fed = True
            else:
                frac = a.food / need if need else 0.0
                a.food = 0.0; a._fed = False
                a.health -= NO_FOOD_HEALTH * (1 - frac)
                a.days_hungry += 1

        # ---------------- spoilage (after the meal, before the night) ----------------
        for g in groups:
            rate = SPOILAGE_FIRE if "firestarter" in g.tools(agents) else SPOILAGE
            g.food *= (1 - rate)
        for a in agents:
            if a.alive and a.food > 0:
                rate = SPOILAGE_FIRE if has_tool(a, "firestarter") else SPOILAGE
                a.food *= (1 - rate)

        # ---------------- night: theft ----------------
        for a in agents:
            if not a.alive or a.strategy != "thief": continue
            # richest target: a group pool or a solo store
            best, best_food, best_group = None, 0.0, None
            for g in groups:
                if g.food > best_food and g.alive_members(agents):
                    best_food, best_group, best = g.food, g, None
            for x in agents:
                if x.alive and x.group < 0 and x is not a and x.food > best_food:
                    best_food, best, best_group = x.food, x, None
            if best_food < 1.0: continue
            amt = min(best_food, rng.uniform(1.0, 3.5) * (0.6 + 0.6 * a.luck))
            if "knife" in a.tools: amt *= 1.3
            if best_group is not None: best_group.food -= amt
            else: best.food -= amt
            a.food += amt; a.total_stolen += amt
            caught_p = 0.16 + 0.22 * (1 - a.skill)
            if best_group is not None: caught_p += GROUP_THEFT_CAUGHT
            if rng.random() < caught_p:
                dmg = rng.uniform(8, 15); a.health -= dmg
                # the stash is found and confiscated: 60% goes back to the victim
                conf = a.food * 0.6; a.food -= conf
                if best_group is not None: best_group.food += conf
                elif best is not None: best.food += conf
                events.append({"day": day, "type": "caught", "who": a.name,
                               "detail": f"{a.name} was caught stealing, beaten (-{dmg:.0f} health), stash confiscated"})
            elif amt >= 2.5:
                events.append({"day": day, "type": "theft", "who": a.name,
                               "detail": f"{a.name} stole {amt:.1f} food in the night"})

        # ---------------- night: exposure, recovery, death ----------------
        for a in agents:
            if not a.alive: continue
            drain = max(0.0, EXPOSURE_BASE - EXPOSURE_PER_SHELTER * shelter_of(a))
            if has_tool(a, "firestarter"): drain *= FIRE_EXPOSURE_MULT
            if storm: drain *= 2.0
            a.health -= drain
            if getattr(a, "_fed", False):
                a.health = min(100.0, a.health + FED_REGEN)
            if a.health <= 0:
                a.health = 0.0; a.alive = False; a.death_day = day
                events.append({"day": day, "type": "death", "who": a.name,
                               "detail": f"{a.name} ({a.strategy}) died on day {day}"})
                if a.group < 0:
                    for tool in a.tools: lost_tools.append(tool)
                    a.tools = []
                # group members' tools stay available to their group
            if a.alive:
                a.peak_score = max(a.peak_score, score_of(a))

        # stocks regenerate
        stocks["forage"] = min(FORAGE_CAP, stocks["forage"] + FORAGE_REGEN)
        stocks["fish"] = min(FISH_CAP, stocks["fish"] + FISH_REGEN)
        stocks["game"] = min(GAME_CAP, stocks["game"] + GAME_REGEN)

        # ---------------- bookkeeping ----------------
        ranked = sorted((a for a in agents if a.alive), key=lambda a: -score_of(a))
        leader = ranked[0] if ranked else None
        if leader and prev_leader is not None and leader.name != prev_leader:
            events.append({"day": day, "type": "lead_change", "who": leader.name,
                           "detail": f"{leader.name} ({leader.strategy}) takes the lead, score {score_of(leader):.0f}"})
        if leader: prev_leader = leader.name
        daily.append({
            "day": day,
            "storm": storm,
            "leader": leader.name if leader else None,
            "leader_score": round(score_of(leader)) if leader else 0,
            "leader_strategy": leader.strategy if leader else None,
            "top5": [{"name": x.name, "score": round(score_of(x)), "strategy": x.strategy}
                     for x in ranked[:5]],
            "alive_count": sum(1 for a in agents if a.alive),
            "deaths_total": sum(1 for a in agents if not a.alive),
            "stocks": {k: round(v) for k, v in stocks.items()},
            "scores": [round(score_of(a), 1) for a in agents],
            "health": [round(a.health, 1) for a in agents],
            "alive": [a.alive for a in agents],
            "has_tool": [len(a.tools) > 0 for a in agents],
            "tools": [list(a.tools) for a in agents],
            "shelter": [shelter_of(a) for a in agents],
            "food_eff": [round(eff_food(a), 1) for a in agents],
        })

    ranked = sorted(agents, key=lambda a: -score_of(a))
    winner = ranked[0]
    most_skilled = max(agents, key=lambda a: a.skill)
    hardest = max(agents, key=lambda a: a.work_ethic)
    strat_survival = {}
    for s in ("leader", "cooperator", "survivor", "hoarder", "loner", "thief"):
        members = [a for a in agents if a.strategy == s]
        if members:
            strat_survival[s] = {"n": len(members),
                                 "alive": sum(1 for a in members if a.alive),
                                 "rate": round(sum(1 for a in members if a.alive) / len(members), 3)}
    def fate(a):
        return {"name": a.name, "strategy": a.strategy, "traits": trait_dict(a),
                "alive": a.alive, "death_day": a.death_day,
                "final_rank": ranked.index(a) + 1, "final_score": round(score_of(a)),
                "health": round(a.health), "food_eff": round(eff_food(a), 1),
                "shelter": shelter_of(a), "group": a.group,
                "tools": a.tools, "days_hungry": a.days_hungry,
                "total_gathered": round(a.total_gathered), "total_stolen": round(a.total_stolen, 1)}
    log = {
        "seed": seed, "days": DAYS,
        "tools": TOOLS,
        "tool_holders_start": {t: agents[h].name for t, h in zip(TOOLS, holders)},
        "strategy_counts": {s: sum(1 for a in agents if a.strategy == s)
                            for s in ("leader", "cooperator", "survivor", "hoarder", "loner", "thief")},
        "n_groups": len(groups),
        "group_sizes_start": [len(g.members) for g in groups],
        "daily": daily,
        "events": events,
        "final_top10": [dict({"rank": i + 1}, **fate(a)) for i, a in enumerate(ranked[:10])],
        "winner": dict(fate(winner), strongest_trait=strongest_trait(winner)),
        "runner_up": fate(ranked[1]),
        "most_skilled": fate(most_skilled),
        "hardest_worker": fate(hardest),
        "total_deaths": sum(1 for a in agents if not a.alive),
        "alive_final": sum(1 for a in agents if a.alive),
        "survival_by_strategy": strat_survival,
        "median_final_score": round(sorted(score_of(a) for a in agents)[50]),
        "final_stocks": {k: round(v) for k, v in stocks.items()},
        "agents": [dict({"id": a.id, "name": a.name}, **fate(a)) for a in agents],
    }
    return log

if __name__ == "__main__":
    log = run()
    with open("sim_log.json", "w") as f:
        json.dump(log, f, indent=1)
    print("strategies:", log["strategy_counts"], "| groups:", log["n_groups"], log["group_sizes_start"])
    print("tool holders:", log["tool_holders_start"])
    print("winner:", log["winner"]["name"], log["winner"]["strategy"], log["winner"]["final_score"],
          "| runner-up:", log["runner_up"]["name"], log["runner_up"]["final_score"])
    print("deaths:", log["total_deaths"], "| alive:", log["alive_final"])
    print("survival:", log["survival_by_strategy"])
    print("most skilled:", log["most_skilled"]["name"], "alive:", log["most_skilled"]["alive"],
          "rank:", log["most_skilled"]["final_rank"])
    print("lead changes:", [(e["day"], e["who"]) for e in log["events"] if e["type"] == "lead_change"])
    print("deaths by day:", [(e["day"], e["who"]) for e in log["events"] if e["type"] == "death"][:20])
