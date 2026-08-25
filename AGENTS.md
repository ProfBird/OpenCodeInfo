# OpenCodeInfo — OpenCode Zen & Go Model Benchmarks & Cost

Static site + refresh script for OpenCode Zen model pricing and AA Coding Index.

## Commands
- Serve the page:            `python -m http.server` → http://localhost:8000/models.html
- Update data:               `python update_zen_prices.py`          (adds/removes models, refreshes prices)
- Preview changes:           `python update_zen_prices.py --dry-run`
- Prices only, no sync:      `python update_zen_prices.py --no-sync`
- Validate data file:        `python3 -m json.tool models.json`

## Files
- `models.html`            — the page (table, Value Index, filters, sorting)
- `models.json`            — data source (77 models); the page fetches this
- `update_zen_prices.py`   — fetches catalogs/pricing and rewrites models.json
- `opencode-go-models.md`  — markdown snapshot of the same data
- `readme.md`              — usage docs

## models.json data model
Each entry: `name`, `codingIndex` (AA Coding Index %, 0–100, `null` if unpublished),
`inputCost`/`outputCost`/`cachedReadCost` (USD per 1M tokens), `context` (e.g. "1M", "500K"),
`plan` (`"go"` = Go $10/mo plan, `"zen"` = Zen-only), `hfUrl` (HF card, else BenchLM specs, else manufacturer).

## Update rules (update_zen_prices.py)
- Catalog = union of https://opencode.ai/zen/v1/models + .../zen/go/v1/models; `plan` reflects Go membership.
- Pricing from https://opencode.ai/docs/zen#pricing and https://opencode.ai/docs/go; Go price wins where both exist.
- Context/cost fallback from https://models.dev/api.json; `CONTEXT_OVERRIDES`/`KNOWN_URLS` maps hold verified values.
- Do NOT hand-edit models.json — run the script.

## Web page (models.html)
- Value Index (client-side, 0–100): `(AA³ × (Context/1M)^0.3) ÷ (1 + Output $/1M)`, normalized so best = 100.
- Filters: Plan (All Zen / Go only), Max output ($/1M), Min AA index; Reset clears all.
- Click column headers to sort; `null` scores sort last and render as "—".