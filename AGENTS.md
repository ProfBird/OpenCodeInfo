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
`swePro` (SWE-bench Pro %, 0–100, `null` if unpublished),
`terminalBench` (Terminal-Bench %, 0–100, `null` if unpublished; 2.1 preferred, else 2.0),
`deepSwe` (DeepSWE %, 0–100, `null` if unpublished),
`inputCost`/`outputCost`/`cachedReadCost` (USD per 1M tokens),
`plan` (`"go"` = Go $10/mo plan, `"zen"` = Zen-only), `alsoOnZen` (`true` when a Go-plan model is also on Zen pay-as-you-go; omitted otherwise), `na` (`true` = N.A. — no longer selectable in OpenCode's model picker; omitted otherwise), `naSince` (ISO date the model was first flagged N.A.; only present with `na`),
`hfUrl` (HF card, else BenchLM specs, else manufacturer).

## Update rules (update_zen_prices.py)
- Catalog = union of https://opencode.ai/zen/v1/models + .../zen/go/v1/models; `plan` reflects Go membership, `alsoOnZen` marks Go-plan models present in the Zen catalog (Go price wins for those). Models that leave the catalogs are NEVER removed from models.json — they stay listed and keep their last-known data, flagged `na: true` by the availability check.
- Pricing from https://opencode.ai/docs/zen#pricing and https://opencode.ai/docs/go; Go price wins where both exist.
- Context/cost fallback from https://models.dev/api.json; `CONTEXT_OVERRIDES`/`PARAM_OVERRIDES`/`KNOWN_URLS` maps hold verified values.
- SWE-bench Pro + Terminal-Bench + DeepSWE from https://benchlm.ai/data/models.json (`benchmarks.coding.swePro` / `.terminalBench21`+`.terminalBench2` / `.deepSwe`); `BENCH_SLUG_OVERRIDES` maps display names to BenchLM slugs, `BENCH_SLUG_OVERRIDES_DEEPSWE`/`BENCH_SLUG_OVERRIDES_TERMINAL` override slug for the DeepSWE/Terminal-Bench fields only. `SWE_PRO_OVERRIDES` hardcodes Scale SWE-bench Pro scores BenchLM lacks (e.g. Claude Haiku 4.5 39.45, from labs.scale.com/leaderboard/swe_bench_pro_public). `BENCH_INHERIT_FROM` copies a free variant's benchmarks from its non-free counterpart (e.g. Ox Alpha Free ← GLM-5.3-Flash, incl. codingIndex from `.aaCodingIndex`).
- Availability: models.dev is the catalog OpenCode's model picker consumes; `na: true` when a model has no non-`deprecated` entry in either its `opencode` (Zen) or `opencode-go` (Go plan) provider. `naSince` is set on first flag (backfilled on the first run for pre-existing flags) and cleared when the model becomes available again.
- Pruning: prune_na_models.py removes rows whose `naSince` is older than 6 months (`--months` to override); rows with missing/bad `naSince` are never removed. The daily workflow runs it after the update.
- Every run refreshes the "Checked <date>." footer note in docs/index.html (`update_checked_date`); dry-run never writes.
- Do NOT hand-edit models.json — run the script.

## Web page (docs/index.html)
- Columns: Model, Params, Context, AA Coding Index, SWE-bench Pro, Terminal-Bench, DeepSWE, Output ($/1M).
- Filters: Plan (All Models / Zen Models = on Zen pay-as-you-go, incl. Go-plan models marked `alsoOnZen` / Go Plan Models) + "Available only" checkbox (hides `na` models), Min AA index, Min SWE-bench Pro, Min Terminal-Bench, Min DeepSWE, Max output ($/1M) — same order as the columns; Reset clears all.
- Click the sort button (⇅) or column header to sort; `null` scores/params sort last and render as "—". Benchmark header names link to the originator's page.