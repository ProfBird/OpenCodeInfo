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
    "gpt-5.6-luna": "GPT 5.6 Luna", "grok-4.5": "Grok 4.5",
    "deepseek-v4-pro": "DeepSeek V4 Pro", "deepseek-v4-flash": "DeepSeek V4 Flash",
    "deepseek-v4-flash-vision-exp": "DeepSeek V4 Flash Vision Exp",
    "glm-5.3": "GLM-5.3", "glm-5.2": "GLM-5.2", "glm-5.1": "GLM-5.1", "glm-5": "GLM-5",
    "minimax-m3": "MiniMax M3", "minimax-m2.7": "MiniMax M2.7", "minimax-m2.5": "MiniMax M2.5",
    "kimi-k3": "Kimi K3", "kimi-k2.7-code": "Kimi K2.7 Code", "kimi-k2.6": "Kimi K2.6",
    "kimi-k2.5": "Kimi K2.5", "qwen3.6-plus": "Qwen3.6 Plus", "qwen3.5-plus": "Qwen3.5 Plus",
    "qwen3.7-max": "Qwen3.7 Max", "qwen3.7-plus": "Qwen3.7 Plus", "qwen3.8-max": "Qwen3.8 Max",
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
    "LongCat-2.0": "longcat-2-0",
    "Grok Build 0.1": "grok-build-0-1",
    "MiniMax M2.5": "minimax-m2-5",
    "GLM-5.3": "glm-5-3",
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
    "glm-5": "203K", "glm-5.1": "203K", "glm-5.2": "1M", "glm-5.3": "1M",
    "hy3": "256K", "hy3-preview": "256K",
    "kimi-k2.5": "256K", "kimi-k2.6": "262K", "kimi-k2.7-code": "262K", "kimi-k3": "1M",
    "minimax-m2.5": "200K", "minimax-m2.7": "205K", "minimax-m3": "1M",
    "qwen3.5-plus": "1M", "qwen3.6-plus": "1M", "qwen3.7-max": "1M",
    "qwen3.7-plus": "1M", "qwen3.8-max": "1M",
    "longcat-2.0": "1M", "mimo-v2.5": "1M", "mimo-v2.5-pro": "1M",
    "mimo-v2-pro": "1M", "mimo-v2-omni": "1M",
    "muse-spark-1.2-contributor": "1M", "ox-alpha-free": "1M",
    "deepseek-v4-flash-vision-exp": "1M",
    "gpt-5.6-luna": "1.05M", "grok-4.5": "500K",
    "deepseek-v4-pro": "1M", "deepseek-v4-flash": "1M",
}

def build_desired(zen_ids, go_ids, md):
    """Return dict id -> row data for the full union of Zen + Go models."""
    go_set = set(go_ids)
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
            "inputCost": cost.get("input"),
            "outputCost": cost.get("output"),
            "cachedReadCost": cost.get("cache_read"),
            "context": CONTEXT_OVERRIDES.get(i) or fmt_ctx((m.get("limit") or {}).get("context")),
        }
    return desired

def reconcile(data, desired, zen_pricing, go_pricing, md, dry_run=False):
    """Add/remove/update models to match the desired catalog."""
    models = data.setdefault("models", [])
    by_id = {}
    for m in models:
        by_id[normalize(id_from_name(m["name"]))] = m
        by_id[normalize(m["name"])] = m

    added = []
    removed = []
    changed = []

    desired_norm = {normalize(i) for i in desired}

    # Remove models no longer in the Zen catalog
    keep = []
    for m in models:
        mid = normalize(id_from_name(m["name"]))
        if mid not in desired_norm:
            removed.append(m["name"])
            if not dry_run:
                continue
        keep.append(m)
    if not dry_run:
        data["models"] = keep
        models = keep

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
                "plan": d["plan"],
            }
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
            # context (only update if we have a real value)
            if d["context"] and existing.get("context") != d["context"]:
                updates["context"] = d["context"]
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
                        existing[k] = v

    if not dry_run:
        data["models"].sort(key=lambda x: x["name"].lower())
    return added, removed, changed

def bench_slug_for(name: str) -> str:
    """Best-effort BenchLM slug for an OpenCode model name."""
    if name in BENCH_SLUG_OVERRIDES:
        return BENCH_SLUG_OVERRIDES[name]
    return id_from_name(name)

# BenchLM coding benchmark fields merged into each model (null if unpublished).
BENCH_FIELDS = ("swePro", "aaSciCode")

def merge_benchmarks(models, bench_items, dry_run=False):
    """Merge coding benchmark scores (BENCH_FIELDS) from BenchLM into models."""
    by_slug = {}
    by_norm = {}
    for it in bench_items:
        by_slug[it.get("slug")] = it
        by_norm[normalize(it.get("model"))] = it

    changed = []
    for m in models:
        it = by_slug.get(bench_slug_for(m["name"])) or by_norm.get(normalize(m["name"]))
        if not it:
            continue
        coding = it.get("benchmarks", {}).get("coding", {}) or {}
        for field in BENCH_FIELDS:
            score = coding.get(field)
            if score is None:
                continue
            old = m.get(field)
            if old is None or abs(old - score) > 1e-9:
                changed.append((field, m["name"], old, score))
                if not dry_run:
                    m[field] = score
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
        md = fetch_json(args.modelsdev_url).get("opencode", {}).get("models", {})
    except Exception:
        md = {}
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
        desired = build_desired(zen_ids, go_ids, md)
        added, removed, changed = reconcile(data, desired, zen_pricing, go_pricing, md, dry_run=args.dry_run)
    else:
        added = removed = changed = []

    bench_changed = merge_benchmarks(data["models"], bench_items, dry_run=args.dry_run)

    if changed:
        print(f"\n{len(changed)} price/plan update(s):" + (" (dry-run)" if args.dry_run else ""), file=sys.stderr)
        for name, updates in changed:
            print(f"  {name:34} {updates}", file=sys.stderr)
    if bench_changed:
        print(f"\n{len(bench_changed)} benchmark update(s):" + (" (dry-run)" if args.dry_run else ""), file=sys.stderr)
        for field, name, old, new in bench_changed:
            print(f"  {field:10} {name:34} {old} -> {new}", file=sys.stderr)
    if added:
        print(f"\n{len(added)} model(s) to add:" if args.dry_run else f"\n{len(added)} model(s) added:", file=sys.stderr)
        for name, i in added:
            print(f"  + {name:34} ({i})", file=sys.stderr)
    if removed:
        print(f"\n{len(removed)} model(s) to remove:" if args.dry_run else f"\n{len(removed)} model(s) removed:", file=sys.stderr)
        for name in removed:
            print(f"  - {name}", file=sys.stderr)
    if not (changed or added or removed or bench_changed):
        print("\nCatalog, prices and benchmarks in sync (no changes).", file=sys.stderr)

    if not args.dry_run and (changed or added or removed or bench_changed):
        today = date.today().isoformat()
        data["source"] = f"OpenCode Zen pricing (OpenCode model registry / Zen pricing page), retrieved {today}"
        data["goSource"] = f"OpenCode Go plan (https://opencode.ai/zen/go/v1/models), retrieved {today}"
        data["benchmarkPro"] = f"SWE-bench Pro (Scale AI), via {DEFAULT_BENCHLM_URL}, retrieved {today}"
        data["benchmarkSciCode"] = f"AA SciCode (Artificial Analysis), via {DEFAULT_BENCHLM_URL}, retrieved {today}"
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
