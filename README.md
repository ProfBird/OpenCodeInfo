# OpenCode Zen & Go — Model Benchmarks & Cost

A small static web page that displays **all OpenCode Zen models** (coding benchmark scores, pricing, context) with sortable columns, a SWE-bench Pro score column, filters, and a Go-plan toggle.

**Live page:** <a href="https://profbird.github.io/OpenCodeInfo/" target="_blank">https://profbird.github.io/OpenCodeInfo/</a>

## Files

- `docs/models.json` — Model data: composite benchmark rank (`rank`), AA Coding Index score, SWE-bench Pro score, Terminal-Bench 2 score, Terminal-Bench 4 score, DeepSWE score, USD-per-1M-token pricing (input, output, cached read), `params` (total parameters, e.g. "744B", "1.6T", `null` if undisclosed), `context` window (e.g. "1M", "500K"), a `plan` field (`"go"` for models on the Go $10/mo plan, `"zen"` for Zen-only, `"openrouter"` for OpenRouter's programming-category models, which carry OpenRouter's own pricing and are badged (OpenRouter) on the page), `alsoOnZen: true` when a Go-plan model is also available on Zen pay-as-you-go, and `na: true` when a model is no longer selectable in OpenCode (shown as (N.A.) on the page), for every model in the Zen catalog. Models that leave the catalog are never removed; they stay listed as (N.A.). Each model also has a link (`hfUrl`) to its model card — Hugging Face when weights are open, otherwise BenchLM model specs, or the manufacturer's site.
- `docs/index.html` — The page itself. Loads `models.json` and renders the table. Filtering and sorting all happen in the browser. Published to GitHub Pages via the `docs/` folder.
- `update_zen_prices.py` — Fetches the current OpenCode Zen catalog and pricing, the Go plan, model context/cost data, and SWE-bench Pro / Terminal-Bench 2 & 4 / DeepSWE scores, computes transitive rankings, then updates `docs/models.json` (adds models that join the catalog, refreshes prices, maintains the `plan`/`alsoOnZen` flags, and flags models that are no longer selectable in OpenCode as `na` — models are never removed).
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
- **Plan** filter: show all models, recently added (**New**) models, models available on Zen pay-as-you-go (including Go-plan models also on Zen), **Go Plan** models only, or **OpenRouter** programming-category models (36 verified of OpenRouter's 47; separate rows with OpenRouter's own pricing, badged (OpenRouter)).
- **Available only** checkbox: hide models marked (N.A.) — those no longer selectable in OpenCode's model picker.
- Filter by **Min AA index**, **Min SWE-bench Pro**, **Min Terminal-Bench 2**, **Min Terminal-Bench 4**, **Min DeepSWE**, and **Max output price ($/1M)** — same order as the columns.
- **Reset** clears all filters and restores the default (alphabetical) order.
- Models with no benchmark score (`—`) sort to the bottom when sorting by benchmark.

## Ranking

Composite ranking across all 5 benchmark suites (AA Coding Index, SWE-bench Pro, Terminal-Bench 2, Terminal-Bench 4, and DeepSWE) calculated via transitive harmonic pairwise ranking (HodgeRank). Suite weights reflect test recency and rigor (Terminal-Bench 4: 1.5×, DeepSWE: 1.5×, SWE-bench Pro: 1.0×, AA Coding Index: 1.0×, Terminal-Bench 2: 0.5×). Models are first ranked within each suite (using fractional tie percentiles), pairwise comparison graphs are formed with edge weights matching the sum of shared benchmark weights, and a harmonic potential solver calculates latent skill ratings so models evaluated on disjoint benchmark suites are ranked transitively through bridge models. Standard competition ranking assigns integer ranks (1..N) to all benchmarked models; unranked models receive `—`.

## SWE-bench Pro

Scale AI's contamination-resistant coding benchmark (1,865 tasks, standardized harness), mirrored from BenchLM. Scores are % of tasks resolved. OpenAI's July 2026 audit found ~30% of its public tasks broken, so treat values as directional.

## Terminal-Bench 2

Laude Institute's agentic terminal & CLI coding benchmark (89 tasks, v2.1 / v2.0), mirrored from BenchLM. Scores are % of tasks resolved. Note: TB2 scores are not comparable to TB4 scores.

## Terminal-Bench 4

Laude Institute's redesigned agentic terminal coding benchmark (66 tasks, v4.1 / v4.0 / AA), built to evaluate long-horizon reasoning and robustness against distribution shifts and dataset contamination. Scores across models are substantially lower (e.g. Gemini 3.8 Flash drops from 89.4% on TB2 to 18.2% on TB4) and are not comparable to TB2.

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
- **Benchmark (Terminal-Bench 2)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.terminalBench21`, fallback `terminalBench2`), refreshed on every run.
- **Benchmark (Terminal-Bench 4)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.terminalBench41` / `agentic.terminalBench41` / `terminalBench4` / `aaTerminalBench4`), refreshed on every run.
- **Benchmark (DeepSWE)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.deepSwe`), refreshed on every run.

Models that appear in the catalog but aren't priced in either docs table are shown as `Free` until a price is published.
