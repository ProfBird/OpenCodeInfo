# OpenCode Zen & Go — Model Benchmarks & Cost

A small static web page that displays **all OpenCode Zen models** (coding benchmark scores, pricing, context) with sortable columns, SWE-bench Pro, Bug Hunt and FrontierCode 2.0 score columns, filters, and a Go-plan toggle.

**Live page:** <a href="https://profbird.github.io/OpenCodeInfo/" target="_blank">https://profbird.github.io/OpenCodeInfo/</a>

## Files

- `docs/models.json` — Model data: composite benchmark rank (`rank`), AA Coding Index score, SWE-bench Pro score, Bug Hunt score (planted bugs fixed out of 105), FrontierCode 2.0 mergeability score, Terminal-Bench 2 score, Terminal-Bench 4 score, DeepSWE score, USD-per-1M-token pricing (input, output, cached read), `params` (total parameters, e.g. "744B", "1.6T", `null` if undisclosed), `context` window (e.g. "1M", "500K"), a `plan` field (`"go"` for models on the Go $10/mo plan, `"zen"` for a Zen pay-as-you-go row, `"openrouter"` for OpenRouter's programming-category models, which carry OpenRouter's own pricing and are badged (OpenRouter) on the page), `alsoOnZen: true` when a Go-plan model is also available on Zen pay-as-you-go **at the same price** — a model the two plans price differently gets a separate `go` row and `zen` row instead, each showing its own plan's price, and `na: true` when a model is no longer selectable in OpenCode (shown as (N.A.) on the page), for every model in the Zen catalog. Models that leave the catalog are never removed; they stay listed as (N.A.). Each model also has a link (`hfUrl`) to its model card — Hugging Face when weights are open, otherwise BenchLM model specs, or the manufacturer's site.
- `docs/index.html` — The page itself. Loads `models.json` and renders the table. Filtering and sorting all happen in the browser. Published to GitHub Pages via the `docs/` folder.
- `update_zen_prices.py` — Fetches the current OpenCode Zen catalog and pricing, the Go plan, model context/cost data, and SWE-bench Pro / Bug Hunt / FrontierCode 2.0 / Terminal-Bench 2 & 4 / DeepSWE scores, computes transitive rankings, then updates `docs/models.json` (adds models that join the catalog, refreshes prices, maintains the `plan`/`alsoOnZen` flags, splits a model into per-plan rows when Go and Zen price it differently, and flags models that are no longer selectable in OpenCode as `na` — models are never removed).
- `prune_na_models.py` — Removes models that have been flagged `na` (N.A.) for over 6 months (tracked via each model's `naSince` date); `--dry-run` previews, `--months` overrides the cutoff. Run automatically in the daily CI job after the update.
- `.github/workflows/update_models.yml` — Daily GitHub Actions job (03:00 UTC) that runs the update script and commits any changes to `docs/models.json` and `docs/index.html`.

## Usage

1. Start a local server (required because browsers block `fetch` on `file://`):

   ```bash
   cd docs && python3 -m http.server
   ```

2. Open <http://localhost:8000/>.

## Sorting & filtering

- Click the sort button (⇅) next to a column name, or the column header itself, to sort (click again to reverse direction).
- **Plan** filter: show all models, recently added (**New**) models, models available on Zen pay-as-you-go (including Go-plan models also on Zen), **Go Plan** models only, or **OpenRouter** programming-category models (36 verified of OpenRouter's 47; separate rows with OpenRouter's own pricing, badged (OpenRouter)).
- **Available only** checkbox: hide models marked (N.A.) — those no longer selectable in OpenCode's model picker.
- Filter by **Min AA index**, **Min SWE-bench Pro**, **Min Bug Hunt (0–105)**, **Min FrontierCode 2.0**, **Min Terminal-Bench 2**, **Min Terminal-Bench 4**, **Min DeepSWE**, and **Max output price ($/1M)** — same order as the columns.
- **Reset** clears all filters, restores the default column set, and re-sorts by **Rank** (ascending).
- Default view: sorted by **Rank**; AA Coding Index, SWE-bench Pro, Terminal-Bench 2, Input, Cached Read, and Go Limits are hidden until enabled under **choose columns**.
- On narrow screens each model becomes a compact card showing only its name and platform badge; tap the header (or the ▸ button) to expand rank, benchmarks, and output cost.
- Models with no benchmark score (`—`) sort to the bottom when sorting by benchmark.

## Composite Ranking & Benchmark Methodology

The site computes an automatic, objective composite rank across all evaluated models whenever new benchmarks or models are added.

### Ranking Algorithm: Log-Odds Latent Skill with 2-Parameter Mean-Sigma Equating & Conservative Bayesian LCB

Raw percentage scores from different coding benchmarks cannot be directly averaged or compared. Different benchmarks exhibit vastly different difficulty curves, ceiling compression, and score distributions: for example, resolving 67% of tasks on **Terminal-Bench 4** is state-of-the-art frontier performance (#1 in the catalog), whereas 67% on **Terminal-Bench 2** is mid-tier.

Furthermore, naive linear z-scores suffer from three distinct distortions:
1. **Ceiling Compression & Skew:** On older or higher-scoring benchmarks (such as **Terminal-Bench 2** and **AA Coding Index**), frontier models cluster near 80–92% while legacy/lightweight models create a long lower tail, compressing top-tier linear z-scores to $+1.2\sigma$ while newer benchmarks reach $+2.3\sigma$.
2. **Cohort Range Restriction (Location & Scale Bias):** Cutting-edge benchmarks like **Terminal-Bench 4** and **DeepSWE** evaluate narrower, higher-capability frontier cohorts than broad catalog benchmarks. Adjusting only for cohort *mean* (shift-only equating) ignores cohort *variance* restriction and distorts relative slopes across suites.
3. **Symmetric Shrinkage Distortion:** Shrinking sparse models symmetrically toward the catalog mean ($Z = 0$) pulls weak single-suite models *upward* above thoroughly tested mid-tier models.

To provide fair, monotonic, and clone-invariant rankings across the entire catalog, `compute_model_ranks` uses **Log-Odds Latent Skill (Item Response Theory) with 2-Parameter Mean-Sigma Anchored Equating and Conservative Bayesian Lower-Confidence-Bound (LCB) Weighting**:

1. **Canonical Model Deduplication:** Free tiers, Contributor tiers, OpenRouter twins, dated OpenRouter builds of a model already listed under its bare name (`DeepSeek V4 Pro 0813` → `DeepSeek V4 Pro`), and `BENCH_INHERIT_FROM` aliases representing the same underlying model are collapsed into a single canonical identity during calibration and rank numbering (unconfirmed `?` proxy scores are excluded from parameter fitting, and a confirmed value always wins over an uncertain one for the same canonical field), preventing duplicate rows from skewing suite statistics or creating artificial rank gaps.

2. **Log-Odds (IRT Logistic) Transformation:** For each suite $f$, raw percentage pass rates $p_{m,f} \in (0, 100)$ (clamped to $[0.5, 99.5]$) are mapped to log-odds:
   $$\ell_{m,f} = \ln\left(\frac{p_{m,f}}{100 - p_{m,f}}\right)$$
   Under the logistic Item Response Theory link, equal capability gains near benchmark ceilings (e.g. $88\% \to 92\%$) receive appropriate credit relative to mid-range gains ($50\% \to 54\%$). Bug Hunt reports a count (bugs fixed out of 105) rather than a percentage and is converted first: $p = \text{fixed} / 105 \times 100$.

3. **2-Parameter Mean-Sigma Anchored Equating:**
   Using reliability-weighted multi-suite "bridge models" (models evaluated on suite $f$ plus at least one other suite), the pipeline iteratively estimates both suite **location/difficulty** $b_f$ and **scale/discrimination** $a_f$ so that calibrated skill scores match the bridge cohort's leave-one-out latent skill mean and standard deviation on a global $\mathcal{N}(0, 1)$ scale:
   $$a_f = \frac{\sigma_{\ell \mid B_f}}{\sigma_{\hat{\theta}^{(-f)} \mid B_f}}, \qquad b_f = \mu_{\ell \mid B_f} - a_f \mu_{\hat{\theta}^{(-f)} \mid B_f}, \qquad Z_{m,f}^{\text{cal}} = \frac{\ell_{m,f} - b_f}{a_f}$$

   Three guards keep a thin suite from acquiring a degenerate scale: $a_f$ is bounded to $[0.4, 4.0]$ (the live suites fit 0.56–1.90), a suite needs at least 3 bridge models before its scale is re-fit (a 2-point Mean-Sigma fit is exactly determined and swings with either point), and a suite with fewer than 2 confirmed values takes its moments from every score on that suite rather than from an unequated raw log-odds scale. Without them, a suite whose handful of values happen to coincide would divide by $\sigma \approx 0$ and amplify every later score on it tenfold.

4. **Suite Weighting:** Each suite is assigned an explicit importance weight $w_f$ reflecting test recency, evaluation rigor, and resistance to contamination (see [Suite Weighting Rationale](#suite-weighting-rationale) below).

5. **Conservative Bayesian Skill (TrueSkill LCB, $\lambda = 0.35, \kappa = 0.75$):**
   Each model's posterior mean $\mu_m$ and posterior uncertainty $\sigma_m$ are combined into a TrueSkill-style conservative lower confidence bound:
   $$\mu_m = \frac{\sum_{f \in \mathcal{F}_m} w_f \cdot Z_{m,f}^{\text{cal}}}{\sum_{f \in \mathcal{F}_m} w_f + \lambda}, \qquad \sigma_m = \frac{1}{\sqrt{\sum_{f \in \mathcal{F}_m} w_f + \lambda}}, \qquad R_m = \mu_m - \kappa \cdot \sigma_m$$
   Because $-\kappa \sigma_m$ penalizes high uncertainty regardless of sign, sparse single-benchmark models cannot leapfrog proven multi-suite frontier models at the top *or* get pulled artificially upward toward the average in the lower half of the table. Note that $\sigma_m$ depends only on how much suite weight a model has accumulated (its coverage) — a model's dispersion *across* suites does not enter the penalty.

6. **Competition Ranking:** Canonical models are sorted by descending conservative rating $R_m$ and assigned standard competition ranks ($1, 2, 2, 4\dots$). Any row whose benchmark profile materially diverges from its canonical twin (e.g. an older build on OpenRouter) is scored from its own benchmarks against the canonical scale, clamped to the canonical range $1..K$. A rank computed only from unconfirmed, identity-inferred scores carries a trailing `?` (e.g. `#89?`), matching the convention the score cells use. Models without published benchmarks receive `—` and sort to the bottom.

---

### Benchmark Selection Rationale

The catalog spans over 175 models across OpenCode Zen, the Go plan, and OpenRouter. To provide meaningful comparisons across this broad spectrum, the benchmark suite must strike a balance between **modern technical rigor** for frontier models and **wide catalog coverage** across commercial and open-weight models alike.

The seven selected benchmarks are:

- **Terminal-Bench 4 (Laude Institute, v4.1 / v4.0 / AA):** Redesigned in late 2026 to evaluate long-horizon agentic reasoning, multi-turn terminal command execution, and live debugging under distribution shifts. Crucially, tasks are engineered to resist data leakage and memorization.
- **DeepSWE (Datacurve):** Contamination-free long-horizon software engineering benchmark testing pass@1 code generation and bug fixes across 113 realistic tasks spanning 91 distinct open-source codebases. Evaluates real-world repo-level comprehension, dependency navigation, and multi-file editing.
- **SWE-bench Pro (Scale AI):** Industry-standard repository problem-solving benchmark (1,865 standardized tasks with human-verified gold patches). Serves as a primary reference point across enterprise coding models.
- **Bug Hunt (Product Compass):** 2026 blind-graded bug-fixing benchmark: 105 real bugs hidden in two production TypeScript repos (a ~28K-line VS Code extension and a ~60K-line React/Supabase LMS), with each model's patches judged blind. Reports bugs fixed out of 105 and directly measures repository comprehension, debugging, and patch precision rather than from-scratch generation.
- **FrontierCode 2.0 (Cognition):** The first benchmark to score *mergeability* — would the repository's maintainer actually merge this PR? 132 tasks written by the maintainers of the repos they come from, graded by unit tests, rubrics and verifiers across correctness, test quality, scope discipline, style and codebase standards. Kept at 0.5× because its cohort is still sparse and per-model harnesses differ.
- **AA Coding Index (Artificial Analysis):** Broad multi-dimensional coding index snapshot combining code generation, code repair, and language proficiency into a standardized composite metric.
- **Terminal-Bench 2 (Laude Institute, v2.1 / v2.0):** Established 89-task CLI benchmark. While partially saturated by frontier models, it offers the highest evaluation density across older, smaller, and open-weight models, acting as a crucial bridge connecting diverse models into the comparison pool.

#### Why Newer Niche Benchmarks Were Excluded

Recent specialized benchmarks (such as Vals Index, KingBench 4, or FrontierSWE v2) provide interesting frontier data points but currently only evaluate 10–25 flagship models. Including them would leave 75–85% of the 175-model catalog blank, fragmenting the interface without providing comparative value for the broader catalog. The 7 selected suites represent the optimal intersection of high evaluation rigor and broad cross-model coverage (evaluating 67 to 103 models per suite for six of them; FrontierCode 2.0 is the deliberate exception — see below).

**FrontierCode 2.0** is included despite covering only ~28 models because mergeability is the closest published proxy for what a coding agent is actually asked to do (land a change a maintainer accepts). It carries **0.5×** weight — the same as the saturated Terminal-Bench 2 anchor — so its sparse, harness-varying coverage cannot dominate the composite: it nudges models it covers and leaves the rest untouched. Artificial Analysis' independent FrontierCode-AA 2.0 run (55 models, Stirrup harness) is **not** used as a fill source because it diverges materially from the official board on the models both cover (e.g. Kimi K3 17.7 vs 10.9, DeepSeek V4.1 Flash 19.3 vs 28.5).

---

### Suite Weighting Rationale

The relative weights assigned to each suite reflect a deliberate trade-off between anti-contamination rigor, task complexity, and measurement reliability:

| Benchmark | Weight | Primary Rationale |
| :--- | :---: | :--- |
| **Terminal-Bench 4** | **1.5×** | **Highest rigor & anti-contamination.** Evaluates multi-turn CLI agent execution in interactive environments. Redesigned specifically to prevent benchmark gaming and memorization. |
| **DeepSWE** | **1.5×** | **Highest real-world repo depth.** 91 distinct repositories ensure test variety without reliance on a single project structure; zero contamination pass@1 evaluation. |
| **SWE-bench Pro** | **1.0×** | **Standard reference baseline.** Essential multi-repo benchmark, but downweighted from 1.5× due to independent audits (e.g. OpenAI's July 2026 study) identifying ~30% task flakiness or broken test environments in the public dataset. |
| **Bug Hunt** | **1.0×** | **Direct, blind-graded bug fixing.** Independent, uncontaminated 2026 suite that measures real debugging and patch precision, but kept at 1.0× rather than 1.5× because it is a single publisher's board over two TypeScript-only repos and harness/effort vary by entry. |
| **FrontierCode 2.0** | **0.5×** | **Mergeability, sparsely covered.** The only suite that grades whether a change would actually be merged (maintainer-written tasks, rubric + test ensemble), but it covers ~28 models and its per-model runs use different agent harnesses, so it is held at 0.5× to keep it from dominating. |
| **AA Coding Index** | **1.0×** | **Broad multi-skill composite.** Well-calibrated across a wide range of model families, but relies more heavily on curated/synthetic tasks rather than full agentic repository environments. |
| **Terminal-Bench 2** | **0.5×** | **Statistical anchor.** Early-2026 suite with ceiling saturation among frontier models. Retained at 0.5× so it grounds older and open-weight models in the global ranking without distorting the standings of top-tier models. |

---

## Updating the data

```bash
python3 update_zen_prices.py --output docs/models.json  # fetch + update in place
python3 update_zen_prices.py --dry-run --output docs/models.json # preview changes without writing
python3 update_zen_prices.py --no-sync --output docs/models.json # only refresh prices of existing models
python3 update_zen_prices.py --verbose --output docs/models.json # show parsed sources and per-model changes
python3 prune_na_models.py --output docs/models.json    # remove models N.A. for over 6 months
python3 prune_na_models.py --dry-run --output docs/models.json   # preview the prune without writing
```

The GitHub Actions workflow runs the same command on a daily schedule and pushes any changes.

Sources:

- **Catalog** — `https://opencode.ai/zen/v1/models` (all Zen models) and `https://opencode.ai/zen/go/v1/models` (Go plan subset, `plan: "go"`).
- **Pricing** — `https://opencode.ai/docs/zen#pricing` (Zen pay-per-use) and `https://opencode.ai/docs/go` (Go plan pricing table). Go plan pricing wins where a model is on both.
- **Context / cost fallback** — `https://models.dev/api.json` (opencode provider), with verified context overrides in the script.
- **Benchmark (AA)** — AA Coding Index via the BenchLM mirror: `https://benchlm.ai/benchmarks/aacodingindex` (display-only mirror of Artificial Analysis), snapshot 2026-08-21.
- **Benchmark (SWE-bench Pro)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.swePro`), refreshed on every run.
- **Benchmark (Bug Hunt)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding["bug-hunt-bench"]`), with `https://bughunt.productcompass.pm/data/benchmark.json` filling models BenchLM has not imported (publisher values are fallbacks only), refreshed on every run.
- **Benchmark (FrontierCode 2.0)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.frontierCode2`, a mirror of Cognition's official board at `https://cognition.com/frontiercode`), refreshed on every run.
- **Benchmark (Terminal-Bench 2)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.terminalBench21`, fallback `terminalBench2`), refreshed on every run.
- **Benchmark (Terminal-Bench 4)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.terminalBench41` / `agentic.terminalBench41` / `terminalBench4` / `aaTerminalBench4`), refreshed on every run.
- **Benchmark (DeepSWE)** — `https://benchlm.ai/data/models.json` (`benchmarks.coding.deepSwe`), refreshed on every run.

Models that appear in the catalog but aren't priced in either docs table are shown as `Free` until a price is published.
