# OpenCode Zen & Go — Model Benchmarks & Cost

All OpenCode Zen models (pay-as-you-go). Models on the $10/mo **Go** plan are flagged **Go** in the Plan column; the rest are **Zen**-only. On the web page use the **Plan** filter to switch between all Zen models and Go-only.

Costs are per 1M tokens, based on **OpenCode Zen / Go plan** pricing (OpenCode Zen pricing page and Go plan docs; refreshed by `update_zen_prices.py`). Context windows come from the model registry (models.dev) with verified overrides.

Benchmarks:
- **AA Coding Index** — Artificial Analysis coding index, percentage score, snapshot 2026-08-21 via the BenchLM mirror ([benchlm.ai/benchmarks/aacodingindex](https://benchlm.ai/benchmarks/aacodingindex)).
- **SWE-bench Pro** — Scale AI, percentage resolved, via [benchlm.ai/data/models.json](https://benchlm.ai/data/models.json).
- **AA SciCode** — Artificial Analysis research-code benchmark, percentage, via [benchlm.ai/data/models.json](https://benchlm.ai/data/models.json).

## Models

| Model | AA Coding Index | SWE-bench Pro | AA SciCode | Input ($/1M) | Output ($/1M) | Cached Read ($/1M) | Context | Plan |
|---|---|---|---|---|---|---|---|---|
| Big Pickle | — | — | — | Free | Free | Free | 200K | ZEN |
| Claude Fable 5 | 76.49 | 80 | 60.2 | $10 | $50 | $1 | 1M | ZEN |
| Claude Haiku 4.5 | — | — | — | $1 | $5 | $0.1 | 200K | ZEN |
| Claude Opus 4.5 | — | 57.1 | 47 | $5 | $25 | $0.5 | 200K | ZEN |
| Claude Opus 4.6 | — | 53.4 | 45.7 | $5 | $25 | $0.5 | 1M | ZEN |
| Claude Opus 4.7 | 73.6 | — | 50.1 | $5 | $25 | $0.5 | 1M | ZEN |
| Claude Opus 4.8 | 74.25 | 69.2 | 53.5 | $5 | $25 | $0.5 | 1M | ZEN |
| Claude Opus 5 | 77.98 | 79.2 | 55.7 | $5 | $25 | $0.5 | 1M | ZEN |
| Claude Sonnet 4 | — | — | — | $3 | $15 | $0.3 | 1M | ZEN |
| Claude Sonnet 4.5 | — | — | — | $3 | $15 | $0.3 | 1M | ZEN |
| Claude Sonnet 4.6 | — | — | 46.9 | $3 | $15 | $0.3 | 1M | ZEN |
| Claude Sonnet 5 | 71.55 | 63.2 | 53.6 | $2 | $10 | $0.2 | 1M | ZEN |
| DeepSeek V4 Flash | 69.06 | 52.6 | 49.9 | $0.22 | $0.66 | $0.007 | 1M | GO |
| DeepSeek V4 Flash Free | — | — | — | Free | Free | Free | 200K | ZEN |
| DeepSeek V4 Flash Vision Exp | — | — | — | $0.22 | $0.66 | $0.007 | 1M | GO |
| DeepSeek V4 Pro | 68.83 | 55.4 | 49.2 | $0.66 | $1.98 | $0.022 | 1M | GO |
| Gemini 3 Flash | — | — | 49.9 | $0.5 | $3 | $0.05 | 1M | ZEN |
| Gemini 3.1 Pro | 68.83 | — | 58.9 | $2 | $12 | $0.2 | 1M | ZEN |
| Gemini 3.5 Flash | 70.14 | 55.1 | 53.1 | $1.5 | $9 | $0.15 | 1M | ZEN |
| Gemini 3.5 Flash Lite | 49.32 | 54.2 | 40.9 | $0.3 | $2.5 | $0.03 | 1M | ZEN |
| Gemini 3.6 Flash | 69.24 | — | 52.7 | $1.5 | $7.5 | $0.15 | 1M | ZEN |
| Gemini 3.7 Flash | 76.12 | — | 56.8 | $1.5 | $7.5 | $0.15 | 1M | ZEN |
| GLM-5 | — | 55.1 | 46.2 | $1 | $3.2 | $0.2 | 203K | GO |
| GLM-5.1 | 55.78 | 58.4 | 43.8 | $1.4 | $4.4 | $0.26 | 203K | GO |
| GLM-5.2 | 68.76 | 62.1 | 50.5 | $1.4 | $4.4 | $0.26 | 1M | GO |
| GLM-5.3 | 74.76 | — | 56.5 | $1.4 | $4.4 | $0.26 | 1M | GO |
| GPT 5 | — | — | — | $1.07 | $8.5 | $0.107 | 400K | ZEN |
| GPT 5 Codex | — | — | — | $1.07 | $8.5 | $0.107 | 400K | ZEN |
| GPT 5 Nano | — | — | — | $0.05 | $0.4 | $0.005 | 400K | ZEN |
| GPT 5.1 | 49.39 | — | 43.3 | $1.07 | $8.5 | $0.107 | 400K | ZEN |
| GPT 5.1 Codex | — | — | 40.2 | $1.07 | $8.5 | $0.107 | 400K | ZEN |
| GPT 5.1 Codex Max | — | — | 40.2 | $1.25 | $10 | $0.125 | 400K | ZEN |
| GPT 5.1 Codex Mini | — | — | — | $0.25 | $2 | $0.025 | 400K | ZEN |
| GPT 5.2 | — | 55.6 | 52.1 | $1.75 | $14 | $0.175 | 400K | ZEN |
| GPT 5.2 Codex | — | — | 54.6 | $1.75 | $14 | $0.175 | 400K | ZEN |
| GPT 5.3 Codex | — | 56.8 | 53.2 | $1.75 | $14 | $0.175 | 400K | ZEN |
| GPT 5.3 Codex Spark | — | — | — | $1.75 | $14 | $0.175 | 128K | ZEN |
| GPT 5.4 | 71.05 | 57.7 | 56.6 | $2.5 | $15 | $0.25 | 1.05M | ZEN |
| GPT 5.4 Mini | 56.08 | — | 49.9 | $0.75 | $4.5 | $0.075 | 400K | ZEN |
| GPT 5.4 Nano | 56.07 | — | 46.9 | $0.2 | $1.25 | $0.02 | 400K | ZEN |
| GPT 5.4 Pro | — | — | — | $30 | $180 | $30 | 1.05M | ZEN |
| GPT 5.5 | 74.89 | 58.6 | 56.1 | $5 | $30 | $0.5 | 1.05M | ZEN |
| GPT 5.5 Pro | — | — | — | $30 | $180 | $30 | 1.05M | ZEN |
| GPT 5.6 Luna | 71.45 | 62.7 | 52.5 | $0.2 | $1.2 | $0.02 | 1.05M | GO |
| GPT 5.6 Sol | 77.39 | 64.6 | 56.1 | $2 | $10 | $0.2 | 1.05M | ZEN |
| GPT 5.6 Terra | 76.66 | 63.4 | 53.9 | $2 | $12 | $0.2 | 1.05M | ZEN |
| Grok 4.5 | 72.45 | 64.7 | 54.1 | $2 | $6 | $0.3 | 500K | GO |
| Grok 4.6 | 76.79 | — | 53.6 | $2 | $6 | $0.5 | 500K | GO |
| Grok Build 0.1 | — | — | — | $1 | $2 | $0.2 | 256K | ZEN |
| Hy3 | 58.8 | — | 47.6 | $0.14 | $0.58 | $0.035 | 256K | GO |
| Hy3 Free | — | — | — | Free | Free | Free | 190K | ZEN |
| Hy3 Preview | 58.8 | — | 47.6 | Free | Free | Free | 256K | GO |
| Kimi K2.5 | 46.78 | 50.7 | 49 | $0.6 | $3 | $0.1 | 256K | GO |
| Kimi K2.6 | 61.77 | 58.6 | 53.5 | $0.95 | $4 | $0.16 | 262K | GO |
| Kimi K2.7 Code | 60.76 | — | 47.5 | $0.95 | $4 | $0.19 | 262K | GO |
| Kimi K3 | 76.24 | — | 58.7 | $3 | $15 | $0.3 | 1M | GO |
| Laguna S 2.1 Free | — | — | — | Free | Free | Free | 256K | ZEN |
| LongCat-2.0 | — | — | — | $0.3 | $1.2 | $0.006 | 1M | GO |
| MiMo-V2 Omni | — | — | 36.7 | Free | Free | Free | 1M | GO |
| MiMo-V2 Pro | — | — | 42.5 | Free | Free | Free | 1M | GO |
| MiMo-V2.5 | — | 56.1 | — | $0.14 | $0.28 | $0.0028 | 1M | GO |
| MiMo-V2.5 Free | — | — | — | Free | Free | Free | 200K | ZEN |
| MiMo-V2.5-Pro | 60.19 | 57.2 | 50.2 | $0.435 | $0.87 | $0.003625 | 1M | GO |
| MiniMax M2.5 | — | — | — | $0.3 | $1.2 | $0.06 | 200K | GO |
| MiniMax M2.7 | 52.62 | 56.2 | 47 | $0.3 | $1.2 | $0.06 | 205K | GO |
| MiniMax M3 | 58.57 | 59 | 45.4 | $0.3 | $1.2 | $0.06 | 1M | GO |
| Muse Spark 1.2 | 72.22 | — | 56.4 | $1.25 | $4.25 | $0.15 | 1M | ZEN |
| Muse Spark 1.2 Contributor | 72.22 | — | 56.4 | $0.1 | $0.2 | $0.002 | 1M | GO |
| Muse Spark 1.2 Contributor Free | — | — | 56.4 | Free | Free | Free | 1M | ZEN |
| Nemotron 3 Ultra Free | 49.27 | — | — | Free | Free | Free | 1M | ZEN |
| Nemotron 3.5 Lightning Free | 26.76 | — | — | Free | Free | Free | 262K | ZEN |
| Ox Alpha Free | — | — | — | Free | Free | Free | 1M | GO |
| Qwen3.5 Plus | — | — | — | $0.2 | $1.2 | $0.02 | 1M | GO |
| Qwen3.6 Plus | 54.53 | 56.6 | 40.7 | $0.5 | $3 | $0.05 | 1M | GO |
| Qwen3.7 Max | 65.97 | 60.6 | 48.8 | $2.5 | $7.5 | $0.5 | 1M | GO |
| Qwen3.7 Plus | 55.86 | 57.6 | 45.5 | $0.4 | $1.6 | $0.04 | 1M | GO |
| Qwen3.8 Max | 71.81 | — | 52.9 | $2 | $6 | $0.25 | 1M | GO |

## Notes

- **`—`** marks models with no published score on a given benchmark (kept as `—` until a score is published).
- **Variant mapping:** "Muse Spark 1.2 Contributor" is scored under "Muse Spark 1.2" (72.22); "DeepSeek V4 Pro" maps to "DeepSeek V4 Pro 0813" (68.83); "DeepSeek V4 Flash" maps to "DeepSeek V4 Flash 0731" (69.06); "Qwen3.8 Max" is listed as "Qwen3.8 Max Preview" (71.81); "Hy3 Preview" scores under "Hy3 Preview" (58.8).
- **DeepSeek V4 Pro / Flash** use peak/off-peak pricing. Values above are off-peak. Peak hours (01:00–04:00 and 06:00–10:00 UTC): Pro $1.32/$3.96, Flash $0.44/$1.32.
- **Grok 4.5** and **GPT 5.6 Luna/Sol/Terra** have a higher tier for long contexts (> 200K / > 272K tokens); the lower (≤272K / ≤200K) tier is shown.
- **Free models** (Big Pickle, Nemotron, MiMo-V2.5 Free, Hy3 Free, DeepSeek V4 Flash Free, Laguna S 2.1 Free, Ox Alpha Free, Muse Spark 1.2 Contributor Free) are promotional/limited-time.
