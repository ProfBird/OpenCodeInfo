#!/usr/bin/env python3
"""
update_zen_prices.py — Fetch OpenCode Zen catalog, pricing, and Go plan; update models.json

Sources:
  Zen catalog: https://opencode.ai/zen/v1/models            (all pay-as-you-go models)
  Zen pricing: https://opencode.ai/docs/zen#pricing        (table Model/Input/Output/Cached Read)
  Go plan:     https://opencode.ai/zen/go/v1/models        (Go plan subset)
  Go pricing:  https://opencode.ai/docs/go                 (Go plan pricing table)
  Context/cost: https://models.dev/api.json                (opencode provider: context + cost)
  SWE-bench Pro: https://benchlm.ai/data/models.json       (per-model benchmarks.coding.swePro)
  Terminal-Bench: https://benchlm.ai/data/models.json      (per-model benchmarks.coding.terminalBench21 / terminalBench2)
  DeepSWE:       https://benchlm.ai/data/models.json       (per-model benchmarks.coding.deepSwe)

Every model in models.json carries a "plan" field: "go" for models on the Go
$10/mo plan, "zen" for Zen-only models. The web page lets you filter by plan.

Usage:
  python update_zen_prices.py                 # update prices + sync full catalog
  python update_zen_prices.py --dry-run       # show what would change
  python update_zen_prices.py --no-sync       # only update prices of existing models
  python update_zen_prices.py --verbose       # verbose output

Standard library only (urllib, re, html, json, argparse).
"""
import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path
from datetime import date

DEFAULT_ZEN_URL = "https://opencode.ai/docs/zen"
DEFAULT_GO_URL = "https://opencode.ai/docs/go"
DEFAULT_ZEN_API_URL = "https://opencode.ai/zen/v1/models"
DEFAULT_GO_API_URL = "https://opencode.ai/zen/go/v1/models"
DEFAULT_MODELSDEV_URL = "https://models.dev/api.json"
DEFAULT_BENCHLM_URL = "https://benchlm.ai/data/models.json"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_MODELS_PATH = Path(__file__).with_name("models.json")

# Display-name overrides for models where the registry name is awkward.
DISPLAY_NAME = {
    "claude-fable-5": "Claude Fable 5", "claude-opus-5": "Claude Opus 5",
    "claude-opus-4-8": "Claude Opus 4.8", "claude-opus-4-7": "Claude Opus 4.7",
    "claude-opus-4-6": "Claude Opus 4.6", "claude-opus-4-5": "Claude Opus 4.5",
    "claude-sonnet-5": "Claude Sonnet 5", "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "claude-sonnet-4-5": "Claude Sonnet 4.5", "claude-sonnet-4": "Claude Sonnet 4",
    "claude-haiku-4-5": "Claude Haiku 4.5",
    "gemini-3.6-flash": "Gemini 3.6 Flash", "gemini-3.7-flash": "Gemini 3.7 Flash",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash Lite", "gemini-3.5-flash": "Gemini 3.5 Flash",
    "gemini-3.1-pro": "Gemini 3.1 Pro", "gemini-3-flash": "Gemini 3 Flash",
    "gpt-5.6-sol": "GPT 5.6 Sol", "gpt-5.6-terra": "GPT 5.6 Terra",
    "gpt-5.5": "GPT 5.5", "gpt-5.5-pro": "GPT 5.5 Pro",
    "gpt-5.4": "GPT 5.4", "gpt-5.4-pro": "GPT 5.4 Pro",
    "gpt-5.4-mini": "GPT 5.4 Mini", "gpt-5.4-nano": "GPT 5.4 Nano",
    "gpt-5.3-codex-spark": "GPT 5.3 Codex Spark", "gpt-5.3-codex": "GPT 5.3 Codex",
    "gpt-5.2": "GPT 5.2", "gpt-5.2-codex": "GPT 5.2 Codex",
    "gpt-5.1": "GPT 5.1", "gpt-5.1-codex-max": "GPT 5.1 Codex Max",
    "gpt-5.1-codex": "GPT 5.1 Codex", "gpt-5.1-codex-mini": "GPT 5.1 Codex Mini",
    "gpt-5": "GPT 5", "gpt-5-codex": "GPT 5 Codex", "gpt-5-nano": "GPT 5 Nano",
    "grok-build-0.1": "Grok Build 0.1", "grok-4.6": "Grok 4.6",
    "muse-spark-1.2": "Muse Spark 1.2",
    "big-pickle": "Big Pickle", "deepseek-v4-flash-free": "DeepSeek V4 Flash Free",
    "muse-spark-1.2-contributor-free": "Muse Spark 1.2 Contributor Free",
    "mimo-v2.5-free": "MiMo-V2.5 Free", "hy3-free": "Hy3 Free",
    "nemotron-3-ultra-free": "Nemotron 3 Ultra Free",
    "nemotron-3.5-lightning-free": "Nemotron 3.5 Lightning Free",
    "laguna-s-2.1-free": "Laguna S 2.1 Free",
    "ling-3.0-flash-fin-free": "Ling 3.0 Flash Fin Free",
    "gpt-5.6-luna": "GPT 5.6 Luna", "grok-4.5": "Grok 4.5",
    "deepseek-v4-pro": "DeepSeek V4 Pro", "deepseek-v4-flash": "DeepSeek V4 Flash",
    "deepseek-v4-flash-vision-exp": "DeepSeek V4 Flash Vision Exp",
    "glm-5.3-flash": "GLM-5.3-Flash", "glm-5.3": "GLM-5.3", "glm-5.2": "GLM-5.2", "glm-5.1": "GLM-5.1", "glm-5": "GLM-5",
    "minimax-m3": "MiniMax M3", "minimax-m2.7": "MiniMax M2.7", "minimax-m2.5": "MiniMax M2.5",
    "kimi-k3": "Kimi K3", "kimi-k2.7-code": "Kimi K2.7 Code", "kimi-k2.6": "Kimi K2.6",
    "kimi-k2.5": "Kimi K2.5", "qwen3.6-plus": "Qwen3.6 Plus", "qwen3.5-plus": "Qwen3.5 Plus",
    "qwen3.7-max": "Qwen3.7 Max", "qwen3.7-plus": "Qwen3.7 Plus", "qwen3.8-max": "Qwen3.8 Max", "qwen3.8-flash": "Qwen3.8 Flash",
    "mimo-v2-pro": "MiMo-V2 Pro", "mimo-v2-omni": "MiMo-V2 Omni",
    "mimo-v2.5-pro": "MiMo-V2.5-Pro", "mimo-v2.5": "MiMo-V2.5",
    "hy3": "Hy3", "hy3-preview": "Hy3 Preview",
    "muse-spark-1.2-contributor": "Muse Spark 1.2 Contributor",
    "ox-alpha-free": "Ox Alpha Free", "x-preview-f-free": "Ox Alpha Free",
    "longcat-2.0": "LongCat-2.0",
}

# Known model-card links (HF if a card exists, else BenchLM specs, else manufacturer).
KNOWN_URLS = {
    # open weights -> Hugging Face
    "deepseek-v4-flash": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash",
    "deepseek-v4-flash-vision-exp": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash",
    "deepseek-v4-pro": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro",
    "glm-5": "https://huggingface.co/zai-org/GLM-5",
    "glm-5.1": "https://huggingface.co/zai-org/GLM-5.1",
    "glm-5.2": "https://huggingface.co/zai-org/GLM-5.2",
    "glm-5.3-flash": "https://huggingface.co/zai-org/GLM-5.3-Flash",
    "kimi-k2.5": "https://huggingface.co/moonshotai/Kimi-K2.5",
    "kimi-k2.6": "https://huggingface.co/moonshotai/Kimi-K2.6",
    "kimi-k2.7-code": "https://huggingface.co/moonshotai/Kimi-K2.7-Code",
    "kimi-k3": "https://huggingface.co/moonshotai/Kimi-K3",
    "longcat-2.0": "https://huggingface.co/meituan-longcat/LongCat-2.0",
    "minimax-m2.5": "https://huggingface.co/MiniMaxAI/MiniMax-M2.5",
    "minimax-m2.7": "https://huggingface.co/MiniMaxAI/MiniMax-M2.7",
    "minimax-m3": "https://huggingface.co/MiniMaxAI/MiniMax-M3",
    "mimo-v2.5": "https://huggingface.co/XiaomiMiMo/MiMo-V2.5",
    "mimo-v2.5-pro": "https://huggingface.co/XiaomiMiMo/MiMo-V2.5-Pro",
    "hy3": "https://huggingface.co/tencent/HY3",
    "hy3-preview": "https://huggingface.co/tencent/HY3-Preview",
    "qwen3.6-plus": "https://huggingface.co/Qwen/Qwen3.6-27B",
    "qwen3.8-max": "https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B",
    "qwen3.8-flash": "https://huggingface.co/Qwen/Qwen3.8-Flash-Next",
    "laguna-s-2.1-free": "https://huggingface.co/poolside/Laguna-S-2.1",
    # free variants -> same model card
    "deepseek-v4-flash-free": "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash",
    "mimo-v2.5-free": "https://huggingface.co/XiaomiMiMo/MiMo-V2.5",
    "hy3-free": "https://huggingface.co/tencent/HY3",
    # proprietary/closed -> manufacturer page
    "grok-4.5": "https://docs.x.ai/developers/models/grok-4.5",
    "glm-5.3": "https://docs.z.ai/guides/llm/glm-5.3",
    "gpt-5.6-luna": "https://developers.openai.com/api/docs/models/gpt-5.6-luna",
    "gpt-5": "https://developers.openai.com/api/docs/models",
    "gpt-5-codex": "https://developers.openai.com/api/docs/models",
    "gpt-5.1-codex-mini": "https://developers.openai.com/api/docs/models",
    "muse-spark-1.2-contributor": "https://developer.meta.com/ai/models/muse-spark/",
    "muse-spark-1.2-contributor-free": "https://developer.meta.com/ai/models/muse-spark/",
    "qwen3.7-max": "https://qwen.ai/blog?id=qwen3.7",
    "qwen3.7-plus": "https://qwen.ai/blog?id=qwen3.7-plus",
    "qwen3.5-plus": "https://qwen.ai/blog?id=qwen3.5-plus",
    "mimo-v2-pro": "https://mimo.xiaomi.com/mimo-v2-pro",
    "mimo-v2-omni": "https://mimo.xiaomi.com/mimo-v2-omni",
    "ox-alpha-free": "https://openrouter.ai/stealth/ox-alpha",
    "claude-sonnet-4": "https://www.anthropic.com/claude",
    "big-pickle": "https://opencode.ai/docs/zen",
    # closed models -> BenchLM specs
    "claude-fable-5": "https://benchlm.ai/models/claude-fable-5",
    "claude-opus-5": "https://benchlm.ai/models/claude-opus-5",
    "claude-opus-4-8": "https://benchlm.ai/models/claude-opus-4-8",
    "claude-opus-4-7": "https://benchlm.ai/models/claude-opus-4-7",
    "claude-opus-4-6": "https://benchlm.ai/models/claude-opus-4-6",
    "claude-opus-4-5": "https://benchlm.ai/models/claude-opus-4-5",
    "claude-sonnet-5": "https://benchlm.ai/models/claude-sonnet-5",
    "claude-sonnet-4-6": "https://benchlm.ai/models/claude-sonnet-4-6",
    "claude-sonnet-4-5": "https://benchlm.ai/models/claude-sonnet-4-5",
    "claude-haiku-4-5": "https://benchlm.ai/models/claude-haiku-4-5",
    "gemini-3.7-flash": "https://benchlm.ai/models/gemini-3.7-flash",
    "gemini-3.6-flash": "https://benchlm.ai/models/gemini-3-6-flash",
    "gemini-3.5-flash": "https://benchlm.ai/models/gemini-3-5-flash",
    "gemini-3.5-flash-lite": "https://benchlm.ai/models/gemini-3.5-flash-lite",
    "gemini-3.1-pro": "https://benchlm.ai/models/gemini-3-1-pro",
    "gemini-3-flash": "https://benchlm.ai/models/gemini-3-flash",
    "gpt-5.6-sol": "https://benchlm.ai/models/gpt-5.6-sol",
    "gpt-5.6-terra": "https://benchlm.ai/models/gpt-5.6-terra",
    "gpt-5.5": "https://benchlm.ai/models/gpt-5.5",
    "gpt-5.5-pro": "https://benchlm.ai/models/gpt-5.5-pro",
    "gpt-5.4": "https://benchlm.ai/models/gpt-5.4",
    "gpt-5.4-pro": "https://benchlm.ai/models/gpt-5.4-pro",
    "gpt-5.4-mini": "https://benchlm.ai/models/gpt-5.4-mini",
    "gpt-5.4-nano": "https://benchlm.ai/models/gpt-5.4-nano",
    "gpt-5.3-codex": "https://benchlm.ai/models/gpt-5.3-codex",
    "gpt-5.3-codex-spark": "https://benchlm.ai/models/gpt-5.3-codex-spark",
    "gpt-5.2": "https://benchlm.ai/models/gpt-5.2",
    "gpt-5.2-codex": "https://benchlm.ai/models/gpt-5.2-codex",
    "gpt-5.1": "https://benchlm.ai/models/gpt-5.1",
    "gpt-5.1-codex": "https://benchlm.ai/models/gpt-5.1-codex",
    "gpt-5.1-codex-max": "https://benchlm.ai/models/gpt-5.1-codex-max",
    "gpt-5-nano": "https://benchlm.ai/models/gpt-5-nano",
    "grok-4.6": "https://benchlm.ai/models/grok-4.6",
    "grok-build-0.1": "https://benchlm.ai/models/grok-build-0.1",
    "muse-spark-1.2": "https://benchlm.ai/models/muse-spark-1-2",
    "nemotron-3-ultra-free": "https://benchlm.ai/models/nemotron-3-ultra",
    "nemotron-3.5-lightning-free": "https://benchlm.ai/models/nemotron-3-5-lightning-30b-a3b-nvfp4",
    # Ling 3.0 Flash Fin: finance fine-tune; weights not on HF yet (API-only launch
    # 2026-08-27) -> BenchLM spec profile per the fallback chain.
    "ling-3.0-flash-fin-free": "https://benchlm.ai/models/ling-3-0-flash-fin",
}

# OpenCode model name -> BenchLM slug for SWE-bench Pro lookups where the
# display name doesn't map cleanly to the BenchLM model slug.
BENCH_SLUG_OVERRIDES = {
    "Claude Fable 5": "claude-fable",
    "DeepSeek V4 Flash": "deepseek-v4-flash-0731",
    "DeepSeek V4 Pro": "deepseek-v4-pro-0813",
    "Muse Spark 1.2": "muse-spark-1-2",
    "Muse Spark 1.2 Contributor": "muse-spark-1-2",
    "Muse Spark 1.2 Contributor Free": "muse-spark-1-2",
    "MiMo-V2 Omni": "mimo-v2-omni",
    "MiMo-V2 Pro": "mimo-v2-pro",
    "MiMo-V2.5": "mimo-v2-5",
    "MiMo-V2.5-Pro": "mimo-v2-5-pro",
    "Qwen3.5 Plus": "qwen3-5-plus",
    "Qwen3.6 Plus": "qwen3-6-plus",
    "Qwen3.8 Max": "qwen3-8-max-preview",
    "Qwen3.8 Flash": "qwen3-8-flash-next",
    "LongCat-2.0": "longcat-2-0",
    "Grok Build 0.1": "grok-build-0-1",
    "MiniMax M2.5": "minimax-m2-5",
    "GLM-5.3-Flash": "glm-5-3-flash",
    "GLM-5.3": "glm-5-3",
    "Laguna S 2.1 Free": "laguna-s-2-1",
    "Nemotron 3 Ultra Free": "nemotron-3-ultra",
    "Nemotron 3.5 Lightning Free": "nemotron-3-5-lightning-30b-a3b-nvfp4",
    "Gemini 3.5 Flash Lite": "gemini-3-5-flash-lite",
    "GPT 5.6 Sol": "gpt-5-6-sol",
    "GPT 5.6 Terra": "gpt-5-6-terra",
    "GPT 5.6 Luna": "gpt-5-6-luna",
}

def normalize(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (name or '').lower())

def id_from_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'[^a-z0-9.-]', '', s)
    s = re.sub(r'-+', '-', s)
    return s

def display_from_id(model_id: str) -> str:
    if model_id in DISPLAY_NAME:
        return DISPLAY_NAME[model_id]
    parts = model_id.split("-")
    out = []
    for p in parts:
        if re.match(r'^\d', p):
            out.append(p.upper() if len(p) <= 2 else p)
        elif p in ("v2", "v4"):
            out.append(p.upper())
        else:
            out.append(p.capitalize())
    return " ".join(out).replace("Mimo", "MiMo")

def parse_price(s: str):
    s = s.strip()
    if s.lower() == "free":
        return 0
    if s in ("-", "—", ""):
        return None
    s = s.replace("$", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None

def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (update_zen_prices.py)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")

def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (update_zen_prices.py)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def strip_tags(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()

def extract_pricing_table(html_text: str, is_go: bool = False):
    """Parse pricing table. Zen: 5 cols, Go: 6 cols (with Usage)."""
    if is_go:
        m = re.search(
            r'<table><thead><tr><th>Model</th><th>Input</th><th>Output</th><th>Cached Read</th><th>Cached Write</th><th>Usage</th></tr></thead><tbody>(.*?)</tbody></table>',
            html_text, re.DOTALL)
        if not m:
            m = re.search(r'<th>Model</th>.*?<th>Usage</th>.*?<tbody>(.*?)</tbody>', html_text, re.DOTALL)
            if not m:
                raise ValueError("Go pricing table not found")
        tbody = m.group(1)
        rows = re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>', tbody, re.DOTALL)
    else:
        m = re.search(
            r'<table><thead><tr><th>Model</th><th>Input</th><th>Output</th><th>Cached Read</th><th>Cached Write</th></tr></thead><tbody>(.*?)</tbody></table>',
            html_text, re.DOTALL)
        if not m:
            m = re.search(r'<th>Model</th>.*?<th>Cached Read</th>.*?<tbody>(.*?)</tbody>', html_text, re.DOTALL)
            if not m:
                raise ValueError("Zen pricing table not found")
        tbody = m.group(1)
        rows = re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>', tbody, re.DOTALL)

    pricing = {}
    for row in rows:
        model = strip_tags(row[0])
        base = model.split("(")[0].strip()
        if not model:
            continue
        if ("Peak" in model and "Off-Peak" not in model) or "> 2" in model:
            continue
        pricing[normalize(base)] = (parse_price(row[1]), parse_price(row[2]), parse_price(row[3]))
    return pricing

def fmt_ctx(n):
    if not n:
        return "1M"
    if n >= 1000000:
        m = n / 1000000
        if abs(m - round(m)) < 0.001 or n == 1048576:
            return f"{round(m)}M"
        return f"{m:.2f}".rstrip('0').rstrip('.') + "M"
    return f"{round(n / 1000)}K"

# Verified context overrides (authoritative), take precedence over models.dev.
CONTEXT_OVERRIDES = {
    "glm-5": "203K", "glm-5.1": "203K", "glm-5.2": "1M", "glm-5.3": "1M", "glm-5.3-flash": "1M",
    "hy3": "256K", "hy3-preview": "256K",
    "kimi-k2.5": "256K", "kimi-k2.6": "262K", "kimi-k2.7-code": "262K", "kimi-k3": "1M",
    "minimax-m2.5": "200K", "minimax-m2.7": "205K", "minimax-m3": "1M",
    "qwen3.5-plus": "1M", "qwen3.6-plus": "1M", "qwen3.7-max": "1M",
    "qwen3.7-plus": "1M", "qwen3.8-max": "1M", "qwen3.8-flash": "1M",
    "longcat-2.0": "1M", "mimo-v2.5": "1M", "mimo-v2.5-pro": "1M",
    "mimo-v2-pro": "1M", "mimo-v2-omni": "1M",
    "muse-spark-1.2-contributor": "1M", "ox-alpha-free": "1M",
    "deepseek-v4-flash-vision-exp": "1M",
    "ling-3.0-flash-fin-free": "262K",
    "gpt-5.6-luna": "1.05M", "grok-4.5": "500K",
    "deepseek-v4-pro": "1M", "deepseek-v4-flash": "1M",
}

# Verified parameter count overrides (total parameters). Values are display strings (e.g. "744B", "1.6T").
# Sources: official model cards / HF repos. MoE models list total params (active params in docs).
# GPT/Claude/Gemini/Grok families: vendors do not disclose; estimates from independent analyses
# — GPT: cbowdon.github.io/posts/gpt-params (635B/18B regression) + cometapi.com 2-5T
# — Claude: Musk leak via eu.36kr.com p376067 / unexcitedneurons throughput 1.5-2T (Sonnet 1T / Opus 5T / Fable 10T)
# — Gemini: industry estimates (MLJourney Gemini Ultra ~100B+, Pro ~60-100B, Flash ~20-40B scaled to Gemini3)
# — Grok: datastudios.org Grok4 1.7T, 36kr Grok4.2 0.5T, Grok5 6T — treated as best-effort.
PARAM_OVERRIDES = {
    "deepseek-v4-flash": "284B",
    "deepseek-v4-flash-free": "284B",
    "deepseek-v4-flash-vision-exp": "284B",
    "deepseek-v4-pro": "1.6T",
    "glm-5": "744B",
    "glm-5.1": "744B",
    "glm-5.2": "744B",
    "glm-5.3": "744B",
    "glm-5.3-flash": "320B",
    "kimi-k2.5": "1T",
    "kimi-k2.6": "1T",
    "kimi-k2.7-code": "1T",
    "kimi-k3": "2.8T",
    "longcat-2.0": "1.6T",
    "mimo-v2.5": "310B",
    "mimo-v2.5-free": "310B",
    "ling-3.0-flash-fin-free": "124B",  # finance fine-tune of Ling 3.0 Flash, retains its 124B-total / 5.1B-active MoE (InclusionAI launch notes via BenchLM/Benchable)
    "mimo-v2.5-pro": "1.02T",
    "mimo-v2-pro": "1T",
    "mimo-v2-omni": "1T",
    "hy3": "295B",
    "hy3-preview": "295B",
    "hy3-free": "295B",
    "laguna-s-2.1-free": "118B",
    "minimax-m2.5": "230B",
    "minimax-m2.7": "230B",
    "minimax-m3": "428B",
    "qwen3.5-plus": "397B",
    "qwen3.6-plus": "27B",
    "qwen3.7-max": "1T",
    "qwen3.7-plus": "1T",
    "qwen3.8-max": "2.4T",
    "qwen3.8-flash": "125B",
    "muse-spark-1.2": "405B",
    "muse-spark-1.2-contributor": "405B",
    "muse-spark-1.2-contributor-free": "405B",
    "nemotron-3-ultra-free": "550B",
    "nemotron-3.5-lightning-free": "30B",
    "gpt-5": "635B",
    "gpt-5-codex": "635B",
    "gpt-5-nano": "18B",
    "gpt-5.1": "635B",
    "gpt-5.1-codex": "635B",
    "gpt-5.1-codex-max": "800B",
    "gpt-5.1-codex-mini": "30B",
    "gpt-5.2": "635B",
    "gpt-5.2-codex": "635B",
    "gpt-5.3-codex": "635B",
    "gpt-5.3-codex-spark": "300B",
    "gpt-5.4": "635B",
    "gpt-5.4-mini": "85B",
    "gpt-5.4-nano": "18B",
    "gpt-5.4-pro": "1.2T",
    "gpt-5.5": "635B",
    "gpt-5.5-pro": "1.2T",
    "gpt-5.6-luna": "85B",
    "gpt-5.6-sol": "635B",
    "gpt-5.6-terra": "635B",
    "claude-fable-5": "10T",
    "claude-opus-5": "5T",
    "claude-opus-4-8": "2T",
    "claude-opus-4-7": "2T",
    "claude-opus-4-6": "1.5T",
    "claude-opus-4-5": "1.5T",
    "claude-sonnet-5": "1T",
    "claude-sonnet-4-6": "1T",
    "claude-sonnet-4-5": "1T",
    "claude-sonnet-4": "1T",
    "claude-haiku-4-5": "100B",
    "gemini-3-flash": "400B",
    "gemini-3.1-pro": "1T",
    "gemini-3.5-flash": "400B",
    "gemini-3.5-flash-lite": "100B",
    "gemini-3.6-flash": "500B",
    "gemini-3.7-flash": "600B",
    "grok-4.5": "1.7T",
    "grok-4.6": "1.7T",
    "grok-build-0.1": "500B",
    "big-pickle": "357B?",  # inferred from the (unconfirmed) GLM-4.6 identification
    "ox-alpha-free": "500B",
    # Below are best-effort or undisclosed; null means unknown (rendered as —)
}

# OpenRouter programming-category models. The UI's Programming category
# (https://openrouter.ai/models?categories=programming, 47 models) is computed
# client-side; OPENROUTER_DISPLAY lists the verified subset (31 rendered from the
# filtered UI + 5 from the API's narrower ?category=programming list). Each gets
# its own row named "<Display> (OpenRouter)" because OpenRouter's pricing and
# context can differ from the Zen/Go twins. Params mirror the Zen/Go twins.
OPENROUTER_DISPLAY = {
    "anthropic/claude-opus-5": "Claude Opus 5",
    "anthropic/claude-sonnet-5": "Claude Sonnet 5",
    "anthropic/claude-fable-5": "Claude Fable 5",
    "deepseek/deepseek-v4-flash": "DeepSeek V4 Flash",
    "deepseek/deepseek-v4-flash-0731": "DeepSeek V4 Flash 0731",
    "deepseek/deepseek-v4-flash-vision-exp": "DeepSeek V4 Flash Vision Exp",
    "deepseek/deepseek-v4-pro": "DeepSeek V4 Pro",
    "deepseek/deepseek-v4-pro-0813": "DeepSeek V4 Pro 0813",
    "google/gemini-3.6-flash": "Gemini 3.6 Flash",
    "google/gemini-3.7-flash": "Gemini 3.7 Flash",
    "meta/muse-spark-1.2-contributor": "Muse Spark 1.2 Contributor",
    "minimax/minimax-m3": "MiniMax M3",
    "minimax/minimax-m3:free": "MiniMax M3 Free",
    "moonshotai/kimi-k2.7-code": "Kimi K2.7 Code",
    "moonshotai/kimi-k3": "Kimi K3",
    "nvidia/nemotron-3-ultra-550b-a55b:free": "Nemotron 3 Ultra Free",
    "nvidia/nemotron-3.5-lightning:free": "Nemotron 3.5 Lightning Free",
    "openai/gpt-5.6-luna": "GPT 5.6 Luna",
    "openai/gpt-5.6-luna-pro": "GPT 5.6 Luna Pro",
    "openai/gpt-5.6-sol": "GPT 5.6 Sol",
    "openai/gpt-5.6-terra": "GPT 5.6 Terra",
    "poolside/laguna-s-2.1:free": "Laguna S 2.1 Free",
    "qwen/qwen3.7-flash": "Qwen3.7 Flash",
    "qwen/qwen3.8-27b": "Qwen3.8 27B",
    "qwen/qwen3.8-flash": "Qwen3.8 Flash",
    "qwen/qwen3.8-max": "Qwen3.8 Max",
    "thinkingmachines/inkling:free": "Inkling Free",
    "tencent/hy3": "Hy3",
    "tencent/hy4-preview": "Hy4 Preview",
    "upstage/solar-pro4": "Solar Pro 4",
    "xiaomi/mimo-v2.5": "MiMo-V2.5",
    "x-ai/grok-4.5": "Grok 4.5",
    "x-ai/grok-4.6": "Grok 4.6",
    "z-ai/glm-5.2": "GLM-5.2",
    "z-ai/glm-5.3": "GLM-5.3",
    "z-ai/glm-5.3-flash": "GLM-5.3-Flash",
}

OPENROUTER_PARAMS = {
    "anthropic/claude-opus-5": "5T",
    "anthropic/claude-sonnet-5": "1T",
    "anthropic/claude-fable-5": "10T",
    "deepseek/deepseek-v4-flash": "284B",
    "deepseek/deepseek-v4-flash-0731": "284B",
    "deepseek/deepseek-v4-flash-vision-exp": "284B",
    "deepseek/deepseek-v4-pro": "1.6T",
    "deepseek/deepseek-v4-pro-0813": "1.6T",
    "google/gemini-3.6-flash": "500B",
    "google/gemini-3.7-flash": "600B",
    "meta/muse-spark-1.2-contributor": "405B",
    "minimax/minimax-m3": "428B",
    "minimax/minimax-m3:free": "428B",
    "moonshotai/kimi-k2.7-code": "1T",
    "moonshotai/kimi-k3": "2.8T",
    "nvidia/nemotron-3-ultra-550b-a55b:free": "550B",
    "nvidia/nemotron-3.5-lightning:free": "30B",
    "openai/gpt-5.6-luna": "85B",
    "openai/gpt-5.6-sol": "635B",
    "openai/gpt-5.6-terra": "635B",
    "poolside/laguna-s-2.1:free": "118B",
    "qwen/qwen3.8-27b": "27B",
    "qwen/qwen3.8-flash": "125B",
    "qwen/qwen3.8-max": "2.4T",
    "tencent/hy3": "295B",
    "xiaomi/mimo-v2.5": "310B",
    "x-ai/grok-4.5": "1.7T",
    "x-ai/grok-4.6": "1.7T",
    "z-ai/glm-5.2": "744B",
    "z-ai/glm-5.3": "744B",
    "z-ai/glm-5.3-flash": "320B",
}

# AA Coding Index for OpenRouter programming rows, from OpenRouter's benchmarks
# API (https://openrouter.ai/api/v1/benchmarks, source "artificial-analysis",
# matched permaslug = model id + build date). That endpoint requires auth, so
# these are applied as a curated snapshot rather than fetched by daily runs.
# Models without a published AA coding index (Hy3, Hy4 Preview, Claude Fable 5,
# DeepSeek V4 Flash Vision Exp, Muse Spark 1.2 Contributor, GPT 5.6 Luna Pro,
# Laguna S 2.1, Qwen3.7 Flash, Qwen3.8 Flash) stay null.
OPENROUTER_CODING_INDEX = {
    "anthropic/claude-opus-5": 78,
    "anthropic/claude-sonnet-5": 71.5,
    "deepseek/deepseek-v4-flash": 56.2,
    "deepseek/deepseek-v4-flash-0731": 69.1,
    "deepseek/deepseek-v4-pro": 59.4,
    "deepseek/deepseek-v4-pro-0813": 68.8,
    "google/gemini-3.6-flash": 69.2,
    "google/gemini-3.7-flash": 76.1,
    "minimax/minimax-m3": 58.6,
    "minimax/minimax-m3:free": 58.6,
    "moonshotai/kimi-k2.7-code": 60.8,
    "moonshotai/kimi-k3": 76.2,
    "nvidia/nemotron-3-ultra-550b-a55b:free": 49.3,
    "nvidia/nemotron-3.5-lightning:free": 26.8,
    "openai/gpt-5.6-luna": 71.4,
    "openai/gpt-5.6-sol": 77.4,
    "openai/gpt-5.6-terra": 76.7,
    "qwen/qwen3.8-27b": 68.1,
    "qwen/qwen3.8-max": 71.8,
    "thinkingmachines/inkling:free": 52.1,
    "upstage/solar-pro4": 52.7,
    "x-ai/grok-4.5": 72.4,
    "x-ai/grok-4.6": 76.8,
    "xiaomi/mimo-v2.5": 56.8,
    "z-ai/glm-5.2": 68.8,
    "z-ai/glm-5.3": 74.8,
    "z-ai/glm-5.3-flash": 71.5,
}

def or_display_name(or_id, or_name):
    base = OPENROUTER_DISPLAY.get(or_id)
    if base is None:
        base = or_name.split(": ", 1)[-1]  # strip "Vendor: " prefix
    return f"{base} (OpenRouter)"

def sync_openrouter(models, or_models, dry_run=False):
    """Add/update rows for OpenRouter's programming-category models (plan 'openrouter').

    Pricing/context come from OpenRouter's catalog and can differ from the same
    model's Zen/Go pricing, so every OpenRouter model gets its own row named
    '<Display> (OpenRouter)'. Rows are never removed (same retention policy).
    """
    by_name = {}
    for m in models:
        by_name[normalize(m["name"])] = m
    added = []
    changed = []
    for om in or_models:
        oid = om.get("id", "")
        if oid not in OPENROUTER_DISPLAY:
            continue  # only curated Programming-category models get rows
        name = or_display_name(oid, om.get("name") or oid)
        price = om.get("pricing", {}) or {}
        def per_million(v):
            try:
                return round(float(v) * 1_000_000, 6)
            except (TypeError, ValueError):
                return 0
        row_data = {
            "params": OPENROUTER_PARAMS.get(oid),
            "context": fmt_ctx(om.get("context_length")),
            "inputCost": per_million(price.get("prompt")),
            "outputCost": per_million(price.get("completion")),
            "cachedReadCost": per_million(price.get("input_cache_read")),
            "plan": "openrouter",
            "codingIndex": OPENROUTER_CODING_INDEX.get(oid),
        }
        hf = om.get("hugging_face_id")
        new_url = f"https://huggingface.co/{hf}" if hf else f"https://openrouter.ai/{oid.split(':')[0]}"
        row_data["hfUrl"] = new_url
        existing = by_name.get(normalize(name))
        if existing is None:
            row = {"name": name, "codingIndex": None, "swePro": None,
                   "terminalBench": None, "deepSwe": None}
            row.update(row_data)
            added.append((name, oid))
            if not dry_run:
                models.append(row)
                by_name[normalize(name)] = row
        else:
            updates = {}
            for k, v in row_data.items():
                if v is None:
                    continue
                if existing.get(k) != v:
                    updates[k] = v
            if updates:
                changed.append((name, updates))
                if not dry_run:
                    for k, v in updates.items():
                        existing[k] = v
    if not dry_run:
        models.sort(key=lambda x: x["name"].lower())
    return added, changed

def build_desired(zen_ids, go_ids, md, mdgo=None):
    """Return dict id -> row data for the full union of Zen + Go models."""
    go_set = set(go_ids)
    zen_set = set(zen_ids)
    desired = {}
    for i in list(zen_ids) + list(go_ids):
        if i in desired:
            continue
        if i == "x-preview-f-free" and "ox-alpha-free" in go_set:
            continue  # same model as Go Ox Alpha Free
        nid = normalize(i)
        m = md.get(i, {}) or md.get(nid, {})
        cost = m.get("cost", {})
        plan = "go" if i in go_set else "zen"
        price = None
        # pricing handled later by the caller via tables; here just defaults
        desired[i] = {
            "id": i,
            "name": DISPLAY_NAME.get(i, m.get("name") or display_from_id(i)),
            "plan": plan,
            "alsoOnZen": plan == "go" and i in zen_set,
            "inputCost": cost.get("input"),
            "outputCost": cost.get("output"),
            "cachedReadCost": cost.get("cache_read"),
            "context": CONTEXT_OVERRIDES.get(i) or fmt_ctx((m.get("limit") or {}).get("context")),
            "params": PARAM_OVERRIDES.get(i) or PARAM_OVERRIDES.get(nid),
        }
    return desired

def reconcile(data, desired, zen_pricing, go_pricing, md, dry_run=False):
    """Add/update models to match the desired catalog.

    Models that leave the catalog are NEVER removed — they stay listed and
    get flagged `na` (Not Available) by apply_na_flags (see main()).
    """
    models = data.setdefault("models", [])
    by_id = {}
    for m in models:
        by_id[normalize(id_from_name(m["name"]))] = m
        by_id[normalize(m["name"])] = m

    added = []
    changed = []

    # Update existing + add new
    for i, d in desired.items():
        nid = normalize(i)
        disp_norm = normalize(d["name"])
        existing = by_id.get(nid) or by_id.get(disp_norm)
        # Determine price: go table preferred for go models, else zen table
        price = None
        if d["plan"] == "go":
            price = go_pricing.get(nid) or go_pricing.get(disp_norm) or zen_pricing.get(nid) or zen_pricing.get(disp_norm)
        else:
            price = zen_pricing.get(nid) or zen_pricing.get(disp_norm)
        if not price:
            price = None

        if existing is None:
            row = {
                "name": d["name"],
                "codingIndex": None,
                "inputCost": price[0] if price else d["inputCost"],
                "outputCost": price[1] if price else d["outputCost"],
                "cachedReadCost": price[2] if price else d["cachedReadCost"],
                "context": d["context"],
                "params": d.get("params"),
                "plan": d["plan"],
            }
            if d.get("alsoOnZen"):
                row["alsoOnZen"] = True
            if i in KNOWN_URLS:
                row["hfUrl"] = KNOWN_URLS[i]
            # null price -> treat as Free
            if row["inputCost"] is None: row["inputCost"] = 0
            if row["outputCost"] is None: row["outputCost"] = 0
            if row["cachedReadCost"] is None: row["cachedReadCost"] = 0
            added.append((d["name"], i))
            if not dry_run:
                models.append(row)
        else:
            updates = {}
            # plan
            if existing.get("plan") != d["plan"]:
                updates["plan"] = d["plan"]
            # alsoOnZen (Go-plan model also available on Zen pay-as-you-go)
            want_zen = bool(d.get("alsoOnZen"))
            has_zen = bool(existing.get("alsoOnZen"))
            if want_zen != has_zen:
                updates["alsoOnZen"] = want_zen
            # hfUrl (maintain for existing rows when a known URL exists; never auto-clear)
            if i in KNOWN_URLS and existing.get("hfUrl") != KNOWN_URLS[i]:
                updates["hfUrl"] = KNOWN_URLS[i]
            # context (only update if we have a real value)
            if d["context"] and existing.get("context") != d["context"]:
                updates["context"] = d["context"]
            # params (only update if we have a verified value)
            if d.get("params") is not None and existing.get("params") != d["params"]:
                updates["params"] = d["params"]
            # also clear stale params if override removed (set to None -> show —)
            elif d.get("params") is None and "params" in existing and existing.get("params") is not None:
                # keep existing value if no override; don't auto-clear
                pass
            # pricing
            if price:
                for field, idx in (("inputCost", 0), ("outputCost", 1), ("cachedReadCost", 2)):
                    newv = price[idx]
                    if newv is None:
                        continue
                    old = existing.get(field)
                    if old is None or abs(old - newv) > 1e-9:
                        updates[field] = newv
            if updates:
                changed.append((existing.get("name"), updates))
                if not dry_run:
                    for k, v in updates.items():
                        if k == "alsoOnZen" and v is False:
                            existing.pop("alsoOnZen", None)
                        else:
                            existing[k] = v

    if not dry_run:
        data["models"].sort(key=lambda x: x["name"].lower())
    return added, changed

def bench_slug_for(name: str) -> str:
    """Best-effort BenchLM slug for an OpenCode model name."""
    if name in BENCH_SLUG_OVERRIDES:
        return BENCH_SLUG_OVERRIDES[name]
    return id_from_name(name)

# BenchLM coding benchmark fields merged into each model (null if unpublished).
BENCH_FIELDS = ("swePro", "terminalBench", "deepSwe")

def bench_item_for(model_name, field, by_slug, by_norm):
    """Resolve the BenchLM item for a model+field (per-field slug overrides)."""
    if field == "deepSwe":
        slug = BENCH_SLUG_OVERRIDES_DEEPSWE.get(model_name) or bench_slug_for(model_name)
    elif field == "terminalBench":
        slug = BENCH_SLUG_OVERRIDES_TERMINAL.get(model_name) or bench_slug_for(model_name)
    else:
        slug = bench_slug_for(model_name)
    return by_slug.get(slug) or by_norm.get(normalize(model_name))

def _bench_num(v):
    """Numeric value of a stored benchmark cell; tolerates strings like '9.67?'."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        try:
            return float(str(v).rstrip("?").strip())
        except ValueError:
            return None

def merge_benchmarks(models, bench_items, dry_run=False):
    """Merge coding benchmark scores (BENCH_FIELDS) from BenchLM into models."""
    by_slug = {}
    by_norm = {}
    for it in bench_items:
        by_slug[it.get("slug")] = it
        by_norm[normalize(it.get("model"))] = it

    changed = []
    for m in models:
        for field in BENCH_FIELDS:
            it = bench_item_for(m["name"], field, by_slug, by_norm)
            if not it:
                continue
            coding = it.get("benchmarks", {}).get("coding", {}) or {}
            if field == "terminalBench":
                # prefer the newer Terminal-Bench 2.1, fall back to 2.0
                score = coding.get("terminalBench21")
                if score is None:
                    score = coding.get("terminalBench2")
            else:
                score = coding.get(field)
            if score is None:
                continue
            old = m.get(field)
            old_num = _bench_num(old)
            if old_num is None or abs(old_num - score) > 1e-9:
                changed.append((field, m["name"], old, score))
                if not dry_run:
                    m[field] = score
    return changed

# DeepSWE-specific BenchLM slug overrides. Some models' published DeepSWE lives
# under a different BenchLM slug than the one used for swePro/terminalBench (e.g.
# Qwen3.8 Max vs the older "Qwen3.8 Max Preview" build).
BENCH_SLUG_OVERRIDES_DEEPSWE = {
    "Qwen3.8 Max": "qwen3-8-max",
}

# Terminal-Bench-specific BenchLM slug overrides (same rationale as DeepSWE).
BENCH_SLUG_OVERRIDES_TERMINAL = {
    "Qwen3.8 Max": "qwen3-8-max",
}

# Hardcoded SWE-bench Pro scores not tracked by BenchLM, sourced from Scale AI's
# standardized SWE-bench Pro public leaderboard (labs.scale.com/leaderboard/swe_bench_pro_public).
SWE_PRO_OVERRIDES = {
    "Claude Haiku 4.5": 39.45,  # claude-4-5-haiku, ±3.55, Scale standardized public set
}

# Free-tier variants publish no benchmark runs of their own; they serve the same
# model as their non-free counterpart, so they inherit its scores.
# (Z.ai confirms Ox Alpha was the internal testing name for GLM-5.3-Flash.)
BENCH_INHERIT_FROM = {
    "DeepSeek V4 Flash Free": "DeepSeek V4 Flash",
    "MiMo-V2.5 Free": "MiMo-V2.5",
    "Hy3 Free": "Hy3",
    "Ox Alpha Free": "GLM-5.3-Flash",
    "Laguna S 2.1 Free": "Laguna S 2.1",
    "Muse Spark 1.2 Contributor Free": "Muse Spark 1.2",
}

def inherit_benchmarks(models, bench_items, dry_run=False):
    """Copy benchmark scores from each free variant's non-free counterpart (BENCH_INHERIT_FROM)."""
    by_slug = {}
    by_norm = {}
    for it in bench_items:
        by_slug[it.get("slug")] = it
        by_norm[normalize(it.get("model"))] = it

    changed = []
    for m in models:
        counterpart = BENCH_INHERIT_FROM.get(m["name"])
        if not counterpart:
            continue
        it = by_slug.get(bench_slug_for(counterpart)) or by_norm.get(normalize(counterpart))
        if not it:
            continue
        coding = it.get("benchmarks", {}).get("coding", {}) or {}
        pairs = [
            ("codingIndex", coding.get("aaCodingIndex")),
            ("swePro", coding.get("swePro")),
            ("deepSwe", coding.get("deepSwe")),
            ("terminalBench", coding.get("terminalBench21") if coding.get("terminalBench21") is not None else coding.get("terminalBench2")),
        ]
        for field, score in pairs:
            if score is None:
                continue
            old = m.get(field)
            old_num = _bench_num(old)
            if old_num is None or abs(old_num - score) > 1e-9:
                changed.append((field, m["name"], old, score))
                if not dry_run:
                    m[field] = score
    return changed

def apply_bench_overrides(models, dry_run=False):
    """Apply hardcoded benchmark overrides (e.g. Scale SWE-bench Pro scores BenchLM lacks)."""
    changed = []
    for m in models:
        score = SWE_PRO_OVERRIDES.get(m["name"])
        if score is None:
            continue
        old = m.get("swePro")
        old_num = _bench_num(old)
        if old_num is None or abs(old_num - score) > 1e-9:
            changed.append(("swePro", m["name"], old, score))
            if not dry_run:
                m["swePro"] = score
    return changed

# Uncertain benchmark values, stored verbatim (with a trailing "?") on rows whose
# identity is unconfirmed. Big Pickle's scores are its presumed GLM-4.6 identity's;
# a real published score for the model itself replaces these automatically (the
# merge functions compare numerically, so "9.67?" == 9.67 and real data wins).
UNCERTAIN_BENCH_OVERRIDES = {
    "Big Pickle": {
        # GLM-4.6 on Scale AI's SWE-bench Pro public leaderboard: 9.67 ±2.15,
        # rank ~21 (leaderboard max 66.5), entry created 2026-01-27.
        "swePro": "9.67?",
        # Terminal-Bench v2.1 49.4% — Artificial Analysis's own independent run,
        # embedded in https://artificialanalysis.ai/models/glm-4-6-reasoning
        # (terminalbenchV21 = 0.4944; AA displays it rounded as 49%).
        "terminalBench": "49.4?",
    },
}

def apply_uncertain_bench_overrides(models, dry_run=False):
    """Set uncertain (identity-inferred) benchmark values verbatim, with '?' intact."""
    # canonical key placement: each field goes after the last present predecessor
    preds = {
        "codingIndex": ("context",),
        "swePro": ("codingIndex", "context"),
        "terminalBench": ("swePro", "codingIndex", "context"),
        "deepSwe": ("terminalBench", "swePro", "codingIndex", "context"),
    }
    changed = []
    for m in models:
        for field, val in UNCERTAIN_BENCH_OVERRIDES.get(m["name"], {}).items():
            if str(m.get(field)) == str(val):
                continue
            changed.append((field, m["name"], m.get(field), val))
            if dry_run:
                continue
            if field in m:
                m[field] = val
            else:
                for after in preds.get(field, ()):
                    if after in m:
                        _insert_after(m, field, val, after)
                        break
                else:
                    m[field] = val
    return changed

# Availability: models.dev is the catalog OpenCode's model picker consumes.
# A model is (N.A.) when it has no non-deprecated entry in either the `opencode`
# (Zen pay-as-you-go) or `opencode-go` (Go plan) provider.
UNAVAILABLE_STATUSES = {"deprecated"}
STATUS_ALIAS_IDS = {"x-preview-f-free": ("x-preview-f-free", "ox-alpha-free")}

def is_available(mid, md, mdgo):
    """True if the model is selectable in OpenCode (active entry in either provider)."""
    aliases = {normalize(a) for a in STATUS_ALIAS_IDS.get(mid, (mid,))} | {normalize(mid)}
    for prov in (md, mdgo):
        for pid, entry in prov.items():
            if normalize(pid) not in aliases:
                continue
            st = entry.get("status")
            if st is None or st not in UNAVAILABLE_STATUSES:
                return True
    return False

def _insert_after(d, new_key, value, after_key):
    """Insert new_key/value into dict d right after after_key (in place)."""
    if new_key in d:
        d[new_key] = value
        return
    out = {}
    placed = False
    for k, v in d.items():
        out[k] = v
        if k == after_key:
            out[new_key] = value
            placed = True
    if not placed:
        out[new_key] = value
    d.clear()
    d.update(out)

def apply_na_flags(models, md, mdgo, catalog_ids=(), dry_run=False, today=None):
    """Set/unset the `na` field (Not Available) on every row.

    A model is Not Available when it has no non-deprecated entry in models.dev
    (opencode / opencode-go providers) OR it is no longer in the live Zen+Go
    catalogs. Rows are never removed; retired models simply stay flagged.
    Also maintains `naSince` (date the model was first flagged) so
    prune_na_models.py can retire rows that have been N.A. for over 6 months.
    Returns list of (name, kind) where kind is 'flag' | 'unflag' | 'backfill'.
    """
    if today is None:
        today = date.today()
    cat_norm = {normalize(i) for i in catalog_ids}
    changed = []
    for m in models:
        if m.get("plan") == "openrouter":
            continue  # availability maintained via the OpenRouter catalog sync
        mid = id_from_name(m["name"])
        na = normalize(mid) not in cat_norm or not is_available(mid, md, mdgo)
        if bool(m.get("na")) == na and (not na or m.get("naSince")):
            continue
        kind = "flag" if na else "unflag"
        if na and bool(m.get("na")) and not m.get("naSince"):
            kind = "backfill"
        changed.append((m["name"], kind))
        if dry_run:
            continue
        if na:
            if "na" not in m:
                _insert_after(m, "na", True, "plan")
            else:
                m["na"] = True
            _insert_after(m, "naSince", today.isoformat(), "na")
        else:
            m.pop("na", None)
            m.pop("naSince", None)
    return changed

def update_checked_date(index_path: Path, today) -> bool:
    """Refresh the 'Checked <date>.' footer note in the web page. Returns True if changed."""
    try:
        text = index_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    new_date = today.strftime("%b %d, %Y").replace(" 0", " ")
    new_text, n = re.subn(r'Checked [A-Z][a-z]{2} \d{1,2}, \d{4}\.', f'Checked {new_date}.', text)
    if n and new_text != text:
        index_path.write_text(new_text, encoding="utf-8")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Update models.json from OpenCode Zen catalog + pricing")
    parser.add_argument("--zen-url", default=DEFAULT_ZEN_URL)
    parser.add_argument("--go-url", default=DEFAULT_GO_URL)
    parser.add_argument("--zen-api-url", default=DEFAULT_ZEN_API_URL)
    parser.add_argument("--go-api-url", default=DEFAULT_GO_API_URL)
    parser.add_argument("--modelsdev-url", default=DEFAULT_MODELSDEV_URL)
    parser.add_argument("--benchlm-url", default=DEFAULT_BENCHLM_URL)
    parser.add_argument("--openrouter-url", default=DEFAULT_OPENROUTER_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODELS_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--no-sync", action="store_true", help="Only update prices of existing models")
    args = parser.parse_args()

    try:
        zen_ids = [d["id"] for d in fetch_json(args.zen_api_url)["data"]]
        go_ids = [d["id"] for d in fetch_json(args.go_api_url)["data"]]
    except Exception as e:
        print(f"Error fetching model catalogs: {e}", file=sys.stderr); sys.exit(1)

    zen_pricing = extract_pricing_table(fetch_html(args.zen_url), is_go=False)
    go_pricing = extract_pricing_table(fetch_html(args.go_url), is_go=True)
    try:
        mdev = fetch_json(args.modelsdev_url)
        md = mdev.get("opencode", {}).get("models", {})
        mdgo = mdev.get("opencode-go", {}).get("models", {})
    except Exception:
        md = {}
        mdgo = {}
    try:
        bench_items = fetch_json(args.benchlm_url)["items"]
    except Exception as e:
        bench_items = []
        print(f"Warning: could not fetch BenchLM data: {e}", file=sys.stderr)

    if args.verbose:
        print(f"Zen catalog: {len(zen_ids)}, Go plan: {len(go_ids)}", file=sys.stderr)
        print(f"Zen pricing rows: {len(zen_pricing)}, Go pricing rows: {len(go_pricing)}", file=sys.stderr)
        print(f"BenchLM models: {len(bench_items)}", file=sys.stderr)

    data = json.loads(args.output.read_text(encoding="utf-8"))

    if not args.no_sync:
        desired = build_desired(zen_ids, go_ids, md, mdgo)
        added, changed = reconcile(data, desired, zen_pricing, go_pricing, md, dry_run=args.dry_run)
    else:
        added = changed = []

    try:
        or_models = fetch_json(args.openrouter_url)["data"]
    except Exception as e:
        or_models = []
        print(f"Warning: could not fetch OpenRouter catalog: {e}", file=sys.stderr)
    or_added, or_changed = sync_openrouter(data["models"], or_models, dry_run=args.dry_run)
    added = list(added) + or_added
    changed = list(changed) + or_changed

    bench_changed = merge_benchmarks(data["models"], bench_items, dry_run=args.dry_run)
    bench_changed += apply_bench_overrides(data["models"], dry_run=args.dry_run)
    bench_changed += inherit_benchmarks(data["models"], bench_items, dry_run=args.dry_run)
    bench_changed += apply_uncertain_bench_overrides(data["models"], dry_run=args.dry_run)
    na_changed = apply_na_flags(data["models"], md, mdgo, catalog_ids=list(zen_ids) + list(go_ids), dry_run=args.dry_run)

    if changed:
        print(f"\n{len(changed)} price/plan update(s):" + (" (dry-run)" if args.dry_run else ""), file=sys.stderr)
        for name, updates in changed:
            print(f"  {name:34} {updates}", file=sys.stderr)
    if bench_changed:
        print(f"\n{len(bench_changed)} benchmark update(s):" + (" (dry-run)" if args.dry_run else ""), file=sys.stderr)
        for field, name, old, new in bench_changed:
            print(f"  {field:10} {name:34} {old} -> {new}", file=sys.stderr)
    if na_changed:
        print(f"\n{len(na_changed)} availability update(s):" + (" (dry-run)" if args.dry_run else ""), file=sys.stderr)
        for name, kind in na_changed:
            label = {"flag": "-> (N.A.)", "unflag": "-> available", "backfill": "-> (N.A.) [recorded naSince]"}[kind]
            print(f"  {name:34} {label}", file=sys.stderr)
    if added:
        print(f"\n{len(added)} model(s) to add:" if args.dry_run else f"\n{len(added)} model(s) added:", file=sys.stderr)
        for name, i in added:
            print(f"  + {name:34} ({i})", file=sys.stderr)
    if not (changed or added or bench_changed or na_changed):
        print("\nCatalog, prices and benchmarks in sync (no changes).", file=sys.stderr)

    if not args.dry_run and (changed or added or bench_changed or na_changed):
        today = date.today().isoformat()
        data["source"] = f"OpenCode Zen pricing (OpenCode model registry / Zen pricing page), retrieved {today}"
        data["goSource"] = f"OpenCode Go plan (https://opencode.ai/zen/go/v1/models), retrieved {today}"
        data["benchmarkPro"] = f"SWE-bench Pro (Scale AI), via {DEFAULT_BENCHLM_URL}, retrieved {today}"
        data["benchmarkTerminal"] = f"Terminal-Bench (Laude Institute), via {DEFAULT_BENCHLM_URL}, retrieved {today}"
        data["benchmarkDeepSwe"] = f"DeepSWE (Datacurve), via {DEFAULT_BENCHLM_URL}, retrieved {today}"
        args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nWrote {args.output}", file=sys.stderr)
    elif args.dry_run:
        print("\nDry-run: no file written.", file=sys.stderr)
    else:
        print("\nNo changes to write.", file=sys.stderr)

    if not args.dry_run:
        index_path = args.output.parent / "index.html"
        if update_checked_date(index_path, date.today()):
            print(f"Updated 'Checked' date in {index_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
