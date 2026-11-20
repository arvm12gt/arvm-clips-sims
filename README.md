# arvm clips — simulation sources

Every video on the **arvm clips** YouTube channel is the story of a real,
runnable simulation. This repository publishes the code and the full run
data behind each episode, so anyone can reproduce our results — or prove
us wrong.

No scripted winners. The story in each video is whatever the simulation
actually did.

## EP01 — 100 people, $10,000 each, 30 days, no rules

*Folder: [`ep01/`](ep01/)*

An agent-based model of a tiny money town: 100 agents, each rolled from
five traits (skill, grit, risk appetite, honesty, luck), each following a
strategy derived from those traits — working, building businesses,
gambling, lending, stealing. Thirty days later, who ends up richest?

- Featured run (the one in the video): seed `20261120` → winner **Ann,
  $69,836**. Full log: [`ep01/sim_log.json`](ep01/sim_log.json)
- Aggregate: the same town run 100 times (seeds 1–100). Winners grouped
  by strongest trait: quiet builders 43, geniuses 41, workhorses 11,
  gamblers 4, other 1. Full data: [`ep01/aggregate_log.json`](ep01/aggregate_log.json)
- Full reproduction guide, parameter table and honesty notes:
  [`ep01/REPRODUCE.md`](ep01/REPRODUCE.md)

### Reproduce it in one minute

Requires only Python 3 (standard library, nothing to install):

```bash
cd ep01
python3 sim.py        # rewrites sim_log.json — should be identical to the committed one
python3 batch_run.py  # rewrites aggregate_log.json — same
```

If your output differs from the committed logs, open an issue and tell us
your Python version — determinism is the whole point of this repo.

## Honesty note

The parameters in these models are design choices: they encode the
mechanisms we want to explore (compounding, risk of ruin, luck vs. skill).
Results *illustrate* those principles; they are not evidence about the
real world, and we say so in the videos.

## License

MIT — see [`LICENSE`](LICENSE). Run it, remix it, make your own town.
