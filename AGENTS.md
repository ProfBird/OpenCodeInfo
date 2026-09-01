# OpenCodeInfo — OpenCode Zen & Go Model Benchmarks & Cost

Static site + refresh script for OpenCode Zen model pricing, AA Coding Index, SWE-bench Pro, and AA SciCode.

## Commands
- Serve the page:            `python -m http.server` → http://localhost:8000/docs/index.html
- Update data:               `python update_zen_prices.py --output docs/models.json`   (adds/removes models, refreshes prices + SWE-bench Pro + AA SciCode)
- Preview changes:           `python update_zen_prices.py --dry-run --output docs/models.json`
- Prices only, no sync:      `python update_zen_prices.py --no-sync --output docs/models.json`
- Validate data file:        `python3 -m json.tool docs/models.json`

## Files
- `docs/index.html`          — the page (table, filters, sorting)
- `docs/models.json`         — data source (77 models); the page fetches this
- `update_zen_prices.py`     — fetches catalogs/pricing and rewrites docs/models.json
- `readme.md`                — usage docs (README.md)
- `.github/workflows/update_models.yml` — daily job (03:00 UTC) that runs the script and commits docs/models.json + docs/index.html

## models.json data model
Each entry: `name`, `params` (total parameters, e.g. "744B", "1.6T", `null` if undisclosed),
`context` (e.g. "1M", "500K"), `codingIndex` (AA Coding Index %, 0–100, `null` if unpublished),
`swePro` (SWE-bench Pro %, 0–100, `null` if unpublished),
`aaSciCode` (AA SciCode %, 0–100, `null` if unpublished),
`inputCost`/`outputCost`/`cachedReadCost` (USD per 1M tokens),
`plan` (`"go"` = Go $10/mo plan, `"zen"` = Zen-only), `hfUrl` (HF card, else BenchLM specs, else manufacturer).

## Update rules (update_zen_prices.py)
- Catalog = union of https://opencode.ai/zen/v1/models + .../zen/go/v1/models; `plan` reflects Go membership.
- Pricing from https://opencode.ai/docs/zen#pricing and https://opencode.ai/docs/go; Go price wins where both exist.
- Context/cost fallback from https://models.dev/api.json; `CONTEXT_OVERRIDES`/`PARAM_OVERRIDES`/`KNOWN_URLS` maps hold verified values.
- SWE-bench Pro + AA SciCode from https://benchlm.ai/data/models.json (`benchmarks.coding.swePro` / `.aaSciCode`); `BENCH_SLUG_OVERRIDES` maps display names to BenchLM slugs.
- Every run refreshes the "Checked <date>." footer note in docs/index.html (`update_checked_date`); dry-run never writes.
- Do NOT hand-edit models.json — run the script.

## Web page (docs/index.html)
- Columns: Model, Params, Context, AA Coding Index, SWE-bench Pro, AA SciCode, Output ($/1M).
- Filters: Plan (All Zen / Go only), Max output ($/1M), Min AA index, Min SWE-bench Pro, Min AA SciCode; Reset clears all.
- Click the sort button (⇅) or column header to sort; `null` scores/params sort last and render as "—". Benchmark header names link to the originator's page.