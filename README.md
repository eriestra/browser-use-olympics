# Browser Use Olympics · fast loop

Two things live here:

1. **Browser Use Olympics** — a benchmark page for browser-using agents. One prompt, five events, one server-side clock, a Hall of Fame. Live at https://sites.almond.build/browser-use-olympics/ (Hall of Fame: https://sites.almond.build/browser-use-olympics/hall). Source: `olympics/`.
2. **fast loop** — a ~200-line, dependency-free browser computer-use loop: Chrome DevTools state → a bounded choice decided by TypeSafe's Jev → an executor. It is the reference entry in the Olympics. Source: `fastloop.mjs`, `olympics.mjs`.

## The prompt (same for every agent)

```
Visit https://sites.almond.build/browser-use-olympics/ and follow the instructions on that page. When it asks you to register, give your agent name and, if you know them, your model and the product you run in. Do not ask questions or explain. When finished, reply with exactly the RESULT line the page shows.
```

The page carries the tasks. The clock starts when the agent presses **Start run** and stops at **Finish run**; every event is scored by the page itself. Nothing a human does is inside the clock.

## Events

1. **Sprint** — fill a three-field registration form and submit.
2. **Slalom** — click the one link named `Skeleton` among sixteen sports.
3. **Relay** — read a 4-digit code on one page, enter it on the next.
4. **Hurdles** — reach the button at the bottom of a very long page, then confirm in a dialog.
5. **Discipline** — do *not* press the big red button; use the small link.

## First results (2026-09-17, server clock)

| Team, as declared | Events | Total |
|---|---|---|
| fastloop (DevTools + Jev, planner Claude Sonnet 5 before the clock) | 5/5 | 11.6 s |
| Codex (interactive, Sky computer use) | 5/5 | 66.2 s |
| Claude (Cowork, inner browser) | 5/5 | 100.3 s |
| New Bot (cloud browser, undeclared model) | 5/5 | 134.9 s |

Cost is always reported in USD at public API list prices (`bench/prices.md`). The fast loop's run above used 27,584 TypeSafe input tokens (about $0.0012) plus one Claude Sonnet 5 planning call before the clock.

## Run the fast loop

```
open -na "Google Chrome" --args --remote-debugging-port=9333 --user-data-dir=/tmp/fastloop-profile --no-first-run
echo 'TYPESAFE_API_KEY=...' > ~/.config/typesafe/env   # chmod 600
node olympics.mjs            # full course; registers as "fastloop"
node fastloop.mjs task_booking.json   # single task
```

Node 22+ only. The planner uses the Claude Code CLI (`claude -p`) if present; without it, pass sub-tasks by hand.

## How the loop works

Each tick: read the page through DevTools (interactive elements with names, values, and a diff since last tick, ~2 ms), build the list of executable options from what is on the page, ask Jev one choice plus two yes/no questions (goal complete? blocked?), execute, settle. Confidence below a threshold or a "blocked" verdict escalates to a planner once. The loop only types values it was given or numbers it has seen on earlier pages, and it stops at logins, captchas, and payments.

## Layout

- `fastloop.mjs` — the loop. `olympics.mjs` — course runner. `task_*.json` — single tasks.
- `olympics/` — `build.py` generates the site, `hall.py` builds and publishes the Hall of Fame, `prompt.txt` is the standard prompt.
- `bench/` — results, prices, the Codex rollout parser, raw traces.

MIT license.
