# OpenCodeInfo — OpenCode Zen & Go Model Benchmarks & Cost

Static site + refresh script for OpenCode Zen model pricing, AA Coding Index, SWE-bench Pro, Terminal-Bench, and DeepSWE.

## Commands
- Serve the page:            `python -m http.server` → http://localhost:8000/docs/index.html
- Update data:               `python update_zen_prices.py --output docs/models.json`   (adds models, refreshes prices + SWE-bench Pro + Terminal-Bench + DeepSWE; flags N.A., never removes)
- Prune stale N.A. models:   `python prune_na_models.py --output docs/models.json`     (removes models N.A. for over 6 months; `--dry-run` to preview)
- Preview changes:           `python update_zen_prices.py --dry-run --output docs/models.json`
- Prices only, no sync:      `python update_zen_prices.py --no-sync --output docs/models.json`
- Validate data file:        `python3 -m json.tool docs/models.json`

## Files
- `docs/index.html`          — the page (table, filters, sorting)
- `docs/models.json`         — data source (79 models); the page fetches this
- `update_zen_prices.py`     — fetches catalogs/pricing and rewrites docs/models.json
- `prune_na_models.py`       — removes models N.A. for over 6 months (uses `naSince`)
- `readme.md`                — usage docs (README.md)
- `.github/workflows/update_models.yml` — daily job (03:00 UTC) that runs the update script + the N.A. prune and commits docs/models.json + docs/index.html

## models.json data model
Each entry: `name`, `params` (total parameters, e.g. "744B", "1.6T", `null` if undisclosed),
`context` (e.g. "1M", "500K"), `codingIndex` (AA Coding Index %, 0–100, `null` if unpublished),
`swePro` (SWE-bench Pro %, 0–100, `null` if unpublished; may be a string like `"9.67?"` when inherited from an unconfirmed identity),
`terminalBench` (Terminal-Bench %, 0–100, `null` if unpublished; 2.1 preferred, else 2.0),
`deepSwe` (DeepSWE %, 0–100, `null` if unpublished),
`inputCost`/`outputCost`/`cachedReadCost` (USD per 1M tokens),
`plan` (`"go"` = Go $10/mo plan, `"zen"` = Zen-only, `"openrouter"` = OpenRouter programming-category row with OpenRouter's own pricing/context, which can differ from its Zen/Go twins; the page badges rows (Zen)/(Go)/(Go · Zen)/(OpenRouter) after the model link), `alsoOnZen` (`true` when a Go-plan model is also on Zen pay-as-you-go; omitted otherwise), `na` (`true` = N.A. — no longer selectable in OpenCode's model picker; only applied to zen/go rows; omitted otherwise), `naSince` (ISO date the model was first flagged N.A.; only present with `na`),
`hfUrl` (HF card, else BenchLM specs, else manufacturer), `addedOn` (ISO date the model was added to the page; only present within its first month — the page badges it green "(New)" with the added date as tooltip).

## Update rules (update_zen_prices.py)
- Catalog = union of https://opencode.ai/zen/v1/models + .../zen/go/v1/models; `plan` reflects Go membership, `alsoOnZen` marks Go-plan models present in the Zen catalog (Go price wins for those). Models that leave the catalogs are NEVER removed from models.json — they stay listed and keep their last-known data, flagged `na: true` by the availability check.
- OpenRouter: `sync_openrouter` adds/updates rows for the Programming-category models listed in `OPENROUTER_DISPLAY` (36 verified of the 47 shown by https://openrouter.ai/models?categories=programming — the UI computes that list client-side; all are also present in the OpenCode model picker via the user's OpenRouter provider) as `plan: "openrouter"`, named with the bare display name — OpenRouter pricing/context can differ from Zen/Go, so twins get separate rows distinguished by the page's (OpenRouter) badge (legacy "<Display> (OpenRouter)" names are renamed on sync). `reconcile` never touches openrouter rows (separate identity space). The script fetches the full catalog (https://openrouter.ai/api/v1/models) and syncs only mapped ids. `OPENROUTER_DISPLAY`/`OPENROUTER_PARAMS` map ids; params mirror the Zen/Go twins. `OPENROUTER_CODING_INDEX` holds AA Coding Index values from OpenRouter's benchmarks API (auth required, so curated snapshots; matched per model build — e.g. 0731↔20260731). OpenRouter rows are skipped by the N.A. pass but DO get BenchLM swePro/terminalBench/deepSwe via `merge_benchmarks` (same underlying model). `cross_copy_benchmarks` then fills any benchmark field still missing on one twin from the other (both directions, incl. codingIndex; never overwrites existing values), so Zen/Go rows and their OpenRouter twins show identical benchmarks. Note: OpenRouter adds a 5.5% service charge on top of its listed prices — rows show listed prices, and the page header says so.
- Pricing from https://opencode.ai/docs/zen#pricing and https://opencode.ai/docs/go; Go price wins where both exist.
- Context/cost fallback from https://models.dev/api.json; `CONTEXT_OVERRIDES`/`PARAM_OVERRIDES`/`KNOWN_URLS` maps hold verified values. A trailing `?` in params/context values (e.g. Big Pickle `357B?`) marks inferred/uncertain figures — the page renders it verbatim and sorts it as if the `?` were absent.
- SWE-bench Pro + Terminal-Bench + DeepSWE from https://benchlm.ai/data/models.json (`benchmarks.coding.swePro` / `.terminalBench21`+`.terminalBench2` / `.deepSwe`); `BENCH_SLUG_OVERRIDES` maps display names to BenchLM slugs, `BENCH_SLUG_OVERRIDES_DEEPSWE`/`BENCH_SLUG_OVERRIDES_TERMINAL` override slug for the DeepSWE/Terminal-Bench fields only. `SWE_PRO_OVERRIDES` hardcodes Scale SWE-bench Pro scores BenchLM lacks (e.g. Claude Haiku 4.5 39.45, from labs.scale.com/leaderboard/swe_bench_pro_public). `BENCH_INHERIT_FROM` copies a free variant's benchmarks from its non-free counterpart (e.g. Ox Alpha Free ← GLM-5.3-Flash, incl. codingIndex from `.aaCodingIndex`). `UNCERTAIN_BENCH_OVERRIDES` stores identity-inferred scores verbatim with a trailing `?` (Big Pickle swePro `9.67?` = GLM-4.6's Scale score, terminalBench `49.4?` = GLM-4.6's AA Terminal-Bench v2.1 run) — benchmark fields may carry `?`, which the page renders verbatim and filters/sorts numerically; a real published score replaces them (comparisons are numeric).
- Availability: models.dev is the catalog OpenCode's model picker consumes; `na: true` when a model has no non-`deprecated` entry in either its `opencode` (Zen) or `opencode-go` (Go plan) provider. `naSince` is set on first flag (backfilled on the first run for pre-existing flags) and cleared when the model becomes available again.
- Pruning: prune_na_models.py removes rows whose `naSince` is older than 6 months (`--months` to override); rows with missing/bad `naSince` are never removed. The daily workflow runs it after the update.
- New models: `reconcile`/`sync_openrouter` stamp new rows with `addedOn` (ISO date); the page shows a green "(New)" badge (tooltip = added date, e.g. "Added Sep 2, 2026") while under one calendar month old. Each run drops `addedOn` flags a month or older (`prune_new_flags`); existing rows never gain the badge retroactively.
- Every run refreshes the "Checked <date>." footer note in docs/index.html (`update_checked_date`); dry-run never writes.
- Do NOT hand-edit models.json — run the script.

## Web page (docs/index.html)
- Columns: Model, Params, Context, AA Coding Index, SWE-bench Pro, Terminal-Bench, DeepSWE, Output ($/1M).
- Filters: Plan (All Models / Zen Models = on Zen pay-as-you-go, incl. Go-plan models marked `alsoOnZen` / Go Plan Models / OpenRouter Models) + "Available only" checkbox (hides `na` models), Min AA index, Min SWE-bench Pro, Min Terminal-Bench, Min DeepSWE, Max output ($/1M) — same order as the columns; Reset clears all.
- Click the sort button (⇅) or column header to sort; `null` scores/params sort last and render as "—". Selecting a new sort column keeps the previous sort as the secondary (tiebreaker) sort; Reset clears it. Benchmark header names link to the originator's page.