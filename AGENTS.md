# OpenCodeInfo — OpenCode Zen & Go Model Benchmarks & Cost

Static site + refresh script for OpenCode Zen model pricing, AA Coding Index, SWE-bench Pro, and AA SciCode.

## Commands
- Serve the page:            `python -m http.server` → http://localhost:8000/docs/index.html
- Update data:               `python update_zen_prices.py --output docs/models.json`   (adds/removes models, refreshes prices + SWE-bench Pro)
- Preview changes:           `python update_zen_prices.py --dry-run --output docs/models.json`
- Prices only, no sync:      `python update_zen_prices.py --no-sync --output docs/models.json`
- Validate data file:        `python3 -m json.tool docs/models.json`

## Files
- `docs/index.html`          — the page (table, filters, sorting)
- `docs/models.json`         — data source (77 models); the page fetches this
- `update_zen_prices.py`     — fetches catalogs/pricing and rewrites docs/models.json
- `opencode-go-models.md`    — markdown snapshot of the same data
- `readme.md`                — usage docs
- `.github/workflows/update_models.yml` — daily job (03:00 UTC) that runs the script and commits changes

## models.json data model
Each entry: `name`, `codingIndex` (AA Coding Index %, 0–100, `null` if unpublished),
`swePro` (SWE-bench Pro %, 0–100, `null` if unpublished),
`aaSciCode` (AA SciCode %, 0–100, `null` if unpublished),
`inputCost`/`outputCost`/`cachedReadCost` (USD per 1M tokens), `context` (e.g. "1M", "500K"),
`plan` (`"go"` = Go $10/mo plan, `"zen"` = Zen-only), `hfUrl` (HF card, else BenchLM specs, else manufacturer).

## Update rules (update_zen_prices.py)
- Catalog = union of https://opencode.ai/zen/v1/models + .../zen/go/v1/models; `plan` reflects Go membership.
- Pricing from https://opencode.ai/docs/zen#pricing and https://opencode.ai/docs/go; Go price wins where both exist.
- Context/cost fallback from https://models.dev/api.json; `CONTEXT_OVERRIDES`/`KNOWN_URLS` maps hold verified values.
- SWE-bench Pro + AA SciCode from https://benchlm.ai/data/models.json (`benchmarks.coding.swePro` / `.aaSciCode`); `BENCH_SLUG_OVERRIDES` maps display names to BenchLM slugs.
- Do NOT hand-edit models.json — run the script.

## Web page (docs/index.html)
- Columns: Model, AA Coding Index, SWE-bench Pro, AA SciCode, Input ($/1M), Output ($/1M), Context.
- Filters: Plan (All Zen / Go only), Max output ($/1M), Min AA index, Min SWE-bench Pro; Reset clears all.
- Click column headers to sort; `null` scores sort last and render as "—".