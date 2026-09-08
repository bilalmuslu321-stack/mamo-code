#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 ███╗   ███╗ █████╗ ███╗   ███╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
 Mamo Code V2.3 — single-file terminal coding assistant with 100+ AI API support.

 Install :  pip install litellm rich requests prompt_toolkit   (optional: pyperclip)
 Run     :  python mamo.py
 Config  :  ~/.mamo/config.json      Sessions: ~/.mamo/sessions/
"""
import os, sys, re, json, time, subprocess, logging, difflib, shutil
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.spinner import Spinner
    from rich.syntax import Syntax
    from rich import box
except ImportError:
    print("Missing packages. Run:  pip install litellm rich requests prompt_toolkit")
    sys.exit(1)

logging.disable(logging.CRITICAL)
os.environ.setdefault("LITELLM_LOG", "ERROR")
import litellm
litellm.suppress_debug_info = True
litellm.drop_params = True

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import HTML
    HAS_PT = True
except ImportError:
    HAS_PT = False

VERSION = "2.3.0"
CONFIG_DIR = Path.home() / ".mamo"
CONFIG_FILE = CONFIG_DIR / "config.json"
SESS_DIR = CONFIG_DIR / "sessions"
console = Console()
GRADIENT = ["#7c3aed", "#8b5cf6", "#a78bfa", "#c084fc", "#e879f9", "#f472b6", "#fb7185", "#fb923c"]
ACC = "#c084fc"   # purple
ACC2 = "#fb923c"  # orange

CHANGELOG = {
    "2.3.0": [
        "Fixed: OpenRouter 'requires more credits / max_tokens' crash → output is auto-capped to what your credits allow",
        "Fixed: local servers not detected (Ollama, LM Studio…) → 127.0.0.1 first (IPv6 bug), OLLAMA_HOST, WSL host, CLI fallback, auto-start Ollama",
        "New: /local  scan or add local servers · /credits  OpenRouter balance · /changelog",
        "Real cost tracking for OpenRouter, Groq, DeepSeek, Mistral, xAI, Together, Fireworks, DeepInfra, Perplexity, Cerebras, SambaNova, NVIDIA",
        "Smarter retries: rate-limit backoff, adaptive max_tokens (never silently removed), friendly quota errors, no misleading warnings",
        "Fixed: crash after Ctrl-C in the middle of a tool call · compact() edge-case crash · local diagnostics table",
        "Update log shown at startup  (/changelog off  to hide)",
    ],
    "2.0.0": [
        "Token fixes: usage tracking in streaming, auto-compact at 75% context, tool-output pruning, context-overflow retry",
        "~45 new providers, /mode plan|build, sessions (/save /load), /add, /undo, /retry, /export, /copy, /tree, /git, /diff, 9 new skills",
    ],
}

# ═══════════════════════════════════════════════════════════════════════════
#  PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════
def P(label, kind, base=None):
    return {"label": label, "kind": kind, "base": base}

PROVIDERS = {
    # ── big labs ──────────────────────────────────────────────────────────
    "openai":      P("OpenAI",                     "openai",    "https://api.openai.com/v1"),
    "anthropic":   P("Anthropic (Claude)",         "anthropic"),
    "gemini":      P("Google Gemini",              "gemini"),
    "gemini_oai":  P("Google Gemini (OpenAI-compat)", "openai", "https://generativelanguage.googleapis.com/v1beta/openai"),
    "xai":         P("xAI (Grok)",                 "openai",    "https://api.x.ai/v1"),
    "mistral":     P("Mistral",                    "openai",    "https://api.mistral.ai/v1"),
    "codestral":   P("Mistral Codestral",          "openai",    "https://codestral.mistral.ai/v1"),
    "cohere":      P("Cohere",                     "cohere"),
    "cohere_oai":  P("Cohere (OpenAI-compat)",     "openai",    "https://api.cohere.ai/compatibility/v1"),
    "deepseek":    P("DeepSeek",                   "openai",    "https://api.deepseek.com/v1"),
    "perplexity":  P("Perplexity",                 "openai",    "https://api.perplexity.ai"),
    "ai21":        P("AI21 Labs",                  "openai",    "https://api.ai21.com/studio/v1"),
    "meta":        P("Meta Llama API",             "openai",    "https://api.llama.com/compat/v1"),
    "reka":        P("Reka",                       "openai",    "https://api.reka.ai/v1"),
    "inception":   P("Inception (Mercury)",        "openai",    "https://api.inceptionlabs.ai/v1"),
    "morph":       P("Morph (fast apply)",         "openai",    "https://api.morphllm.com/v1"),
    "nous":        P("Nous Research",              "openai",    "https://inference-api.nousresearch.com/v1"),
    "arcee":       P("Arcee AI",                   "openai",    "https://conductor.arcee.ai/v1"),
    # ── fast inference clouds ─────────────────────────────────────────────
    "groq":        P("Groq",                       "openai",    "https://api.groq.com/openai/v1"),
    "cerebras":    P("Cerebras",                   "openai",    "https://api.cerebras.ai/v1"),
    "sambanova":   P("SambaNova",                  "openai",    "https://api.sambanova.ai/v1"),
    "together":    P("Together AI",                "openai",    "https://api.together.xyz/v1"),
    "fireworks":   P("Fireworks AI",               "openai",    "https://api.fireworks.ai/inference/v1"),
    "deepinfra":   P("DeepInfra",                  "openai",    "https://api.deepinfra.com/v1/openai"),
    "nvidia":      P("NVIDIA NIM",                 "openai",    "https://integrate.api.nvidia.com/v1"),
    "hyperbolic":  P("Hyperbolic",                 "openai",    "https://api.hyperbolic.xyz/v1"),
    "nebius":      P("Nebius",                     "openai",    "https://api.studio.nebius.com/v1"),
    "novita":      P("Novita AI",                  "openai",    "https://api.novita.ai/v3/openai"),
    "featherless": P("Featherless",                "openai",    "https://api.featherless.ai/v1"),
    "chutes":      P("Chutes",                     "openai",    "https://llm.chutes.ai/v1"),
    "friendli":    P("Friendli",                   "openai",    "https://api.friendli.ai/serverless/v1"),
    "kluster":     P("Kluster AI",                 "openai",    "https://api.kluster.ai/v1"),
    "inference":   P("Inference.net",              "openai",    "https://api.inference.net/v1"),
    "parasail":    P("Parasail",                   "openai",    "https://api.parasail.io/v1"),
    "targon":      P("Targon",                     "openai",    "https://api.targon.com/v1"),
    "lambda":      P("Lambda",                     "openai",    "https://api.lambda.ai/v1"),
    "scaleway":    P("Scaleway",                   "openai",    "https://api.scaleway.ai/v1"),
    "venice":      P("Venice AI",                  "openai",    "https://api.venice.ai/api/v1"),
    "baseten":     P("Baseten",                    "openai",    "https://inference.baseten.co/v1"),
    "crusoe":      P("Crusoe Cloud",               "openai",    "https://api.crusoe.ai/v1"),
    "nscale":      P("Nscale",                     "openai",    "https://inference-api.nscale.com/v1"),
    "avian":       P("Avian",                      "openai",    "https://api.avian.io/v1"),
    "atlas":       P("Atlas Cloud",                "openai",    "https://api.atlascloud.ai/v1"),
    "cortecs":     P("Cortecs",                    "openai",    "https://api.cortecs.ai/v1"),
    "gmi":         P("GMI Cloud",                  "openai",    "https://api.gmi-serving.com/v1"),
    "io":          P("IO Intelligence",            "openai",    "https://api.intelligence.io.solutions/api/v1"),
    "vultr":       P("Vultr Inference",            "openai",    "https://api.vultrinference.com/v1"),
    "akash":       P("Akash Chat API",             "openai",    "https://chatapi.akash.network/api/v1"),
    "ionos":       P("IONOS AI Hub",               "openai",    "https://openai.inference.de-txl.ionos.com/v1"),
    "digitalocean":P("DigitalOcean Gradient",      "openai",    "https://inference.do-ai.run/v1"),
    "cloudrift":   P("CloudRift",                  "openai",    "https://inference.cloudrift.ai/v1"),
    "redpill":     P("RedPill (Phala)",            "openai",    "https://api.redpill.ai/v1"),
    "arli":        P("Arli AI",                    "openai",    "https://api.arliai.com/v1"),
    "infermatic":  P("Infermatic",                 "openai",    "https://api.totalgpt.ai/v1"),
    "mancer":      P("Mancer",                     "openai",    "https://neuro.mancer.tech/oai/v1"),
    "ollama_cloud":P("Ollama Cloud",               "openai",    "https://ollama.com/v1"),
    # ── routers / aggregators ─────────────────────────────────────────────
    "openrouter":  P("OpenRouter (300+ models)",   "openai",    "https://openrouter.ai/api/v1"),
    "vercel":      P("Vercel AI Gateway",          "openai",    "https://ai-gateway.vercel.sh/v1"),
    "requesty":    P("Requesty",                   "openai",    "https://router.requesty.ai/v1"),
    "aihubmix":    P("AiHubMix",                   "openai",    "https://aihubmix.com/v1"),
    "ai302":       P("302.AI",                     "openai",    "https://api.302.ai/v1"),
    "poe":         P("Poe",                        "openai",    "https://api.poe.com/v1"),
    "nanogpt":     P("NanoGPT",                    "openai",    "https://nano-gpt.com/api/v1"),
    "huggingface": P("Hugging Face",               "openai",    "https://router.huggingface.co/v1"),
    "github":      P("GitHub Models",              "openai",    "https://models.github.ai/inference"),
    # ── asia ──────────────────────────────────────────────────────────────
    "moonshot":    P("Moonshot (Kimi) · intl",     "openai",    "https://api.moonshot.ai/v1"),
    "moonshot_cn": P("Moonshot (Kimi) · CN",       "openai",    "https://api.moonshot.cn/v1"),
    "zhipu":       P("Zhipu (GLM) · CN",           "openai",    "https://open.bigmodel.cn/api/paas/v4"),
    "zai":         P("Z.ai (GLM) · intl",          "openai",    "https://api.z.ai/api/paas/v4"),
    "qwen":        P("Alibaba Qwen · intl",        "openai",    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
    "qwen_cn":     P("Alibaba Qwen · CN",          "openai",    "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    "modelscope":  P("ModelScope",                 "openai",    "https://api-inference.modelscope.cn/v1"),
    "siliconflow": P("SiliconFlow",                "openai",    "https://api.siliconflow.cn/v1"),
    "minimax":     P("MiniMax",                    "openai",    "https://api.minimax.io/v1"),
    "stepfun":     P("StepFun",                    "openai",    "https://api.stepfun.com/v1"),
    "hunyuan":     P("Tencent Hunyuan",            "openai",    "https://api.hunyuan.cloud.tencent.com/v1"),
    "volcengine":  P("ByteDance Volcengine (Doubao)", "openai", "https://ark.cn-beijing.volces.com/api/v3"),
    "qianfan":     P("Baidu Qianfan (ERNIE)",      "openai",    "https://qianfan.baidubce.com/v2"),
    "spark":       P("iFlytek Spark",              "openai",    "https://spark-api-open.xf-yun.com/v1"),
    "infini":      P("Infini-AI",                  "openai",    "https://cloud.infini-ai.com/maas/v1"),
    "yi":          P("01.AI (Yi)",                 "openai",    "https://api.lingyiwanwu.com/v1"),
    "baichuan":    P("Baichuan",                   "openai",    "https://api.baichuan-ai.com/v1"),
    "upstage":     P("Upstage (Solar)",            "openai",    "https://api.upstage.ai/v1"),
    # ── local (127.0.0.1 on purpose: 'localhost' → ::1 breaks on Windows) ──
    "ollama":      P("Ollama (local)",             "ollama",    "http://127.0.0.1:11434"),
    "lmstudio":    P("LM Studio (local)",          "openai",    "http://127.0.0.1:1234/v1"),
    "vllm":        P("vLLM / llama.cpp (local)",   "openai",    "http://127.0.0.1:8000/v1"),
    "jan":         P("Jan (local)",                "openai",    "http://127.0.0.1:1337/v1"),
    "localai":     P("LocalAI / llamafile (local)","openai",    "http://127.0.0.1:8080/v1"),
    "kobold":      P("KoboldCpp (local)",          "openai",    "http://127.0.0.1:5001/v1"),
    "textgen":     P("text-generation-webui (local)", "openai", "http://127.0.0.1:5000/v1"),
    "gpt4all":     P("GPT4All (local)",            "openai",    "http://127.0.0.1:4891/v1"),
    "xinference":  P("Xinference (local)",         "openai",    "http://127.0.0.1:9997/v1"),
    "litellm":     P("LiteLLM Proxy (local)",      "openai",    "http://127.0.0.1:4000/v1"),
    "custom":      P("Custom OpenAI-compatible URL", "openai"),
}
def prov(pid): return PROVIDERS.get(pid) or P(pid, "openai")
LOCAL = [k for k, v in PROVIDERS.items() if v["base"] and urlparse(v["base"]).hostname in ("127.0.0.1", "localhost")]

# litellm native providers → real cost tables + model info (context size, reasoning support)
LM_PREFIX = {"openrouter": "openrouter/", "groq": "groq/", "deepseek": "deepseek/", "mistral": "mistral/",
             "codestral": "codestral/", "xai": "xai/", "together": "together_ai/", "fireworks": "fireworks_ai/",
             "deepinfra": "deepinfra/", "perplexity": "perplexity/", "cerebras": "cerebras/", "sambanova": "sambanova/",
             "nvidia": "nvidia_nim/"}
KIND_PREFIX = {"anthropic": "anthropic/", "gemini": "gemini/", "cohere": "cohere_chat/", "ollama": "ollama_chat/"}

# ═══════════════════════════════════════════════════════════════════════════
#  API KEY PATTERNS   (regex, [providers], strong)
# ═══════════════════════════════════════════════════════════════════════════
UUID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
KEY_PATTERNS = [
    (r"^sk-ant-",                       ["anthropic"],              True),
    (r"^sk-or-",                        ["openrouter"],             True),
    (r"^gsk_",                          ["groq"],                   True),
    (r"^xai-",                          ["xai"],                    True),
    (r"^AIza",                          ["gemini", "gemini_oai"],   True),
    (r"^pplx-",                         ["perplexity"],             True),
    (r"^csk-",                          ["cerebras"],               True),
    (r"^fw_",                           ["fireworks"],              True),
    (r"^nvapi-",                        ["nvidia"],                 True),
    (r"^hf_",                           ["huggingface"],            True),
    (r"^(ghp_|github_pat_|gho_)",       ["github"],                 True),
    (r"^up_",                           ["upstage"],                True),
    (r"^rc_",                           ["featherless"],            True),
    (r"^cpk_",                          ["chutes"],                 True),
    (r"^sk_",                           ["novita"],                 True),
    (r"^secret_",                       ["lambda"],                 True),
    (r"^flp_",                          ["friendli"],               True),
    (r"^vck_",                          ["vercel"],                 True),
    (r"^LLM\|",                         ["meta"],                   True),
    (r"^ms-",                           ["modelscope"],             True),
    (r"^bce-v3/",                       ["qianfan"],                True),
    (r"^[a-f0-9]{32}\.[A-Za-z0-9]{16}$", ["zhipu", "zai"],          True),
    (r"^sk-(proj|svcacct|admin)-",      ["openai"],                 True),
    (r"^sk-", ["openai", "deepseek", "moonshot", "moonshot_cn", "qwen", "qwen_cn", "siliconflow", "aihubmix",
               "requesty", "stepfun", "hunyuan", "ai302", "redpill", "nous", "morph", "akash", "infini"], False),
    (r"^eyJ", ["minimax", "hyperbolic", "nebius", "ionos", "io"], False),
    (UUID,    ["sambanova", "scaleway", "kluster", "volcengine", "nanogpt", "arli"], False),
    (r"^[A-Za-z0-9]{32}$",              ["mistral", "codestral", "deepinfra"], False),
    (r"^[A-Za-z0-9]{40}$",              ["cohere", "cohere_oai"],   False),
    (r"^[a-f0-9]{64}$",                 ["together"],               False),
    (r"^[A-Za-z0-9]{64}$",              ["ai21"],                   False),
    (r"^[A-Za-z0-9_-]{40,50}$",         ["poe"],                    False),
]
PROBE_FALLBACK = [k for k, v in PROVIDERS.items() if v["kind"] == "openai" and v["base"] and k not in LOCAL] \
                 + ["anthropic", "gemini", "cohere"]

# ═══════════════════════════════════════════════════════════════════════════
#  STATE / CONFIG
# ═══════════════════════════════════════════════════════════════════════════
DEFAULT_CFG = {"providers": {}, "current": {}, "thinkmode": 1, "multimode": 1, "max_tokens": 8192,
               "temperature": None, "mode": "build", "lang": "", "system_extra": "", "autocompact": True,
               "ctx_limit": 0, "show_changelog": True}

class State:
    def __init__(s):
        s.cfg = dict(DEFAULT_CFG); s.messages = []
        s.cost = 0.0; s.tin = s.tout = s.requests = 0
        s.yolo = False; s.attach = []; s.last_user = ""; s.t_start = time.time()
        s.cap = 0          # session output-token cap learned from provider errors (credits / model limit)
S = State()

def load_cfg():
    if CONFIG_FILE.exists():
        try: S.cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception: pass
    for k, v in DEFAULT_CFG.items(): S.cfg.setdefault(k, v)
    # migrate old localhost bases → 127.0.0.1
    for p in S.cfg["providers"].values():
        if p.get("base") and "://localhost" in p["base"]: p["base"] = p["base"].replace("://localhost", "://127.0.0.1")

def save_cfg():
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(S.cfg, indent=2))
    try: os.chmod(CONFIG_FILE, 0o600)
    except Exception: pass

def cur():
    c = S.cfg["current"]; p = S.cfg["providers"].get(c.get("provider"), {})
    return c.get("provider"), c.get("model"), p.get("key"), p.get("base")

def lm_model(pid, model):
    return (LM_PREFIX.get(pid) or KIND_PREFIX.get(prov(pid)["kind"], "openai/")) + model

def lm_kwargs(stream=False):
    pid, model, key, base = cur(); kind = prov(pid)["kind"]
    kw = {"model": lm_model(pid, model), "api_key": key or "x"}
    if kind == "ollama": kw["api_base"] = base or prov(pid)["base"]
    elif kind == "openai" and (pid not in LM_PREFIX or base): kw["api_base"] = base or prov(pid)["base"]
    mt = int(S.cfg.get("max_tokens") or 0)
    if S.cap: mt = min(mt, S.cap) if mt else S.cap
    if mt: kw["max_tokens"] = mt
    if S.cfg.get("temperature") is not None: kw["temperature"] = float(S.cfg["temperature"])
    if stream:
        kw["stream"] = True
        if kind != "ollama": kw["stream_options"] = {"include_usage": True}
    if pid == "openrouter":
        kw["extra_headers"] = {"HTTP-Referer": "https://github.com/mamo-code", "X-Title": "Mamo Code"}
        kw["extra_body"] = {"usage": {"include": True}}       # exact cost from OpenRouter
    return kw

# ═══════════════════════════════════════════════════════════════════════════
#  TOKENS / CONTEXT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════
class CtxError(Exception): pass
CTX_ERR = ("context_length", "context length", "context window", "too many tokens", "maximum context", "token limit",
           "prompt is too long", "input is too long", "content_too_large", "request too large", "exceeds the limit")
_CTX_CACHE = {}

def est_tokens(msgs):
    n = 0
    for m in msgs:
        n += len(str(m.get("content") or ""))
        if m.get("tool_calls"): n += len(json.dumps(m["tool_calls"]))
    return n // 4 + 4 * len(msgs)

def ctx_limit():
    if S.cfg.get("ctx_limit"): return int(S.cfg["ctx_limit"])
    m = lm_kwargs()["model"]
    if m not in _CTX_CACHE:
        try:
            info = litellm.get_model_info(m)
            _CTX_CACHE[m] = int(info.get("max_input_tokens") or info.get("max_tokens") or 128000)
        except Exception: _CTX_CACHE[m] = 128000
    return _CTX_CACHE[m]

def _track(resp, messages=None, text=""):
    u = getattr(resp, "usage", None)
    pi = int(getattr(u, "prompt_tokens", 0) or 0); co = int(getattr(u, "completion_tokens", 0) or 0)
    if not pi and messages: pi = est_tokens(messages)
    if not co and text: co = max(1, len(text) // 4)
    S.tin += pi; S.tout += co; S.requests += 1
    cost = None
    try:
        cost = getattr(u, "cost", None)
        if cost is None and u is not None: cost = (getattr(u, "model_extra", None) or {}).get("cost")
    except Exception: cost = None
    if cost is None:
        try: cost = litellm.completion_cost(completion_response=resp)
        except Exception: cost = 0
    S.cost += float(cost or 0)

def prune_tool_outputs(msgs, keep=8, limit=600):
    idx = [i for i, m in enumerate(msgs) if m.get("role") == "tool"]
    for i in idx[:-keep]:
        c = msgs[i].get("content") or ""
        if len(c) > limit: msgs[i]["content"] = c[:limit] + f"\n...[{len(c)-limit} chars pruned to save context]"

def fix_dangling(msgs):
    """Remove an assistant tool_call turn whose tool results never arrived (Ctrl-C / error mid-run)."""
    for i in range(len(msgs) - 1, 0, -1):
        m = msgs[i]
        if m["role"] == "assistant" and m.get("tool_calls"):
            got = {t.get("tool_call_id") for t in msgs[i + 1:] if t["role"] == "tool"}
            if any(tc["id"] not in got for tc in m["tool_calls"]): del msgs[i:]
            return
        if m["role"] == "user": return

def compact(force=False):
    limit = ctx_limit(); used = est_tokens(S.messages)
    if not force and used < limit * 0.75: return False
    users = [i for i, m in enumerate(S.messages) if m["role"] == "user"]
    if len(S.messages) < 4 or not users:
        if force: warn("nothing to compact")
        return False
    cut = users[-2] if len(users) >= 2 else users[-1]
    if est_tokens(S.messages[cut:]) > limit * 0.3: cut = users[-1]
    head, tail = S.messages[1:cut], S.messages[cut:]
    if not head:
        if force: warn("nothing to compact")
        return False
    transcript = "\n".join(f"[{m['role']}] {str(m.get('content') or '')[:3000]}" for m in head)[:60000]
    with console.status(f"[{ACC}]compacting context (~{used:,} tokens → summary)...[/]", spinner="dots12"):
        try:
            kw = lm_kwargs(); kw["max_tokens"] = min(kw.get("max_tokens") or 2048, 2048)
            r = litellm.completion(**kw, messages=[
                {"role": "system", "content": "Summarize this coding session for continuation: goals, decisions, files "
                 "touched (with paths), current state, open issues. Keep code identifiers exact. Be dense; max 600 words."},
                {"role": "user", "content": transcript}])
            _track(r); summary = r.choices[0].message.content or ""
        except Exception as e: warn(f"compact failed: {str(e)[:120]}"); return False
    S.messages[:] = [S.messages[0],
                     {"role": "user", "content": f"[Context summary of earlier conversation]\n{summary}"},
                     {"role": "assistant", "content": "Understood, I have the context. Continuing."}] + tail
    ok(f"context compacted: ~{used:,} → ~{est_tokens(S.messages):,} tokens"); return True

def undo():
    idx = [i for i, m in enumerate(S.messages) if m["role"] == "user"]
    if not idx: return False
    del S.messages[idx[-1]:]; return True

# ═══════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════
BANNER = r"""
███╗   ███╗ █████╗ ███╗   ███╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
████╗ ████║██╔══██╗████╗ ████║██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
██╔████╔██║███████║██╔████╔██║██║   ██║    ██║     ██║   ██║██║  ██║█████╗
██║╚██╔╝██║██╔══██║██║╚██╔╝██║██║   ██║    ██║     ██║   ██║██║  ██║██╔══╝
██║ ╚═╝ ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝"""

def gradient_text(line, offset=0):
    t = Text()
    for i, ch in enumerate(line): t.append(ch, style=GRADIENT[((i + offset) // 6) % len(GRADIENT)])
    return t

def banner():
    console.clear()
    for i, line in enumerate(BANNER.strip("\n").split("\n")):
        console.print(gradient_text(line, i * 2)); time.sleep(0.04)
    console.print(Text(f"  V2.3 · v{VERSION} · {len(PROVIDERS)} providers · type /help for commands", style="dim")); console.print()

def show_changelog(full=False):
    body = Text()
    for v in (list(CHANGELOG) if full else [VERSION]):
        if full: body.append(f"v{v}\n", style=f"bold {ACC2}")
        for l in CHANGELOG.get(v, []): body.append("  • ", style=ACC); body.append(l + "\n")
    if not full: body.append("  /changelog for history · /changelog off to hide this", style="dim")
    console.print(Panel(body, title="[bold]Changelog[/]" if full else f"[bold {ACC}]🚀 What's new in v{VERSION}[/]",
                        border_style=ACC, expand=False))

def ok(m): console.print(f"[bold green]✓[/] {m}")
def warn(m): console.print(f"[bold yellow]![/] {m}")
def err(m): console.print(f"[bold red]✗[/] {m}")
def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True); return (r.stdout + r.stderr).strip()

def show_diff(old, new, path, max_lines=60):
    d = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"a/{path}", f"b/{path}", lineterm="", n=2))
    if d:
        more = f"\n... (+{len(d)-max_lines} lines)" if len(d) > max_lines else ""
        console.print(Syntax("\n".join(d[:max_lines]) + more, "diff", theme="ansi_dark", word_wrap=True))

def status_bar():
    pid, model, _, _ = cur()
    used = est_tokens(S.messages); lim = ctx_limit(); pct = min(100, used * 100 // max(lim, 1))
    t = Text(); t.append(" ◆ ", style=ACC); t.append(prov(pid)["label"], style="bold")
    t.append(f" · {model}", style=ACC2)
    if S.cfg["mode"] == "plan": t.append(" · PLAN", style="bold cyan")
    t.append(f" · think {S.cfg['thinkmode']}/5 · agents {S.cfg['multimode']}/3", style="dim")
    t.append(f" · ctx {pct}%", style="green" if pct < 60 else "yellow" if pct < 85 else "bold red")
    if S.cap: t.append(f" · out≤{S.cap}", style="yellow")
    if S.yolo: t.append(" · YOLO", style="bold red")
    t.append(f" · ${S.cost:.4f}", style="dim"); console.print(t)

# ═══════════════════════════════════════════════════════════════════════════
#  LOCAL SERVER DISCOVERY
# ═══════════════════════════════════════════════════════════════════════════
FOUND_BASE = {}

def _is_wsl():
    try: return "microsoft" in Path("/proc/version").read_text().lower()
    except Exception: return False

def _wsl_host():
    try:
        for l in Path("/etc/resolv.conf").read_text().splitlines():
            if l.startswith("nameserver"): return l.split()[1]
    except Exception: pass

def local_bases(pid):
    u = urlparse(prov(pid)["base"]); port = u.port; path = u.path.rstrip("/")
    hosts = []
    if pid == "ollama" and os.environ.get("OLLAMA_HOST"):
        h = os.environ["OLLAMA_HOST"].strip()
        if "://" not in h: h = "http://" + h
        hu = urlparse(h); hn = (hu.hostname or "127.0.0.1").replace("0.0.0.0", "127.0.0.1")
        hosts.append((hn, hu.port or 11434))
    hosts += [("127.0.0.1", port), ("localhost", port)]
    if _is_wsl(): hosts += [(h, port) for h in (_wsl_host(), "host.docker.internal") if h]
    out = []
    for h, p in hosts:
        b = f"http://{h}:{p}{path}"
        if b not in out: out.append(b)
    return out

def ollama_cli_models():
    exe = shutil.which("ollama")
    if not exe: return []
    try:
        r = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=8)
        if r.returncode != 0: return []
        return [l.split()[0] for l in r.stdout.splitlines()[1:] if l.strip()]
    except Exception: return []

def start_ollama():
    exe = shutil.which("ollama")
    if not exe: return False
    flags = {"creationflags": 0x08000000} if os.name == "nt" else {"start_new_session": True}
    try: subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
    except Exception: return False
    with console.status(f"[{ACC}]starting Ollama...[/]", spinner="dots12"):
        for _ in range(24):
            time.sleep(0.5)
            if fetch_models("ollama", "")[0] == "ok": return True
    return False

def local_diag(results):
    t = Table(box=box.SIMPLE, title="[dim]local servers probed[/]")
    t.add_column("Server", style="bold"); t.add_column("Address", style="dim"); t.add_column("Result")
    for pid in LOCAL:
        st, data = results.get(pid, ("fail", "not probed"))
        t.add_row(prov(pid)["label"], local_bases(pid)[0], f"[green]ok[/]" if st == "ok" else f"[red]{str(data)[-60:]}[/]")
    console.print(t)
    console.print("  [dim]Ollama → run `ollama serve` (or open the Ollama app) · LM Studio → Developer tab → Start Server\n"
                  "  Different address/port?  /local http://HOST:PORT/v1[/]")

# ═══════════════════════════════════════════════════════════════════════════
#  KEY DETECTION + VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def candidates_for(key):
    if not key: return LOCAL
    strong, weak = [], []
    for rx, pids, st in KEY_PATTERNS:
        if re.match(rx, key):
            (strong if st else weak).extend(p for p in pids if p not in strong and p not in weak)
    return strong or weak or PROBE_FALLBACK

def _probe(pid, key, base, timeout):
    kind = prov(pid)["kind"]; key = key or "x"
    try:
        if kind == "anthropic":
            r = requests.get("https://api.anthropic.com/v1/models?limit=1000", timeout=timeout,
                             headers={"x-api-key": key, "anthropic-version": "2023-06-01"})
            parse = lambda j: [m["id"] for m in j["data"]]
        elif kind == "gemini":
            r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=200", timeout=timeout)
            parse = lambda j: [m["name"].replace("models/", "") for m in j["models"]
                               if "generateContent" in m.get("supportedGenerationMethods", [])]
        elif kind == "cohere":
            r = requests.get("https://api.cohere.com/v1/models?page_size=200&endpoint=chat", timeout=timeout,
                             headers={"Authorization": f"Bearer {key}"})
            parse = lambda j: [m["name"] for m in j["models"]]
        elif kind == "ollama":
            r = requests.get(f"{base.rstrip('/')}/api/tags", timeout=timeout)
            parse = lambda j: [m["name"] for m in j["models"]]
        else:
            r = requests.get(f"{base.rstrip('/')}/models", timeout=timeout, headers={"Authorization": f"Bearer {key}"})
            parse = lambda j: [m["id"] for m in j["data"]]
        if r.status_code in (401, 403): return "auth", f"HTTP {r.status_code}"
        if r.status_code >= 400: return "fail", f"HTTP {r.status_code}"
        models = sorted(set(parse(r.json())))
        return ("ok", models) if models else ("fail", "empty model list (nothing pulled/loaded)")
    except requests.exceptions.ConnectionError: return "fail", "connection refused"
    except requests.exceptions.Timeout: return "fail", "timeout"
    except Exception as e: return "fail", str(e)[:100]

def fetch_models(pid, key, base=None, timeout=12):
    """returns (status, data)  status: ok | auth | fail.  Local providers: tries several addresses."""
    if base is None and pid in LOCAL:
        last = ("fail", "no address")
        for b in local_bases(pid):
            st, data = _probe(pid, key, b, 2.5)
            if st == "ok": FOUND_BASE[pid] = b; return st, data
            last = (st, data)
        if pid == "ollama":
            ms = ollama_cli_models()
            if ms: FOUND_BASE[pid] = local_bases(pid)[0]; return "ok", ms
        return last
    return _probe(pid, key, base or prov(pid)["base"], timeout)

def detect_and_verify(key):
    cands = candidates_for(key); results = {}
    with console.status(f"[{ACC}]{'Scanning local servers' if not key else 'Detecting provider'} · {len(cands)} candidate(s)...[/]", spinner="dots12"):
        with ThreadPoolExecutor(max_workers=min(32, len(cands))) as ex:
            futs = {ex.submit(fetch_models, pid, key): pid for pid in cands}
            for f in as_completed(futs):
                pid = futs[f]; results[pid] = f.result()
    winners = [pid for pid in cands if results.get(pid, ("",))[0] == "ok"]
    return winners, results

def choose_model(models):
    filt = ""
    while True:
        shown = [m for m in models if filt.lower() in m.lower()]
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        t.add_column(style=ACC2, justify="right"); t.add_column()
        for i, m in enumerate(shown[:40], 1): t.add_row(str(i), m)
        extra = f" (+{len(shown)-40} more — type to filter)" if len(shown) > 40 else ""
        console.print(Panel(t, title=f"[bold {ACC}]Pick a model[/] [dim]{len(shown)}/{len(models)}{extra}[/]",
                            border_style=ACC, expand=False))
        a = Prompt.ask("[bold]Number / type to filter / Enter = first[/]").strip()
        if a == "" and shown: return shown[0]
        if a.isdigit() and 1 <= int(a) <= min(40, len(shown)): return shown[int(a) - 1]
        if a in models: return a
        filt = a

def pick(title, options, labels=None):
    labels = labels or options
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(style=ACC2, justify="right"); t.add_column()
    for i, l in enumerate(labels, 1): t.add_row(str(i), l)
    console.print(Panel(t, title=f"[bold {ACC}]{title}[/]", border_style=ACC, expand=False))
    while True:
        a = Prompt.ask("[bold]Choice[/]").strip()
        if a.isdigit() and 1 <= int(a) <= len(options): return options[int(a) - 1]
        err("Invalid choice")

def set_model(pid, model):
    S.cfg["current"] = {"provider": pid, "model": model}
    S.cfg["providers"].setdefault(pid, {})["model"] = model
    _CTX_CACHE.clear(); S.cap = 0; save_cfg()

def finish_setup(pid, key, base, st, data):
    ok(f"Provider: [bold]{prov(pid)['label']}[/]" + (f"  [dim]{base}[/]" if base else ""))
    if st == "ok":
        ok(f"[bold]{len(data)}[/] models available"); model = choose_model(data)
    else:
        warn(f"Couldn't list models ({data}). Enter model name manually."); model = Prompt.ask("Model name").strip()
    S.cfg["providers"][pid] = {"key": key, "base": base}
    set_model(pid, model); S.messages.clear()
    ok(f"Ready: [bold]{prov(pid)['label']}[/] → [{ACC2}]{model}[/]")
    return True

def setup_provider(key=None):
    if key is None:
        console.print(Panel("[bold]Paste your API key[/]  [dim](any provider — auto-detected · Enter with no key = local models)[/]",
                            border_style=ACC, expand=False))
        key = Prompt.ask(f"[{ACC2}]🔑[/]", password=True).strip()
    winners, results = detect_and_verify(key)
    base = None
    if len(winners) == 1:
        pid = winners[0]
    elif len(winners) > 1:
        ok(f"Works with: {', '.join(prov(w)['label'] for w in winners)}")
        pid = pick("Which one?", winners, [prov(w)["label"] for w in winners])
    else:
        if not key:
            err("No local server responded."); local_diag(results)
            if shutil.which("ollama") and Confirm.ask("Ollama is installed but not running — start it now?", default=True):
                if start_ollama(): ok("Ollama started"); return setup_provider("")
                err("Ollama didn't come up — try `ollama serve` in another terminal")
            if Confirm.ask("Enter a local server URL manually?", default=False):
                return local_setup(Prompt.ask("URL", default="http://127.0.0.1:11434").strip())
            if Confirm.ask("Try again?", default=True): return setup_provider()
            return False
        auth_fail = [p for p, (st, _) in results.items() if st == "auth"]
        if auth_fail and len(results) <= 3:
            err(f"Invalid API key — rejected by {', '.join(prov(p)['label'] for p in auth_fail)}")
        else: err("Couldn't verify this key with any known provider.")
        if Confirm.ask("Try again?", default=True): return setup_provider()
        if not Confirm.ask("Pick provider manually instead?", default=False): return False
        ids = list(PROVIDERS)
        pid = pick("Provider", ids, [PROVIDERS[i]["label"] for i in ids])
        if pid == "custom" or Confirm.ask("Custom base URL?", default=False):
            base = Prompt.ask("Base URL", default=PROVIDERS[pid]["base"] or "http://127.0.0.1:8000/v1").strip()
        with console.status(f"[{ACC}]Verifying...[/]", spinner="dots12"):
            results[pid] = fetch_models(pid, key, base)
    st, data = results[pid]
    return finish_setup(pid, key, base or FOUND_BASE.get(pid), st, data)

def local_setup(url):
    base = url.rstrip("/"); pid = "custom"
    if ":11434" in base:
        pid = "ollama"; base = base[:-3] if base.endswith("/v1") else base
    with console.status(f"[{ACC}]probing {base}...[/]", spinner="dots12"): st, data = fetch_models(pid, "", base)
    if st != "ok": err(f"{base}: {data}"); return False
    return finish_setup(pid, "", base, st, data)

def scan_local():
    winners, results = detect_and_verify("")
    if not winners: err("No local server responded."); local_diag(results); return False
    pid = winners[0] if len(winners) == 1 else pick("Local server", winners,
          [f"{prov(w)['label']}  [dim]{FOUND_BASE.get(w)} · {len(results[w][1])} models[/]" for w in winners])
    return finish_setup(pid, "", FOUND_BASE.get(pid), *results[pid])

# ═══════════════════════════════════════════════════════════════════════════
#  TOOLS
# ═══════════════════════════════════════════════════════════════════════════
MAX_OUT = 12000
IGNORE = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", ".idea", ".vscode", ".mypy_cache"}
def _clip(s): return s if len(s) <= MAX_OUT else s[:MAX_OUT] + f"\n...[{len(s)-MAX_OUT} chars truncated]"

def t_read_file(path):
    p = Path(path)
    return _clip(p.read_text(errors="replace")) if p.is_file() else f"ERROR: no such file: {path}"

def t_write_file(path, content):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    if p.is_file(): show_diff(p.read_text(errors="replace"), content, path)
    p.write_text(content); return f"wrote {path} ({len(content)} chars)"

def t_edit_file(path, old, new):
    p = Path(path)
    if not p.is_file(): return f"ERROR: no such file: {path}"
    s = p.read_text(errors="replace")
    if s.count(old) == 0: return "ERROR: 'old' text not found (must match exactly)"
    if s.count(old) > 1: return f"ERROR: 'old' appears {s.count(old)} times, be more specific"
    ns = s.replace(old, new, 1); show_diff(s, ns, path); p.write_text(ns); return f"edited {path}"

def t_list_dir(path="."):
    p = Path(path)
    if not p.is_dir(): return f"ERROR: no such directory: {path}"
    items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    return _clip("\n".join(("📁 " if x.is_dir() else "   ") + x.name for x in items if x.name != ".git"))

def t_tree(path=".", depth=3):
    out = []
    def walk(p, pre, d):
        if d > depth or len(out) > 300: return
        try: items = sorted([x for x in p.iterdir() if x.name not in IGNORE and not x.name.startswith(".")],
                            key=lambda x: (not x.is_dir(), x.name))
        except Exception: return
        for i, x in enumerate(items):
            last = i == len(items) - 1
            out.append(f"{pre}{'└── ' if last else '├── '}{x.name}{'/' if x.is_dir() else ''}")
            if x.is_dir(): walk(x, pre + ("    " if last else "│   "), d + 1)
    if not Path(path).is_dir(): return f"ERROR: no such directory: {path}"
    walk(Path(path), "", 1); return _clip("\n".join(out) or "(empty)")

def t_search(pattern, path=".", glob="*"):
    out, rx = [], re.compile(pattern, re.I)
    for f in Path(path).rglob(glob):
        if f.is_file() and not (set(f.parts) & IGNORE) and f.stat().st_size < 2_000_000:
            try:
                for i, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                    if rx.search(line): out.append(f"{f}:{i}: {line.strip()[:200]}")
            except Exception: pass
            if len(out) > 300: break
    return _clip("\n".join(out) or "no matches")

def t_run_shell(command):
    if not S.yolo:
        console.print(Panel(Text(command, style="bold yellow"), title="[bold red]⚠ run this command?[/]",
                            border_style="red", expand=False))
        if not Confirm.ask("Allow", default=False): return "USER DENIED"
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        return _clip(f"exit={r.returncode}\n{r.stdout}\n{r.stderr}".strip())
    except subprocess.TimeoutExpired: return "ERROR: timeout (120s)"

TOOL_FUNCS = {"read_file": t_read_file, "write_file": t_write_file, "edit_file": t_edit_file,
              "list_dir": t_list_dir, "tree": t_tree, "search": t_search, "run_shell": t_run_shell}

def _tool(name, desc, props, req):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": req}}}
STR, INT = {"type": "string"}, {"type": "integer"}
TOOLS = [
    _tool("read_file", "Read a file", {"path": STR}, ["path"]),
    _tool("write_file", "Create or overwrite a file", {"path": STR, "content": STR}, ["path", "content"]),
    _tool("edit_file", "Replace exact 'old' text with 'new' in a file", {"path": STR, "old": STR, "new": STR}, ["path", "old", "new"]),
    _tool("list_dir", "List a directory", {"path": STR}, []),
    _tool("tree", "Show directory tree (default depth 3)", {"path": STR, "depth": INT}, []),
    _tool("search", "Regex search across files (grep)", {"pattern": STR, "path": STR, "glob": STR}, ["pattern"]),
    _tool("run_shell", "Run a shell command (requires user approval)", {"command": STR}, ["command"]),
]
READ_TOOLS = [t for t in TOOLS if t["function"]["name"] in ("read_file", "list_dir", "tree", "search")]
def active_tools(): return READ_TOOLS if S.cfg["mode"] == "plan" else TOOLS

def exec_tool(name, args):
    icon = {"read_file": "📖", "write_file": "✏️ ", "edit_file": "🔧", "list_dir": "📁", "tree": "🌳",
            "search": "🔍", "run_shell": "💻"}.get(name, "🛠")
    console.print(f"  [dim]{icon} {name}[/] [{ACC2}]{json.dumps(args, ensure_ascii=False)[:120]}[/]")
    try: return TOOL_FUNCS[name](**args)
    except Exception as e: return f"ERROR: {e}"

# ═══════════════════════════════════════════════════════════════════════════
#  THINK MODE / SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════
THINK_PROMPT = {
    3: "Think briefly before answering.",
    4: "Think step by step in detail before answering; question your assumptions.",
    5: "Think deeply before answering: decompose the problem, compare alternatives, "
       "critique your own answer and fix it. Only then give the final answer.",
}
def think_params():
    lvl = S.cfg["thinkmode"]
    if lvl <= 1: return {}, ""
    try: native = litellm.supports_reasoning(model=lm_kwargs()["model"])
    except Exception: native = False
    if native:
        return {"reasoning_effort": {2: "low", 3: "medium", 4: "high", 5: "high"}[lvl]}, (THINK_PROMPT[5] if lvl == 5 else "")
    return {}, THINK_PROMPT.get(lvl, THINK_PROMPT[3])

def system_prompt(extra=""):
    mode = ("PLAN MODE: you only have read-only tools. Analyse and propose a concrete plan; do NOT claim to have edited files."
            if S.cfg["mode"] == "plan" else
            "Use tools (read/write/edit files, tree, search, shell) when needed; always read a file before editing it.")
    lang = f"Always reply in {S.cfg['lang']}." if S.cfg.get("lang") else "Reply in the user's language."
    parts = [f"You are Mamo Code v{VERSION}, an expert software engineering assistant running in a terminal.",
             f"Working directory: {os.getcwd()}.", mode, "Be concise and technical.", lang,
             S.cfg.get("system_extra", ""), extra]
    return " ".join(p for p in parts if p).strip()

# ═══════════════════════════════════════════════════════════════════════════
#  AGENT CORE
# ═══════════════════════════════════════════════════════════════════════════
def _msg_to_dict(m):
    d = {"role": "assistant", "content": m.content or ""}
    if m.tool_calls:
        d["tool_calls"] = [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in m.tool_calls]
    return d

def _cap_from_error(s):
    for rx in (r"can only afford (\d+)", r"afford (\d+)", r"> (\d+), which is the maximum", r"maximum (?:of )?(\d+) (?:output |completion )?tokens",
               r"supports at most (\d+)", r"limit of (\d+)", r"max_tokens[^\d]{0,30}(\d{3,6})"):
        m = re.search(rx, s)
        if m: return int(m.group(1))
    return 0

def stream_completion(messages, tools, extra):
    kw = dict(lm_kwargs(stream=True), messages=messages, **extra)
    if tools: kw["tools"] = tools
    text = think = ""; chunks = []; t0 = time.time(); pid = cur()[0]
    for attempt in range(8):
        chunks, text, think = [], "", ""
        try:
            with Live(Spinner("dots", text=Text(" thinking...", style=ACC)), console=console,
                      refresh_per_second=12, transient=True) as live:
                for ch in litellm.completion(**kw):
                    chunks.append(ch)
                    if not ch.choices: continue
                    d = ch.choices[0].delta
                    rc = getattr(d, "reasoning_content", None)
                    if rc: think += rc
                    if d.content: text += d.content
                    if text: live.update(Panel(Markdown(text), border_style=ACC, title="[bold]mamo[/]", title_align="left"))
                    elif think: live.update(Spinner("dots", text=Text(f" 💭 reasoning ({len(think)} chars)", style="dim")))
            break
        except KeyboardInterrupt: raise
        except Exception as e:
            s = str(e); sl = s.lower(); mt = int(kw.get("max_tokens") or 0)
            # ── credits / quota ──────────────────────────────────────────
            if "afford" in sl or "credits" in sl or "insufficient_quota" in sl or "insufficient balance" in sl or "402" in sl:
                cap = _cap_from_error(sl)
                if cap >= 64 and (not mt or cap < mt):
                    S.cap = max(64, int(cap * 0.9)); kw["max_tokens"] = S.cap
                    warn(f"low credits on {prov(pid)['label']} → output capped at [bold]{S.cap}[/] tokens this session. "
                         f"Add credits or pick a free model ([bold]/models free[/]).")
                    continue
                raise RuntimeError(f"{prov(pid)['label']} rejected the request: out of credits/quota. "
                                   f"Top up, or switch to a free/local model (/models free · /local). Detail: {s[:200]}")
            # ── context overflow ─────────────────────────────────────────
            if any(k in sl for k in CTX_ERR): raise CtxError(s[:200])
            # ── output token limit ───────────────────────────────────────
            if "max_tokens" in sl or "max_completion_tokens" in sl or "output tokens" in sl or "max_new_tokens" in sl:
                cap = _cap_from_error(sl)
                new = int(cap * 0.95) if cap and (not mt or cap < mt) else (mt or 8192) // 2
                if new < 256: raise
                kw["max_tokens"] = new; S.cap = new
                warn(f"max_tokens {mt or 'default'} → {new} (model/provider limit)"); continue
            # ── capability fallbacks ─────────────────────────────────────
            if "reasoning" in sl and "reasoning_effort" in kw: kw.pop("reasoning_effort"); warn("reasoning not supported → plain mode"); continue
            if "stream_options" in sl and "stream_options" in kw: kw.pop("stream_options"); continue
            if "usage" in sl and "extra_body" in kw: kw.pop("extra_body"); continue
            if ("tool" in sl or "function" in sl) and "tools" in kw: kw.pop("tools"); warn("this model doesn't support tools → chat only"); continue
            if "temperature" in sl and "temperature" in kw: kw.pop("temperature"); warn("temperature not supported by this model"); continue
            # ── rate limit → backoff ─────────────────────────────────────
            if ("429" in sl or "rate limit" in sl or "rate_limit" in sl or "overloaded" in sl or "503" in sl) and attempt < 4:
                wait = 2 * (2 ** attempt); warn(f"rate limited / busy → retrying in {wait}s"); time.sleep(wait); continue
            # ── litellm native prefix unknown → generic openai mode ──────
            if pid in LM_PREFIX and not kw["model"].startswith("openai/") and ("llm provider not provided" in sl or "not a valid provider" in sl or "unmapped" in sl):
                kw["model"] = "openai/" + cur()[1]; kw["api_base"] = cur()[3] or prov(pid)["base"]; continue
            raise
    if think:
        console.print(Panel(Text(think[:600] + ("..." if len(think) > 600 else ""), style="dim italic"),
                            title=f"[dim]💭 reasoning · {len(think)} chars[/]", border_style="grey37", expand=False))
    if text:
        console.print(Panel(Markdown(text), border_style=ACC, title="[bold]mamo[/]", title_align="left",
                            subtitle=f"[dim]{time.time()-t0:.1f}s[/]", subtitle_align="right"))
    try: resp = litellm.stream_chunk_builder(chunks, messages=messages)
    except Exception:
        class _R: pass
        resp = _R(); resp.usage = None
        resp.choices = [type("c", (), {"message": type("m", (), {"content": text, "tool_calls": None})()})()]
    return resp, text

def run_agent(messages, tools, extra, max_steps=25):
    text = ""
    for _ in range(max_steps):
        resp, text = stream_completion(messages, tools, extra); _track(resp, messages, text)
        m = resp.choices[0].message; messages.append(_msg_to_dict(m))
        if not m.tool_calls: return text
        for tc in m.tool_calls:
            try: args = json.loads(tc.function.arguments or "{}")
            except Exception: args = {}
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name,
                             "content": exec_tool(tc.function.name, args)})
        prune_tool_outputs(messages)
    warn("step limit reached"); return text

# ═══════════════════════════════════════════════════════════════════════════
#  MULTI MODE
# ═══════════════════════════════════════════════════════════════════════════
ROLES = [
    ("Architect", "Analyze structure, design and overall approach; propose the best solution plan."),
    ("Reviewer", "Find bugs, edge cases, security and performance risks; be skeptical."),
    ("Implementer", "Produce a concrete step-by-step implementation plan: which files change and how."),
]

def worker(role, desc, task, context, extra, status):
    status[role] = "working"
    msgs = [{"role": "system", "content": system_prompt(f"You are a team member, role: {role}. {desc} "
             "You only have read-only tools. Write a short, focused analysis report.")},
            {"role": "user", "content": f"Context:\n{context}\n\nTask: {task}"}]
    try:
        for _ in range(8):
            r = litellm.completion(**lm_kwargs(), messages=msgs, tools=READ_TOOLS, **extra)
            _track(r, msgs); m = r.choices[0].message; msgs.append(_msg_to_dict(m))
            if not m.tool_calls: status[role] = "done"; return m.content or ""
            for tc in m.tool_calls:
                try: args = json.loads(tc.function.arguments or "{}")
                except Exception: args = {}
                try: res = TOOL_FUNCS[tc.function.name](**args)
                except Exception as e: res = f"ERROR: {e}"
                status[role] = tc.function.name
                msgs.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": res})
            prune_tool_outputs(msgs, keep=4)
        status[role] = "done"; return msgs[-1].get("content", "")
    except Exception as e:
        status[role] = "error"; return f"[{role} error: {e}]"

def multi_run(task, extra):
    n = S.cfg["multimode"]; roles = ROLES[:n]
    context = "\n".join(f"{m['role']}: {str(m.get('content',''))[:400]}" for m in S.messages[-6:] if m["role"] in ("user", "assistant"))
    status = {r: "waiting" for r, _ in roles}
    def render():
        t = Table(box=box.ROUNDED, border_style=ACC2, title=f"[bold {ACC2}]⚡ {n} agents in parallel[/]")
        t.add_column("Agent", style="bold"); t.add_column("Status")
        for r, st in status.items():
            t.add_row(r, f"[{ {'done': 'green', 'error': 'red', 'waiting': 'dim'}.get(st, 'yellow') }]{st}[/]")
        return t
    with ThreadPoolExecutor(max_workers=n) as ex, Live(render(), console=console, refresh_per_second=6, transient=True) as live:
        futs = {r: ex.submit(worker, r, d, task, context, extra, status) for r, d in roles}
        while not all(f.done() for f in futs.values()): live.update(render()); time.sleep(0.2)
    reports = {r: f.result() for r, f in futs.items()}
    for r, rep in reports.items():
        console.print(Panel(Markdown(rep[:1500] + ("…" if len(rep) > 1500 else "")), title=f"[bold {ACC2}]{r}[/]",
                            border_style="grey37", expand=False))
    return "\n\n".join(f"### {r} report\n{rep}" for r, rep in reports.items())

# ═══════════════════════════════════════════════════════════════════════════
#  SKILLS
# ═══════════════════════════════════════════════════════════════════════════
SKILLS = {
    "review":   ("Code review", "Review this; list bugs, risks and improvements by priority: {a}"),
    "fix":      ("Find & fix a bug", "Investigate this problem, find the root cause and fix it: {a}"),
    "test":     ("Write tests", "Write thorough unit tests for {a} and save them to an appropriate file."),
    "refactor": ("Refactor", "Refactor {a} to be cleaner and more readable without changing behavior."),
    "explain":  ("Explain", "What does {a} do? Explain the architecture and flow."),
    "docs":     ("Documentation", "Write docstrings / README documentation for {a}."),
    "commit":   ("Commit message", "Run git diff and git status, summarize changes, propose a conventional commit message."),
    "init":     ("Explore project", "Explore this project (tree, main files, dependencies) and write a short summary."),
    "security": ("Security audit", "Audit {a} for security vulnerabilities (injection, auth, secrets, unsafe deps); rank by severity and propose fixes."),
    "perf":     ("Performance", "Analyze {a} for performance problems; identify hotspots and propose concrete optimizations."),
    "types":    ("Add types", "Add complete, accurate type annotations to {a}."),
    "todo":     ("TODO scan", "Find all TODO/FIXME/HACK comments in {a}, prioritize them and propose a plan."),
    "pr":       ("PR description", "Run git diff against the main/master branch and write a pull-request title and description."),
    "migrate":  ("Migrate / upgrade", "Plan and perform this migration or upgrade carefully, step by step: {a}"),
    "deps":     ("Dependencies", "Analyze the project's dependencies (outdated, vulnerable, unused) and propose updates."),
    "ci":       ("CI pipeline", "Create a CI workflow (GitHub Actions) that lints, tests and builds {a}."),
    "docker":   ("Dockerize", "Write a production-ready Dockerfile (and compose file if useful) for {a}."),
}

# ═══════════════════════════════════════════════════════════════════════════
#  SESSIONS / CLIPBOARD
# ═══════════════════════════════════════════════════════════════════════════
def save_session(name):
    SESS_DIR.mkdir(parents=True, exist_ok=True); pid, model, _, _ = cur()
    (SESS_DIR / f"{name}.json").write_text(json.dumps({
        "messages": S.messages, "cwd": os.getcwd(), "provider": pid, "model": model, "ts": time.time(),
        "cost": S.cost, "tin": S.tin, "tout": S.tout}, ensure_ascii=False))

def load_session(name):
    f = SESS_DIR / f"{name}.json"
    if not f.exists(): return None
    d = json.loads(f.read_text()); S.messages[:] = d.get("messages", []); fix_dangling(S.messages)
    if d.get("cwd") and Path(d["cwd"]).is_dir(): os.chdir(d["cwd"])
    return d

def list_sessions():
    if not SESS_DIR.exists(): return []
    return sorted(SESS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

def to_clipboard(text):
    try:
        import pyperclip; pyperclip.copy(text); return True
    except Exception: pass
    for cmd in (["pbcopy"], ["xclip", "-selection", "clipboard"], ["wl-copy"], ["clip"]):
        if shutil.which(cmd[0]):
            try: subprocess.run(cmd, input=text.encode(), check=True); return True
            except Exception: pass
    return False

def last_assistant():
    return next((m["content"] for m in reversed(S.messages) if m["role"] == "assistant" and m.get("content")), "")

# ═══════════════════════════════════════════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════════════════════════════════════════
HELP = f"""
[bold {ACC}]Model & provider[/]
  /model              switch model             /models [filter]   list models (e.g. /models free)
  /provider           switch saved provider    /key               add API key (auto-detected)
  /local [url]        scan / add local server  /keys [rm <id>]    list / remove saved keys
  /credits            OpenRouter balance
[bold {ACC}]Behaviour[/]
  /mode plan|build    plan = read-only tools   /thinkmode 1-5     reasoning depth
  /multimode 1-3      parallel agents          /maxtokens N|off   max output tokens
  /temp N|off         temperature              /lang <lang>|off   force reply language
  /system <text>|clear  extra system prompt    /yolo              shell without confirmation
[bold {ACC}]Context & tokens[/]
  /context [N]        usage (N = set limit)    /compact [auto]    summarize history / toggle auto
  /add <file|glob>    attach file to next msg  /undo              drop last turn
  /retry              resend last message      /clear             reset chat
[bold {ACC}]Session & output[/]
  /save [name]   /load [name]   /sessions   /export [file.md]   /copy
[bold {ACC}]Project & misc[/]
  /tree [dir]  /git  /diff [args]  /cd <dir>  /skills  /config  /stats  /cost  /debug  /changelog  /version  /exit
[bold {ACC2}]!command[/]   run shell directly      [dim]end a line with \\ for multi-line input[/]
"""
CMDS = ["/model", "/models", "/provider", "/key", "/keys", "/local", "/credits", "/mode", "/thinkmode", "/multimode",
        "/maxtokens", "/temp", "/lang", "/system", "/yolo", "/context", "/compact", "/add", "/undo", "/retry", "/clear",
        "/save", "/load", "/sessions", "/export", "/copy", "/tree", "/git", "/diff", "/cd", "/skills", "/config", "/stats",
        "/cost", "/debug", "/changelog", "/version", "/help", "/exit"] + [f"/{k}" for k in SKILLS]

def handle_command(line):
    parts = line.strip().split(maxsplit=1)
    cmd, arg = parts[0].lower(), (parts[1].strip() if len(parts) > 1 else "")
    if cmd in ("/exit", "/quit", "/q"): raise SystemExit
    elif cmd == "/help": console.print(Panel(HELP.strip(), title="[bold]Commands[/]", border_style=ACC, expand=False))
    elif cmd == "/version": console.print(f"  Mamo Code V2.3 · v{VERSION} · litellm {getattr(litellm, '__version__', '?')}")
    elif cmd == "/changelog":
        if arg.lower() in ("off", "on"): S.cfg["show_changelog"] = arg.lower() == "on"; save_cfg(); ok(f"startup changelog {arg.lower()}")
        else: show_changelog(full=True)
    elif cmd == "/clear": S.messages.clear(); S.attach.clear(); console.clear(); ok("chat cleared")
    elif cmd == "/cost": console.print(f"  [bold]${S.cost:.4f}[/] · in {S.tin:,} · out {S.tout:,} · total {S.tin+S.tout:,} tokens")
    elif cmd == "/stats":
        up = (time.time() - S.t_start) / 60
        console.print(f"  requests [bold]{S.requests}[/] · in [bold]{S.tin:,}[/] · out [bold]{S.tout:,}[/] tok · "
                      f"${S.cost:.4f} · {up:.1f} min · {len(S.messages)} messages · {len(S.attach)} attached"
                      + (f" · output cap {S.cap}" if S.cap else ""))
    elif cmd == "/yolo": S.yolo = not S.yolo; warn(f"YOLO {'ON — commands run without confirmation!' if S.yolo else 'off'}")
    elif cmd == "/debug":
        on = not getattr(litellm, "set_verbose", False); litellm.set_verbose = on
        logging.disable(logging.NOTSET if on else logging.CRITICAL); os.environ["LITELLM_LOG"] = "DEBUG" if on else "ERROR"
        warn(f"debug {'on' if on else 'off'}")
    elif cmd == "/cd":
        try: os.chdir(os.path.expanduser(arg or "~")); ok(os.getcwd())
        except Exception as e: err(e)
    # ── behaviour ──────────────────────────────────────────────────────
    elif cmd == "/mode":
        m = arg.lower() or ("build" if S.cfg["mode"] == "plan" else "plan")
        if m not in ("plan", "build"): err("usage: /mode plan|build"); return
        S.cfg["mode"] = m; save_cfg()
        console.print(f"  {'🗺️  PLAN mode — read-only tools, no edits' if m == 'plan' else '🔨 BUILD mode — full tools'}")
    elif cmd == "/thinkmode":
        if arg.isdigit() and 1 <= int(arg) <= 5:
            S.cfg["thinkmode"] = int(arg); save_cfg()
            console.print(f"  🧠 think mode → [bold {ACC}]{'●' * int(arg)}{'○' * (5 - int(arg))}[/] {arg}/5")
        else: err("usage: /thinkmode 1-5")
    elif cmd == "/multimode":
        if arg.isdigit() and 1 <= int(arg) <= 3:
            S.cfg["multimode"] = int(arg); save_cfg()
            console.print(f"  ⚡ multi mode → [bold {ACC2}]{arg}[/] agent(s) " +
                          ("(single)" if arg == "1" else "(" + ", ".join(r for r, _ in ROLES[:int(arg)]) + " + synthesis)"))
        else: err("usage: /multimode 1-3")
    elif cmd == "/maxtokens":
        S.cap = 0
        if arg.lower() in ("off", "0"): S.cfg["max_tokens"] = 0; save_cfg(); ok("max_tokens → provider default")
        elif arg.isdigit(): S.cfg["max_tokens"] = int(arg); save_cfg(); ok(f"max_tokens → {arg}")
        else: console.print(f"  max_tokens = {S.cfg['max_tokens'] or 'provider default'}   [dim]/maxtokens N|off[/]")
    elif cmd == "/temp":
        if arg.lower() == "off": S.cfg["temperature"] = None; save_cfg(); ok("temperature → default")
        else:
            try: S.cfg["temperature"] = float(arg); save_cfg(); ok(f"temperature → {arg}")
            except ValueError: console.print(f"  temperature = {S.cfg['temperature'] if S.cfg['temperature'] is not None else 'default'}   [dim]/temp 0.7 | off[/]")
    elif cmd == "/lang":
        S.cfg["lang"] = "" if arg.lower() in ("off", "") else arg; save_cfg()
        ok(f"reply language → {S.cfg['lang'] or 'auto'}")
    elif cmd == "/system":
        if arg.lower() == "clear": S.cfg["system_extra"] = ""; save_cfg(); ok("extra system prompt cleared")
        elif arg: S.cfg["system_extra"] = arg; save_cfg(); ok("extra system prompt set")
        else: console.print(f"  system_extra: {S.cfg['system_extra'] or '(none)'}")
    # ── context & tokens ───────────────────────────────────────────────
    elif cmd == "/context":
        if arg.isdigit(): S.cfg["ctx_limit"] = int(arg); save_cfg(); ok(f"context limit → {arg}")
        elif arg.lower() in ("auto", "off"): S.cfg["ctx_limit"] = 0; save_cfg(); _CTX_CACHE.clear(); ok("context limit → auto")
        lim = ctx_limit(); used = est_tokens(S.messages); pct = min(100, used * 100 // max(lim, 1))
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5); color = "green" if pct < 60 else "yellow" if pct < 85 else "red"
        console.print(f"  [{color}]{bar}[/] {pct}%  ·  ~{used:,} / {lim:,} tokens  ·  {len(S.messages)} messages  ·  "
                      f"autocompact {'on' if S.cfg['autocompact'] else 'off'}")
        console.print("  [dim]/compact to summarize · /undo drop last turn · /context N to set limit manually[/]")
    elif cmd == "/compact":
        if arg.lower() == "auto":
            S.cfg["autocompact"] = not S.cfg["autocompact"]; save_cfg(); ok(f"autocompact {'on' if S.cfg['autocompact'] else 'off'}")
        else: compact(force=True)
    elif cmd == "/add":
        if not arg: err("usage: /add <file|glob>"); return
        files = list(Path().glob(arg)) if any(c in arg for c in "*?[") else [Path(os.path.expanduser(arg))]
        n = 0
        for f in files:
            if f.is_file(): S.attach.append((str(f), t_read_file(str(f)))); n += 1
        if n: ok(f"attached {n} file(s) → included in your next message")
        else: err("no such file")
    elif cmd == "/undo":
        if undo(): ok(f"last turn removed · {len(S.messages)} messages left")
        else: warn("nothing to undo")
    elif cmd == "/retry":
        if not S.last_user: warn("nothing to retry"); return
        undo(); return S.last_user
    # ── sessions & output ──────────────────────────────────────────────
    elif cmd == "/save": save_session(arg or "last"); ok(f"session saved → {arg or 'last'}")
    elif cmd == "/load":
        name = arg
        if not name:
            ss = list_sessions()
            if not ss: warn("no saved sessions"); return
            name = pick("Session", [s.stem for s in ss],
                        [f"{s.stem}  [dim]{datetime.fromtimestamp(s.stat().st_mtime):%Y-%m-%d %H:%M}[/]" for s in ss])
        d = load_session(name)
        if d: ok(f"loaded '{name}' · {len(S.messages)} messages · {d.get('provider')}/{d.get('model')} · cwd {os.getcwd()}")
        else: err(f"no session named '{name}'")
    elif cmd == "/sessions":
        ss = list_sessions()
        if not ss: warn("no saved sessions"); return
        t = Table(box=box.SIMPLE); t.add_column("Name", style=ACC); t.add_column("Date"); t.add_column("Msgs"); t.add_column("Model")
        for s in ss:
            try: d = json.loads(s.read_text()); t.add_row(s.stem, f"{datetime.fromtimestamp(s.stat().st_mtime):%Y-%m-%d %H:%M}", str(len(d.get("messages", []))), str(d.get("model", "")))
            except Exception: t.add_row(s.stem, "?", "?", "?")
        console.print(Panel(t, title="[bold]Sessions[/]  [dim]/load <name>[/]", border_style=ACC, expand=False))
    elif cmd == "/export":
        fn = arg or f"mamo-{datetime.now():%Y%m%d-%H%M%S}.md"
        lines = [f"# Mamo Code session · {datetime.now():%Y-%m-%d %H:%M}", ""]
        for m in S.messages[1:]:
            if m["role"] in ("user", "assistant") and m.get("content"):
                lines += [f"## {'👤 You' if m['role'] == 'user' else '🤖 Mamo'}", "", str(m["content"]), ""]
        Path(fn).write_text("\n".join(lines)); ok(f"exported → {fn}")
    elif cmd == "/copy":
        txt = last_assistant()
        if not txt: warn("nothing to copy")
        elif to_clipboard(txt): ok(f"copied {len(txt)} chars to clipboard")
        else: err("no clipboard tool found (pip install pyperclip)")
    # ── project ────────────────────────────────────────────────────────
    elif cmd == "/tree": console.print(Text(t_tree(arg or ".", 3), style="dim"))
    elif cmd == "/git":
        console.print(Panel(Text(sh("git status -sb && echo && git log --oneline -8") or "not a git repo", style="dim"),
                            title="[bold]git[/]", border_style=ACC, expand=False))
    elif cmd == "/diff":
        d = sh(f"git diff --stat {arg} && echo && git diff {arg}")
        if not d: warn("no changes"); return
        console.print(Syntax(d[:8000] + ("\n... (truncated)" if len(d) > 8000 else ""), "diff", theme="ansi_dark", word_wrap=True))
    elif cmd == "/skills":
        t = Table(box=box.SIMPLE); t.add_column("Command", style=ACC); t.add_column("Description")
        for k, (d, _) in SKILLS.items(): t.add_row(f"/{k}", d)
        console.print(Panel(t, title="[bold]Skills[/]", border_style=ACC, expand=False))
    elif cmd == "/config":
        t = Table(box=box.SIMPLE, show_header=False); t.add_column(style=ACC); t.add_column()
        for k, v in S.cfg.items():
            if k != "providers": t.add_row(k, json.dumps(v, ensure_ascii=False))
        t.add_row("config file", str(CONFIG_FILE))
        console.print(Panel(t, title="[bold]Config[/]", border_style=ACC, expand=False))
    # ── providers ──────────────────────────────────────────────────────
    elif cmd == "/key": setup_provider()
    elif cmd == "/local":
        if arg: local_setup(arg)
        else: scan_local()
    elif cmd == "/credits":
        pid, _, key, _ = cur()
        if pid != "openrouter": warn(f"balance lookup is OpenRouter-only for now · this session: ${S.cost:.4f}"); return
        try:
            with console.status(f"[{ACC}]fetching balance...[/]", spinner="dots12"):
                d = requests.get("https://openrouter.ai/api/v1/credits", timeout=10,
                                 headers={"Authorization": f"Bearer {key}"}).json()["data"]
            tot, used = float(d.get("total_credits", 0)), float(d.get("total_usage", 0))
            console.print(f"  OpenRouter: total [bold]${tot:.2f}[/] · used ${used:.4f} · remaining [bold green]${tot-used:.4f}[/]"
                          + ("   [yellow]→ low! try /models free[/]" if tot - used < 0.5 else ""))
        except Exception as e: err(f"couldn't fetch credits: {str(e)[:120]}")
    elif cmd == "/keys":
        if arg.startswith("rm"):
            pid = arg[2:].strip()
            if pid in S.cfg["providers"]:
                S.cfg["providers"].pop(pid)
                if S.cfg["current"].get("provider") == pid: S.cfg["current"] = {}
                save_cfg(); ok(f"removed {pid}")
                if not S.cfg["current"]: setup_provider()
            else: err(f"'{pid}' not saved")
        else:
            t = Table(box=box.SIMPLE); t.add_column("id", style=ACC); t.add_column("Provider"); t.add_column("Key / base"); t.add_column("Last model")
            for pid, p in S.cfg["providers"].items():
                k = p.get("key") or ""
                t.add_row(pid, prov(pid)["label"], (k[:6] + "…" + k[-4:]) if len(k) > 12 else (p.get("base") or "(local)" if not k else "***"), p.get("model") or "")
            console.print(Panel(t, title="[bold]Saved keys[/]  [dim]/keys rm <id>[/]", border_style=ACC, expand=False))
    elif cmd == "/provider":
        ids = list(S.cfg["providers"])
        if len(ids) < 2: warn("only one provider saved — add another with /key or /local"); return
        pid = pick("Provider", ids, [prov(i)["label"] for i in ids])
        S.cfg["current"]["provider"] = pid; saved = S.cfg["providers"][pid].get("model")
        if saved and Confirm.ask(f"Use saved model [{saved}]?", default=True): set_model(pid, saved); ok(f"{prov(pid)['label']} → [{ACC2}]{saved}[/]")
        else: handle_command("/model")
    elif cmd == "/model":
        pid, _, key, base = cur()
        with console.status(f"[{ACC}]fetching models...[/]", spinner="dots12"): st, data = fetch_models(pid, key, base)
        model = choose_model(data) if st == "ok" else Prompt.ask("Model name").strip()
        set_model(pid, model); ok(f"model → [{ACC2}]{model}[/]")
    elif cmd == "/models":
        pid, _, key, base = cur()
        with console.status(f"[{ACC}]fetching models...[/]", spinner="dots12"): st, data = fetch_models(pid, key, base)
        if st != "ok": err(f"couldn't list models: {data}"); return
        shown = [m for m in data if arg.lower() in m.lower()]
        console.print(Panel(Text("\n".join(shown[:80]) + (f"\n... +{len(shown)-80} more" if len(shown) > 80 else ""), style="dim"),
                            title=f"[bold]{prov(pid)['label']}[/] · {len(shown)}/{len(data)} models", border_style=ACC, expand=False))
    elif cmd[1:] in SKILLS:
        return SKILLS[cmd[1:]][1].format(a=arg or "this project")
    else: err(f"unknown command: {cmd}  (try /help)")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════
def chat(user_text, _retry=False):
    S.last_user = user_text
    fix_dangling(S.messages)
    if S.cfg.get("autocompact", True) and S.messages: compact()
    extra, hint = think_params()
    sysmsg = {"role": "system", "content": system_prompt(hint)}
    if not S.messages: S.messages.append(sysmsg)
    else: S.messages[0] = sysmsg
    content = user_text
    if S.attach:
        content = "\n\n".join(f'<file path="{p}">\n{c}\n</file>' for p, c in S.attach) + "\n\n" + content; S.attach.clear()
    if S.cfg["multimode"] > 1:
        reports = multi_run(user_text, extra)
        content = (f"{content}\n\n---\nYour team's parallel analysis reports are below. Synthesize them, resolve "
                   f"conflicts, and apply changes with tools if appropriate:\n{reports}")
    S.messages.append({"role": "user", "content": content})
    try: run_agent(S.messages, active_tools(), extra)
    except CtxError as e:
        warn(f"context window exceeded ({str(e)[:80]})"); undo()
        if not _retry and compact(force=True): chat(user_text, _retry=True)
        else: err("still too large — try /clear, /context N, or a model with a bigger context window")
    except KeyboardInterrupt: warn("cancelled"); fix_dangling(S.messages)
    except Exception as e:
        err(f"API error: {str(e)[:500]}"); undo()

def read_input(session):
    buf = []
    while True:
        if HAS_PT:
            line = session.prompt(HTML(f'<style fg="{ACC}"><b>mamo</b></style> <style fg="{ACC2}">❯</style> ')
                                  if not buf else HTML('<style fg="#888888">  ...</style> '))
        else: line = input("mamo ❯ " if not buf else "  ... ")
        if line.endswith("\\"): buf.append(line[:-1]); continue
        buf.append(line); return "\n".join(buf)

def main():
    load_cfg(); banner()
    if S.cfg.get("show_changelog", True): show_changelog()
    if not S.cfg.get("current") or not S.cfg["current"].get("model"):
        if not setup_provider(): return
    session = PromptSession(completer=WordCompleter(CMDS, sentence=True)) if HAS_PT else None
    console.print(Panel(f"[bold]Welcome to Mamo Code V2.3![/] Ask anything, let me edit files, or type [bold {ACC}]/help[/]. "
                        f"[dim]· /mode plan for read-only · /local for Ollama & co · /load to resume[/]", border_style=ACC2, expand=False))
    while True:
        status_bar()
        try: line = read_input(session).strip()
        except (EOFError, KeyboardInterrupt): break
        if not line: continue
        try:
            if line.startswith("!"):
                out = sh(line[1:]); console.print(Text(out or "(no output)", style="dim"))
            elif line.startswith("/"):
                prompt = handle_command(line)
                if prompt: chat(prompt)
            else: chat(line)
        except SystemExit: break
        except KeyboardInterrupt: warn("cancelled")
        console.print()
    if len(S.messages) > 1:
        try: save_session("last")
        except Exception: pass
    console.print(f"[dim]bye 👋 · ${S.cost:.4f} · {S.tin+S.tout:,} tokens · session autosaved as 'last' (/load)[/]")

if __name__ == "__main__":
    main()
