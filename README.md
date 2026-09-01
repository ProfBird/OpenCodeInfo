# OpenCode Zen & Go — Model Benchmarks & Cost

A small static web page that displays **all OpenCode Zen models** (coding benchmark scores, pricing, context) with sortable columns, a SWE-bench Pro score column, filters, and a Go-plan toggle.

**Live page:** <https://ProfBird.github.io/AiModelinfo/>

## Files

- `docs/models.json` — Model data: AA Coding Index score, SWE-bench Pro score, Terminal-Bench score, DeepSWE score, USD-per-1M-token pricing (input, output, cached read), `params` (total parameters, e.g. "744B", "1.6T", `null` if undisclosed), `context` window (e.g. "1M", "500K"), a `plan` field (`"go"` for models on the Go $10/mo plan, `"zen"` for Zen-only, `"openrouter"` for OpenRouter's programming-category models, listed as "<Display> (OpenRouter)" with OpenRouter's own pricing), `alsoOnZen: true` when a Go-plan model is also available on Zen pay-as-you-go, and `na: true` when a model is no longer selectable in OpenCode (shown as (N.A.) on the page), for every model in the Zen catalog. Models that leave the catalog are never removed; they stay listed as (N.A.). Each model also has a link (`hfUrl`) to its model card — Hugging Face when weights are open, otherwise BenchLM model specs, or the manufacturer's site.
- `docs/index.html` — The page itself. Loads `models.json` and renders the table. Filtering and sorting all happen in the browser. Published to GitHub Pages via the `docs/` folder.
- `update_zen_prices.py` — Fetches the current OpenCode Zen catalog and pricing, the Go plan, model context/cost data, and SWE-bench Pro / Terminal-Bench / DeepSWE scores, then updates `docs/models.json` (adds models that join the catalog, refreshes prices, maintains the `plan`/`alsoOnZen` flags, and flags models that are no longer selectable in OpenCode as `na` — models are never removed).
- `prune_na_models.py` — Removes models that have been flagged `na` (N.A.) for over 6 months (tracked via each model's `naSince` date); `--dry-run` previews, `--months` overrides the cutoff. Run automatically in the daily CI job after the update.
- `.github/workflows/update_models.yml` — Daily GitHub Actions job (03:00 UTC) that runs the update script and commits any changes to `docs/models.json` and `docs/index.html`.

## Usage

1. Start a local server (required because browsers block `fetch` on `file://`):

   ```bash
   cd docs && python -m http.server
   ```

2. Open <http://localhost:8000/>.

## Sorting & filtering

- Click the sort button (⇅) next to a column name, or the column header itself, to sort (click again to reverse direction).
- **Plan** filter: show all models, models available on Zen pay-as-you-go (including Go-plan models also on Zen), **Go Plan** models only, or **OpenRouter** programming-category models (36 verified of OpenRouter's 47; separate rows with OpenRouter's own pricing, named "<Display> (OpenRouter)").
- **Available only** checkbox: hide models marked (N.A.) — those no longer selectable in OpenCode's model picker.
- Filter by **Min AA index**, **Min SWE-bench Pro**, **Min Terminal-Bench**, **Min DeepSWE**, and **Max output price ($/1M)** — same order as the columns.
- **Reset** clears all filters and restores the default (alphabetical) order.
- Models with no benchmark score (`—`) sort to the bottom when sorting by benchmark.

## SWE-bench Pro

Scale AI's contamination-resistant coding benchmark (1,865 tasks, standardized harness), mirrored from BenchLM. Scores are % of tasks resolved. OpenAI's July 2026 audit found ~30% of its public tasks broken, so treat values as directional.

## Terminal-Bench

Laude Institute's agentic terminal & CLI coding benchmark, mirrored from BenchLM. Shows Terminal-Bench 2.1 where published, otherwise 2.0. Scores are % of tasks resolved.

## DeepSWE

Datacurve's contamination-free long-horizon repository benchmark (113 tasks across 91 repos), pass@1, mirrored from BenchLM. Only models with a published score are shown.

## Updating the data

```bash
python update_zen_prices.py --output docs/models.json  # fetch + update in place
python update_zen_prices.py --dry-run --output docs/models.json # preview changes without writing
python update_zen_prices.py --no-sync --output docs/models.json # only refresh prices of existing models
python update_zen_prices.py --verbose --output docs/models.json # show parsed sources and per-model changes
python prune_na_models.py --output docs/models.json    # remove models N.A. for over 6 months
python prune_na_models.py --dry-run --output docs/models.json   # preview the prune without writing
```

The GitHub Actions workflow runs the same command on a daily schedule and pushes any changes.

Sources:

- **Catalog** — `https://opencode.ai/zen/v1/models` (all Zen models) and `https://opencode.ai/zen/go/v1/models` (Go plan subset, `plan: "go"`).
- **Pricing** — `https://opencode.ai/docs/zen#pricing` (Zen pay-per-use) and `https://opencode.ai/docs/go` (Go plan pricing table). Go plan pricing wins where a model is on both.
- **Context / cost fallback** — `https://models.dev/api.json` (opencode provider), with verified context overrides in the script.
- **Benchmark (AA)** — AA Coding Index via the BenchLM mirror: `https://benchlm.ai/benchmarks/aacodingindex` (display-only mirror of Artificial Analysis), snapshot 2026-08-21.
- **Benchmark (SWE-bench Pro)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.swePro`), refreshed on every run.
- **Benchmark (Terminal-Bench)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.terminalBench21`, fallback `terminalBench2`), refreshed on every run.
- **Benchmark (DeepSWE)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.deepSwe`), refreshed on every run.

Models that appear in the catalog but aren't priced in either docs table are shown as `Free` until a price is published.
