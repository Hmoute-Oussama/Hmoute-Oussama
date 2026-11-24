# Maintenance

Everything a future change needs, in the order it is usually needed.

---

## Where to edit what

| I want to change | Edit | Then |
|:--|:--|:--|
| The experiments listed on the profile | `config/profile.yml` → `experiments` | push; the workflow regenerates the panel |
| A project's problem, decisions, stack or status | `config/profile.yml` → `projects` | the README tables are hand-written, so update those too |
| The statement in the hero | `assets/hero.svg` (the typed line) | commit |
| Add a new featured system | `config/profile.yml` + a new `assets/systems/*.svg` + a README block | commit |
| Domain names or relationships | `config/profile.yml` → `domains`, `edges`, and `assets/universe.svg` | commit |
| A palette or type colour | `scripts/theme.py` (generated) and the literal in each hand-written SVG | run the generator |
| Contact links | `README.md` (three places) and `assets/closing.svg` | commit |

`config/profile.yml` is the source of truth for everything that is not fetched. Nothing
in it is inferred or generated: every claim must be traceable to a repository that exists.

---

## Running the generator locally

```bash
pip install pyyaml
python scripts/validate_assets.py        # checks all 13 assets parse
python scripts/build_assets.py           # real run, needs network
python scripts/build_assets.py --offline # exercises the fallback paths
```

`GITHUB_TOKEN` is optional locally. Without it the public API rate limit is 60 requests
per hour, which the four-page repository fetch can approach on a busy hour.

Write only `assets/generated/` from the generator. It is overwritten wholesale; a manual
edit there survives exactly until the next run.

---

## The workflow

`.github/workflows/assets.yml` runs:

* on a weekly schedule (Mondays 04:17 UTC),
* on demand (`workflow_dispatch`),
* on a push touching `config/profile.yml`, `scripts/**` or the workflow itself.

It validates the hand-written assets, regenerates the dynamic ones, validates again, and
commits **only if `assets/generated/` actually changed**. It needs `contents: write`,
which is granted at workflow level and nowhere else. Commits are attributed to
`github-actions[bot]`.

If the schedule needs to be tighter, change the cron line. Because the assets carry no
timestamp, a more frequent schedule does not mean more commits: it means the profile
updates sooner after real activity.

---

## Common tasks

**Add or retire an experiment.** Append or delete an entry under `experiments:` in
`config/profile.yml`. The panel height is computed from the list length, so there is
nothing else to adjust. Keep the list short; three to six entries reads as focus, ten
reads as a wish list.

**Add a featured system.** Four things: a `projects` entry in the config, an
`assets/systems/<name>.svg` following the pattern of `verity.svg` (1100×330, stage panels
at `y="92"` height `72`, artefacts at `y="180"`, footer rules at `y="248"`), a README
block with the five-row table, and a link. Update the count in "Four systems with a spine".

**Change the accent of a project.** Set `accent:` in the config and change the stage
fills in that project's SVG. The README does not use the accent, so nothing else moves.

**Point the generator at a different account.** Change `identity.handle` in the config.
The contribution graph URL and every API path are built from it.

---

## Troubleshooting

**An asset shows "DATA UNAVAILABLE".** The fetch failed: rate limit, network, or changed
markup. Run `python scripts/build_assets.py` locally and read the `fetched:` line — it
reports `user`, `repos` and `days` status separately. The profile is still correct; it is
showing the last good data.

**The contribution calendar is scrambled.** The grid position of a day must be derived
from its date, not its index, because GitHub emits the table by weekday row. See
`_layout_days` in `scripts/render.py`.

**Punctuation renders as `&amp;#183;`.** Something bypassed `theme.esc()`. Do not
hand-escaped strings before passing them to a renderer; `esc()` already protects existing
character references.

**An SVG renders blank on GitHub but opens locally.** Almost always malformed XML —
GitHub's proxy serves the file only if it parses. Run `python scripts/validate_assets.py`.
The most common cause is `--` inside an XML comment.

**A change does not appear on GitHub.** Camo, GitHub's image proxy, caches by URL. The
generated filenames are stable, so a refreshed asset can be served from cache for a
short while. Hard-refresh the profile page; do not add cache-busting query strings, which
would create a new commit every run.

**The workflow pushes nothing.** That is the intended behaviour when the numbers did not
change. To confirm, run the generator locally and check whether `git status` reports
`assets/generated` as modified.

---

## Reviewing a change

Before committing anything that touches the profile:

1. `python scripts/validate_assets.py` — every asset parses.
2. `python scripts/build_assets.py --offline` — the degraded paths still render.
3. `python scripts/build_assets.py` — the live paths still render.
4. Open the changed SVG in a browser and confirm it reads at a glance.
5. Confirm no emoji, no fabricated metric and no fork presented as original work entered
   the diff.
