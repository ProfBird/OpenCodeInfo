# OpenCode Zen & Go — Model Benchmarks & Cost

A small static web page that displays **all OpenCode Zen models** (coding benchmark scores, pricing, context) with sortable columns, a computed value index, filters, and a Go-plan toggle.

**Live page:** <https://ProfBird.github.io/OpenCodeInfo/>

## Files

- `docs/models.json` — Model data: AA Coding Index score, USD-per-1M-token pricing (input, output, cached read), context window, and a `plan` field (`"go"` for models on the Go $10/mo plan, `"zen"` for Zen-only) for every model in the Zen catalog. Each model also has a link (`hfUrl`) to its model card — Hugging Face when weights are open, otherwise BenchLM model specs, or the manufacturer's site.
- `docs/index.html` — The page itself. Loads `models.json` and renders the table. AA Coding Index → Value Index computation, filtering, and sorting all happen in the browser. Published to GitHub Pages via the `docs/` folder.
- `update_zen_prices.py` — Fetches the current OpenCode Zen catalog and pricing, the Go plan, and model context/cost data, then updates `docs/models.json` (adds/removes models that join or leave the Zen catalog, refreshes prices, maintains the `plan` flag).
- `opencode-go-models.md` — A Markdown snapshot of the same data.
- `.github/workflows/update_models.yml` — Daily GitHub Actions job (03:00 UTC) that runs the update script and commits any changes to `docs/models.json`.

## Usage

1. Start a local server (required because browsers block `fetch` on `file://`):

   ```bash
   cd docs && python -m http.server
   ```

2. Open <http://localhost:8000/>.

## Sorting & filtering

- Click any column header to sort (click again to reverse direction).
- **Plan** filter: show all Zen models or just the **Go** plan subset.
- Filter by **Max output price ($/1M)** and **Min AA index**.
- **Reset** clears all filters and restores the default (alphabetical) order.
- Models with no benchmark score (`—`) sort to the bottom when sorting by benchmark.

## Value Index

Computed in the browser for each row:

```
Value Index = (AA³ × (Context/1M)^0.3) ÷ (1 + Output $/1M)
```

normalized so the best model scores 100. AA Coding Index is cubed (dominant), context window enters sub-linearly (`^0.3`, so 1M = 1.00, 500K ≈ 0.81, 256K ≈ 0.66), and price has diminishing returns via the `1 + cost` denominator.

## Updating the data

```bash
python update_zen_prices.py --output docs/models.json  # fetch + update in place
python update_zen_prices.py --dry-run --output docs/models.json # preview changes without writing
python update_zen_prices.py --no-sync --output docs/models.json # only refresh prices of existing models
python update_zen_prices.py --verbose --output docs/models.json # show parsed sources and per-model changes
```

The GitHub Actions workflow runs the same command on a daily schedule and pushes any changes.

Sources:

- **Catalog** — `https://opencode.ai/zen/v1/models` (all Zen models) and `https://opencode.ai/zen/go/v1/models` (Go plan subset, `plan: "go"`).
- **Pricing** — `https://opencode.ai/docs/zen#pricing` (Zen pay-per-use) and `https://opencode.ai/docs/go` (Go plan pricing table). Go plan pricing wins where a model is on both.
- **Context / cost fallback** — `https://models.dev/api.json` (opencode provider), with verified context overrides in the script.
- **Benchmark** — AA Coding Index via the BenchLM mirror: `https://benchlm.ai/benchmarks/aacodingindex` (display-only mirror of Artificial Analysis), snapshot 2026-08-21.

Models that appear in the catalog but aren't priced in either docs table are shown as `Free` until a price is published.
