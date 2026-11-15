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

## Composite Ranking & Benchmark Methodology

The site computes an automatic, objective composite rank across all evaluated models whenever new benchmarks or models are added.

### Ranking Algorithm: Standardized Multi-Suite Skill with Cohort Calibration & Bayesian Coverage

Raw percentage scores from different coding benchmarks cannot be directly averaged or compared. Different benchmarks exhibit vastly different difficulty curves, scales, and score distributions: for example, resolving 67% of tasks on **Terminal-Bench 4** is state-of-the-art frontier performance (#1 in the catalog), whereas 67% on **Terminal-Bench 2** is mid-tier.

Furthermore, naive z-score normalization suffers from **cohort selection bias**: cutting-edge benchmarks like **Terminal-Bench 4** and **DeepSWE** were designed in late 2026 and have only evaluated high-capability frontier models (models tested on TB4 average 85.8% on TB2, compared to the catalog average of 75.2%). Comparing a lightweight or mid-tier model against frontier giants on TB4 yields a negative z-score, while older models that never participated in TB4 escape the comparison entirely.

To provide fair, accurate, and contamination-resistant rankings across the entire catalog, the ranking pipeline uses **Standardized Multi-Suite Skill with Benchmark Cohort Calibration (Anchored Equating) and Bayesian Coverage Weighting**:

1. **Standardized Raw Z-Scores:** For each benchmark suite $f$, the pipeline computes the sample mean $\mu_f$ and standard deviation $\sigma_f$ across all models evaluated on that suite, converting raw scores $x_{m,f}$ to standard units:
   $$Z_{m,f}^{\text{raw}} = \frac{x_{m,f} - \mu_f}{\sigma_f}$$

2. **Benchmark Cohort Calibration (Anchored Equating):**
   Because different benchmarks evaluate non-equivalent cohorts, tests taken by elite models have higher raw sample means than broad tests taken across the whole catalog.
   
   To align all benchmarks onto a unified global baseline, the pipeline uses "bridge models" (models evaluated across multiple suites) to iteratively estimate the latent cohort ability offset $C_f$ for each benchmark:
   $$C_f = \frac{1}{|M_f|} \sum_{m \in M_f} \hat{R}_m^{(-f)} - \bar{C}$$
   Where $\hat{R}_m^{(-f)}$ is model $m$'s composite performance across all suites *other* than $f$, and $\bar{C}$ centers the offsets. Calibrated z-scores are then computed as:
   $$Z_{m,f}^{\text{calibrated}} = Z_{m,f}^{\text{raw}} + C_f$$
   This prevents participation penalties: scoring 18.2% on TB4 is recognized as a respectable result on a frontier benchmark rather than penalized as a failure.

3. **Suite Weighting:** Each suite is assigned an explicit importance weight $w_f$ reflecting test recency, evaluation rigor, and resistance to contamination (see [Suite Weighting Rationale](#suite-weighting-rationale) below).

4. **Bayesian Coverage Shrinkage ($\lambda_{\text{prior}} = 0.6$):**
   Simply calculating a weighted average of available scores introduces severe selection bias ("one-hit wonder" syndrome) — a model evaluated on only a single benchmark where it happened to perform well would leapfrog comprehensively evaluated frontier models that have proven themselves across 3, 4, or 5 rigorous suites.
   
   To enforce statistical confidence, each model's composite score $R_m$ incorporates a Bayesian shrinkage prior $\lambda_{\text{prior}} = 0.6$ (pulling uncertain scores toward the catalog baseline $Z = 0$):
   $$R_m = \frac{\sum_{f \in \mathcal{F}_m} w_f \cdot Z_{m,f}^{\text{calibrated}}}{\sum_{f \in \mathcal{F}_m} w_f + \lambda_{\text{prior}}}$$
   Where $\mathcal{F}_m$ is the set of benchmark suites on which model $m$ has a verified score. This shrinkage smoothly discounts sparse, single-test evaluations while rewarding models that demonstrate sustained, reproducible excellence across diverse testing methodologies.

5. **Competition Ranking:** Models are sorted by descending composite score $R_m$ and assigned standard competition ranks ($1, 2, 2, 4\dots$). Models without any published benchmark evaluations receive `—` and sort to the bottom.

---

### Benchmark Selection Rationale

The catalog spans over 175 models across OpenCode Zen, the Go plan, and OpenRouter. To provide meaningful comparisons across this broad spectrum, the benchmark suite must strike a balance between **modern technical rigor** for frontier models and **wide catalog coverage** across commercial and open-weight models alike.

The five selected benchmarks are:

- **Terminal-Bench 4 (Laude Institute, v4.1 / v4.0 / AA):** Redesigned in late 2026 to evaluate long-horizon agentic reasoning, multi-turn terminal command execution, and live debugging under distribution shifts. Crucially, tasks are engineered to resist data leakage and memorization.
- **DeepSWE (Datacurve):** Contamination-free long-horizon software engineering benchmark testing pass@1 code generation and bug fixes across 113 realistic tasks spanning 91 distinct open-source codebases. Evaluates real-world repo-level comprehension, dependency navigation, and multi-file editing.
- **SWE-bench Pro (Scale AI):** Industry-standard repository problem-solving benchmark (1,865 standardized tasks with human-verified gold patches). Serves as a primary reference point across enterprise coding models.
- **AA Coding Index (Artificial Analysis):** Broad multi-dimensional coding index snapshot combining code generation, code repair, and language proficiency into a standardized composite metric.
- **Terminal-Bench 2 (Laude Institute, v2.1 / v2.0):** Established 89-task CLI benchmark. While partially saturated by frontier models, it offers the highest evaluation density across older, smaller, and open-weight models, acting as a crucial bridge connecting diverse models into the comparison pool.

#### Why Newer Niche Benchmarks Were Excluded

Recent specialized benchmarks (such as Vals Index, KingBench 4, FrontierCode 2.0, or FrontierSWE v2) provide interesting frontier data points but currently only evaluate 10–25 flagship models. Including them would leave 75–85% of the 175-model catalog blank, fragmenting the interface without providing comparative value for the broader catalog. The 5 selected suites represent the optimal intersection of high evaluation rigor and broad cross-model coverage (evaluating 58 to 92 models per suite).

---

### Suite Weighting Rationale

The relative weights assigned to each suite reflect a deliberate trade-off between anti-contamination rigor, task complexity, and measurement reliability:

| Benchmark | Weight | Primary Rationale |
| :--- | :---: | :--- |
| **Terminal-Bench 4** | **1.5×** | **Highest rigor & anti-contamination.** Evaluates multi-turn CLI agent execution in interactive environments. Redesigned specifically to prevent benchmark gaming and memorization. |
| **DeepSWE** | **1.5×** | **Highest real-world repo depth.** 91 distinct repositories ensure test variety without reliance on a single project structure; zero contamination pass@1 evaluation. |
| **SWE-bench Pro** | **1.0×** | **Standard reference baseline.** Essential multi-repo benchmark, but downweighted from 1.5× due to independent audits (e.g. OpenAI's July 2026 study) identifying ~30% task flakiness or broken test environments in the public dataset. |
| **AA Coding Index** | **1.0×** | **Broad multi-skill composite.** Well-calibrated across a wide range of model families, but relies more heavily on curated/synthetic tasks rather than full agentic repository environments. |
| **Terminal-Bench 2** | **0.5×** | **Statistical anchor.** Early-2026 suite with ceiling saturation among frontier models. Retained at 0.5× so it grounds older and open-weight models in the global ranking without distorting the standings of top-tier models. |

---

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
