#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 ███╗   ███╗ █████╗ ███╗   ███╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
 Mamo Code — single-file terminal coding assistant with 100+ AI API support.

 Install :  pip install litellm rich requests prompt_toolkit
 Run     :  python mamo.py
 Config  :  ~/.mamo/config.json
"""
import os, sys, re, json, time, subprocess, logging
from pathlib import Path
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

VERSION = "0.2.0"
CONFIG_DIR = Path.home() / ".mamo"
CONFIG_FILE = CONFIG_DIR / "config.json"
console = Console()
GRADIENT = ["#7c3aed", "#8b5cf6", "#a78bfa", "#c084fc", "#e879f9", "#f472b6", "#fb7185", "#fb923c"]
ACC = "#c084fc"   # purple
ACC2 = "#fb923c"  # orange

# ═══════════════════════════════════════════════════════════════════════════
#  PROVIDERS
#  kind: "openai" = any OpenAI-compatible /v1 endpoint (most providers)
#        "anthropic" / "gemini" / "cohere" / "ollama" = native APIs
# ═══════════════════════════════════════════════════════════════════════════
def P(label, kind, base=None):
    return {"label": label, "kind": kind, "base": base}

PROVIDERS = {
    # ── big labs ──────────────────────────────────────────────────────────
    "openai":      P("OpenAI",                 "openai",    "https://api.openai.com/v1"),
    "anthropic":   P("Anthropic (Claude)",     "anthropic"),
    "gemini":      P("Google Gemini",          "gemini"),
    "xai":         P("xAI (Grok)",             "openai",    "https://api.x.ai/v1"),
    "mistral":     P("Mistral",                "openai",    "https://api.mistral.ai/v1"),
    "cohere":      P("Cohere",                 "cohere"),
    "deepseek":    P("DeepSeek",               "openai",    "https://api.deepseek.com/v1"),
    "perplexity":  P("Perplexity",             "openai",    "https://api.perplexity.ai"),
    "ai21":        P("AI21 Labs",              "openai",    "https://api.ai21.com/studio/v1"),
    # ── fast inference clouds ─────────────────────────────────────────────
    "groq":        P("Groq",                   "openai",    "https://api.groq.com/openai/v1"),
    "cerebras":    P("Cerebras",               "openai",    "https://api.cerebras.ai/v1"),
    "sambanova":   P("SambaNova",              "openai",    "https://api.sambanova.ai/v1"),
    "together":    P("Together AI",            "openai",    "https://api.together.xyz/v1"),
    "fireworks":   P("Fireworks AI",           "openai",    "https://api.fireworks.ai/inference/v1"),
    "deepinfra":   P("DeepInfra",              "openai",    "https://api.deepinfra.com/v1/openai"),
    "nvidia":      P("NVIDIA NIM",             "openai",    "https://integrate.api.nvidia.com/v1"),
    "hyperbolic":  P("Hyperbolic",             "openai",    "https://api.hyperbolic.xyz/v1"),
    "nebius":      P("Nebius",                 "openai",    "https://api.studio.nebius.com/v1"),
    "novita":      P("Novita AI",              "openai",    "https://api.novita.ai/v3/openai"),
    "featherless": P("Featherless",            "openai",    "https://api.featherless.ai/v1"),
    "chutes":      P("Chutes",                 "openai",    "https://llm.chutes.ai/v1"),
    "friendli":    P("Friendli",               "openai",    "https://api.friendli.ai/serverless/v1"),
    "kluster":     P("Kluster AI",             "openai",    "https://api.kluster.ai/v1"),
    "inference":   P("Inference.net",          "openai",    "https://api.inference.net/v1"),
    "parasail":    P("Parasail",               "openai",    "https://api.parasail.io/v1"),
    "targon":      P("Targon",                 "openai",    "https://api.targon.com/v1"),
    "lambda":      P("Lambda",                 "openai",    "https://api.lambda.ai/v1"),
    "scaleway":    P("Scaleway",               "openai",    "https://api.scaleway.ai/v1"),
    "venice":      P("Venice AI",              "openai",    "https://api.venice.ai/api/v1"),
    # ── routers / aggregators ─────────────────────────────────────────────
    "openrouter":  P("OpenRouter (300+ models)", "openai",  "https://openrouter.ai/api/v1"),
    "requesty":    P("Requesty",               "openai",    "https://router.requesty.ai/v1"),
    "aihubmix":    P("AiHubMix",               "openai",    "https://aihubmix.com/v1"),
    "huggingface": P("Hugging Face",           "openai",    "https://router.huggingface.co/v1"),
    "github":      P("GitHub Models",          "openai",    "https://models.github.ai/inference"),
    # ── asia ──────────────────────────────────────────────────────────────
    "moonshot":    P("Moonshot (Kimi)",        "openai",    "https://api.moonshot.ai/v1"),
    "zhipu":       P("Zhipu (GLM)",            "openai",    "https://open.bigmodel.cn/api/paas/v4"),
    "qwen":        P("Alibaba Qwen",           "openai",    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
    "siliconflow": P("SiliconFlow",            "openai",    "https://api.siliconflow.cn/v1"),
    "minimax":     P("MiniMax",                "openai",    "https://api.minimax.io/v1"),
    "stepfun":     P("StepFun",                "openai",    "https://api.stepfun.com/v1"),
    "yi":          P("01.AI (Yi)",             "openai",    "https://api.lingyiwanwu.com/v1"),
    "baichuan":    P("Baichuan",               "openai",    "https://api.baichuan-ai.com/v1"),
    "upstage":     P("Upstage (Solar)",        "openai",    "https://api.upstage.ai/v1"),
    # ── local ─────────────────────────────────────────────────────────────
    "ollama":      P("Ollama (local)",         "ollama",    "http://localhost:11434"),
    "lmstudio":    P("LM Studio (local)",      "openai",    "http://localhost:1234/v1"),
    "vllm":        P("vLLM / llama.cpp (local)", "openai",  "http://localhost:8000/v1"),
    "custom":      P("Custom OpenAI-compatible URL", "openai"),
}

# ═══════════════════════════════════════════════════════════════════════════
#  API KEY PATTERNS  →  which provider does this key belong to?
#  Written out explicitly. Order = most specific first.
#  Several providers share "sk-"; those are ambiguous → we probe all of them.
# ═══════════════════════════════════════════════════════════════════════════
KEY_PATTERNS = [
    # (regex,                                  provider,      note)
    (r"^sk-ant-",                              "anthropic",   "Anthropic keys start with  sk-ant-"),
    (r"^sk-or-",                               "openrouter",  "OpenRouter keys start with sk-or-v1-"),
    (r"^gsk_",                                 "groq",        "GROQ (Groq Cloud) keys start with gsk_"),
    (r"^xai-",                                 "xai",         "GROK (xAI) keys start with xai-"),
    (r"^AIza",                                 "gemini",      "Google Gemini keys start with AIza"),
    (r"^pplx-",                                "perplexity",  "Perplexity keys start with pplx-"),
    (r"^csk-",                                 "cerebras",    "Cerebras keys start with csk-"),
    (r"^fw_",                                  "fireworks",   "Fireworks keys start with fw_"),
    (r"^nvapi-",                               "nvidia",      "NVIDIA NIM keys start with nvapi-"),
    (r"^hf_",                                  "huggingface", "Hugging Face tokens start with hf_"),
    (r"^(ghp_|github_pat_|gho_)",              "github",      "GitHub tokens: ghp_ / github_pat_"),
    (r"^up_",                                  "upstage",     "Upstage keys start with up_"),
    (r"^rc_",                                  "featherless", "Featherless keys start with rc_"),
    (r"^cpk_",                                 "chutes",      "Chutes keys start with cpk_"),
    (r"^sk_",                                  "novita",      "Novita keys start with sk_ (underscore)"),
    (r"^secret_",                              "lambda",      "Lambda keys start with secret_"),
    (r"^flp_",                                 "friendli",    "Friendli keys start with flp_"),
    (r"^[a-f0-9]{32}\.[A-Za-z0-9]{16}$",       "zhipu",       "Zhipu keys look like  <32hex>.<16chars>"),
    (r"^sk-(proj|svcacct|admin)-",             "openai",      "OpenAI project/service keys: sk-proj-"),
    # ambiguous "sk-" family (OpenAI legacy, DeepSeek, Moonshot, Qwen, SiliconFlow...)
    (r"^sk-",                                  "openai",      "sk- (legacy OpenAI or one of the below)"),
    (r"^sk-",                                  "deepseek",    "DeepSeek keys: sk-<32 hex>"),
    (r"^sk-",                                  "moonshot",    "Moonshot keys: sk-..."),
    (r"^sk-",                                  "qwen",        "Alibaba DashScope keys: sk-..."),
    (r"^sk-",                                  "siliconflow", "SiliconFlow keys: sk-..."),
    (r"^sk-",                                  "aihubmix",    "AiHubMix keys: sk-..."),
    (r"^sk-",                                  "requesty",    "Requesty keys: sk-..."),
    (r"^sk-",                                  "stepfun",     "StepFun keys: sk-..."),
    # JWT-style tokens (eyJ...) — MiniMax, Hyperbolic, Nebius
    (r"^eyJ",                                  "minimax",     "MiniMax keys are JWTs (eyJ...)"),
    (r"^eyJ",                                  "hyperbolic",  "Hyperbolic keys are JWTs (eyJ...)"),
    (r"^eyJ",                                  "nebius",      "Nebius keys are JWTs (eyJ...)"),
    # UUID-style keys — SambaNova, Scaleway, Kluster
    (r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "sambanova", "SambaNova keys are UUIDs"),
    (r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "scaleway",  "Scaleway keys are UUIDs"),
    (r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", "kluster",   "Kluster keys are UUIDs"),
    # plain alphanumeric, no prefix — Mistral (32), Cohere (40), Together (64 hex), DeepInfra (32)
    (r"^[A-Za-z0-9]{32}$",                     "mistral",     "Mistral keys: 32 alphanumeric chars"),
    (r"^[A-Za-z0-9]{32}$",                     "deepinfra",   "DeepInfra keys: 32 alphanumeric chars"),
    (r"^[A-Za-z0-9]{40}$",                     "cohere",      "Cohere keys: 40 alphanumeric chars"),
    (r"^[a-f0-9]{64}$",                        "together",    "Together keys: 64 hex chars"),
    (r"^[A-Za-z0-9]{64}$",                     "ai21",        "AI21 keys: 64 chars"),
]
# providers worth probing when a key matches nothing (all OpenAI-compatible → cheap /models call)
PROBE_FALLBACK = ["openai", "mistral", "together", "deepinfra", "sambanova", "novita", "venice",
                  "hyperbolic", "nebius", "kluster", "ai21", "yi", "baichuan", "scaleway", "inference",
                  "parasail", "targon", "lambda", "cohere", "minimax", "zhipu", "moonshot", "deepseek",
                  "qwen", "siliconflow", "groq", "xai", "cerebras", "fireworks", "perplexity"]

# ═══════════════════════════════════════════════════════════════════════════
#  STATE / CONFIG
# ═══════════════════════════════════════════════════════════════════════════
class State:
    def __init__(s):
        s.cfg = {"providers": {}, "current": {}, "thinkmode": 1, "multimode": 1}
        s.messages, s.cost, s.tokens, s.yolo = [], 0.0, 0, False
S = State()

def load_cfg():
    if CONFIG_FILE.exists():
        try: S.cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception: pass

def save_cfg():
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(S.cfg, indent=2))
    try: os.chmod(CONFIG_FILE, 0o600)
    except Exception: pass

def cur():
    c = S.cfg["current"]; p = S.cfg["providers"].get(c.get("provider"), {})
    return c.get("provider"), c.get("model"), p.get("key"), p.get("base")

def lm_model(pid, model):
    kind = PROVIDERS[pid]["kind"]
    return {"anthropic": "anthropic/", "gemini": "gemini/", "cohere": "cohere_chat/",
            "ollama": "ollama_chat/"}.get(kind, "openai/") + model

def lm_kwargs():
    pid, model, key, base = cur()
    kw = {"model": lm_model(pid, model), "api_key": key or "x"}
    if PROVIDERS[pid]["kind"] in ("openai", "ollama"):
        kw["api_base"] = base or PROVIDERS[pid]["base"]
    if pid == "openrouter":
        kw["extra_headers"] = {"HTTP-Referer": "https://github.com/mamo-code", "X-Title": "Mamo Code"}
    return kw

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
        console.print(gradient_text(line, i * 2)); time.sleep(0.05)
    console.print(Text(f"  v{VERSION} · 100+ AI APIs · type /help for commands", style="dim")); console.print()

def ok(m): console.print(f"[bold green]✓[/] {m}")
def warn(m): console.print(f"[bold yellow]![/] {m}")
def err(m): console.print(f"[bold red]✗[/] {m}")

def status_bar():
    pid, model, _, _ = cur()
    t = Text(); t.append(" ◆ ", style=ACC); t.append(PROVIDERS[pid]["label"], style="bold")
    t.append(f" · {model}", style=ACC2)
    t.append(f" · think {S.cfg['thinkmode']}/5 · agents {S.cfg['multimode']}/3", style="dim")
    if S.yolo: t.append(" · YOLO", style="bold red")
    t.append(f" · ${S.cost:.4f}", style="dim"); console.print(t)

# ═══════════════════════════════════════════════════════════════════════════
#  KEY DETECTION + VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def candidates_for(key):
    """Providers whose key format matches. Most specific match wins; ties → all returned."""
    if not key: return ["ollama", "lmstudio", "vllm"]
    hits = []
    for rx, pid, _ in KEY_PATTERNS:
        if re.match(rx, key) and pid not in hits: hits.append(pid)
    # if a specific prefix matched (e.g. sk-ant-), drop the generic sk- family
    specific = [p for p in hits if p not in ("openai", "deepseek", "moonshot", "qwen", "siliconflow",
                                              "aihubmix", "requesty", "stepfun")]
    if specific and re.match(r"^sk-(ant|or|proj|svcacct|admin)-", key): return specific
    return hits or PROBE_FALLBACK

def fetch_models(pid, key, base=None):
    """returns (status, data)  status: ok | auth | fail"""
    p = PROVIDERS[pid]; kind = p["kind"]; base = base or p["base"]
    try:
        if kind == "anthropic":
            r = requests.get("https://api.anthropic.com/v1/models?limit=1000", timeout=15,
                             headers={"x-api-key": key, "anthropic-version": "2023-06-01"})
            parse = lambda j: [m["id"] for m in j["data"]]
        elif kind == "gemini":
            r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=200", timeout=15)
            parse = lambda j: [m["name"].replace("models/", "") for m in j["models"]
                               if "generateContent" in m.get("supportedGenerationMethods", [])]
        elif kind == "cohere":
            r = requests.get("https://api.cohere.com/v1/models?page_size=200&endpoint=chat", timeout=15,
                             headers={"Authorization": f"Bearer {key}"})
            parse = lambda j: [m["name"] for m in j["models"]]
        elif kind == "ollama":
            r = requests.get(f"{base}/api/tags", timeout=5)
            parse = lambda j: [m["name"] for m in j["models"]]
        else:
            r = requests.get(f"{base.rstrip('/')}/models", timeout=15, headers={"Authorization": f"Bearer {key}"})
            parse = lambda j: [m["id"] for m in j["data"]]
        if r.status_code in (401, 403): return "auth", f"HTTP {r.status_code}"
        if r.status_code >= 400: return "fail", f"HTTP {r.status_code}"
        models = sorted(set(parse(r.json())))
        return ("ok", models) if models else ("fail", "empty model list")
    except Exception as e:
        return "fail", str(e)[:100]

def detect_and_verify(key):
    """Auto-detect provider: probe all candidates in parallel, first authenticated one wins."""
    cands = candidates_for(key)
    results = {}
    with console.status(f"[{ACC}]Detecting provider · probing {len(cands)} candidate(s)...[/]", spinner="dots12"):
        with ThreadPoolExecutor(max_workers=min(16, len(cands))) as ex:
            futs = {ex.submit(fetch_models, pid, key): pid for pid in cands}
            for f in as_completed(futs):
                pid = futs[f]; st, data = f.result(); results[pid] = (st, data)
                if st == "ok" and len(cands) == 1: break
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

def setup_provider():
    console.print(Panel(f"[bold]Paste your API key[/]  [dim](any provider — auto-detected · press Enter with no key for local models)[/]",
                        border_style=ACC, expand=False))
    key = Prompt.ask(f"[{ACC2}]🔑[/]", password=True).strip()
    winners, results = detect_and_verify(key)
    base = None

    if len(winners) == 1:
        pid = winners[0]
    elif len(winners) > 1:
        ok(f"Key works with multiple providers: {', '.join(PROVIDERS[w]['label'] for w in winners)}")
        pid = pick("Which one?", winners, [PROVIDERS[w]["label"] for w in winners])
    else:
        # nothing authenticated
        auth_fail = [p for p, (st, _) in results.items() if st == "auth"]
        if key and auth_fail and len(results) <= 3:
            err(f"Invalid API key — rejected by {', '.join(PROVIDERS[p]['label'] for p in auth_fail)}")
        elif key:
            err("Couldn't verify this key with any known provider.")
        else:
            err("No local server found (Ollama :11434 / LM Studio :1234 / vLLM :8000).")
        if Confirm.ask("Try again?", default=True): return setup_provider()
        if not Confirm.ask("Pick provider manually instead?", default=False): return False
        ids = list(PROVIDERS)
        pid = pick("Provider", ids, [PROVIDERS[i]["label"] for i in ids])
        if pid == "custom" or Confirm.ask("Custom base URL?", default=False):
            base = Prompt.ask("Base URL", default=PROVIDERS[pid]["base"] or "http://localhost:8000/v1").strip()
        with console.status(f"[{ACC}]Verifying...[/]", spinner="dots12"):
            results[pid] = fetch_models(pid, key, base)

    st, data = results[pid]
    ok(f"Provider: [bold]{PROVIDERS[pid]['label']}[/]")
    if st == "ok":
        ok(f"Valid key · [bold]{len(data)}[/] models available")
        model = choose_model(data)
    else:
        warn(f"Couldn't list models ({data}). Enter model name manually.")
        model = Prompt.ask("Model name").strip()
    S.cfg["providers"][pid] = {"key": key, "base": base}
    S.cfg["current"] = {"provider": pid, "model": model}
    save_cfg()
    ok(f"Ready: [bold]{PROVIDERS[pid]['label']}[/] → [{ACC2}]{model}[/]")
    return True

# ═══════════════════════════════════════════════════════════════════════════
#  TOOLS (files / shell / search)
# ═══════════════════════════════════════════════════════════════════════════
MAX_OUT = 12000
def _clip(s): return s if len(s) <= MAX_OUT else s[:MAX_OUT] + f"\n...[{len(s)-MAX_OUT} chars truncated]"

def t_read_file(path):
    p = Path(path)
    return _clip(p.read_text(errors="replace")) if p.is_file() else f"ERROR: no such file: {path}"

def t_write_file(path, content):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content); return f"wrote {path} ({len(content)} chars)"

def t_edit_file(path, old, new):
    p = Path(path)
    if not p.is_file(): return f"ERROR: no such file: {path}"
    s = p.read_text(errors="replace")
    if s.count(old) == 0: return "ERROR: 'old' text not found (must match exactly)"
    if s.count(old) > 1: return f"ERROR: 'old' appears {s.count(old)} times, be more specific"
    p.write_text(s.replace(old, new, 1)); return f"edited {path}"

def t_list_dir(path="."):
    p = Path(path)
    if not p.is_dir(): return f"ERROR: no such directory: {path}"
    items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    return _clip("\n".join(("📁 " if x.is_dir() else "   ") + x.name for x in items if x.name != ".git"))

def t_search(pattern, path=".", glob="*"):
    out, rx = [], re.compile(pattern, re.I)
    for f in Path(path).rglob(glob):
        if f.is_file() and ".git" not in f.parts and "node_modules" not in f.parts and f.stat().st_size < 2_000_000:
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
              "list_dir": t_list_dir, "search": t_search, "run_shell": t_run_shell}

def _tool(name, desc, props, req):
    return {"type": "function", "function": {"name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": req}}}
STR = {"type": "string"}
TOOLS = [
    _tool("read_file", "Read a file", {"path": STR}, ["path"]),
    _tool("write_file", "Create or overwrite a file", {"path": STR, "content": STR}, ["path", "content"]),
    _tool("edit_file", "Replace exact 'old' text with 'new' in a file", {"path": STR, "old": STR, "new": STR}, ["path", "old", "new"]),
    _tool("list_dir", "List a directory", {"path": STR}, []),
    _tool("search", "Regex search across files (grep)", {"pattern": STR, "path": STR, "glob": STR}, ["pattern"]),
    _tool("run_shell", "Run a shell command (requires user approval)", {"command": STR}, ["command"]),
]
READ_TOOLS = [t for t in TOOLS if t["function"]["name"] in ("read_file", "list_dir", "search")]

def exec_tool(name, args):
    icon = {"read_file": "📖", "write_file": "✏️ ", "edit_file": "🔧", "list_dir": "📁", "search": "🔍", "run_shell": "💻"}.get(name, "🛠")
    console.print(f"  [dim]{icon} {name}[/] [{ACC2}]{json.dumps(args, ensure_ascii=False)[:120]}[/]")
    try: return TOOL_FUNCS[name](**args)
    except Exception as e: return f"ERROR: {e}"

# ═══════════════════════════════════════════════════════════════════════════
#  THINK MODE
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
    return (f"You are Mamo Code, an expert software engineering assistant running in a terminal. "
            f"Working directory: {os.getcwd()}. Use tools (read/write/edit files, search, shell) when needed; "
            f"always read a file before editing it. Be concise and technical. Reply in the user's language. {extra}").strip()

# ═══════════════════════════════════════════════════════════════════════════
#  AGENT CORE
# ═══════════════════════════════════════════════════════════════════════════
def _msg_to_dict(m):
    d = {"role": "assistant", "content": m.content or ""}
    if m.tool_calls:
        d["tool_calls"] = [{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in m.tool_calls]
    return d

def _track(resp):
    try:
        S.cost += litellm.completion_cost(completion_response=resp) or 0
        S.tokens += getattr(resp.usage, "total_tokens", 0) or 0
    except Exception: pass

def stream_completion(messages, tools, extra):
    kw = dict(lm_kwargs(), messages=messages, stream=True, **extra)
    if tools: kw["tools"] = tools
    text = think = ""; chunks = []; t0 = time.time()
    for _ in range(3):
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
        except Exception as e:
            s = str(e).lower()
            if "reasoning" in s and "reasoning_effort" in kw: kw.pop("reasoning_effort"); warn("reasoning not supported, plain mode")
            elif "tool" in s and "tools" in kw: kw.pop("tools"); warn("this model doesn't support tools, chat only")
            else: raise
    if think:
        console.print(Panel(Text(think[:600] + ("..." if len(think) > 600 else ""), style="dim italic"),
                            title=f"[dim]💭 reasoning · {len(think)} chars[/]", border_style="grey37", expand=False))
    if text:
        console.print(Panel(Markdown(text), border_style=ACC, title="[bold]mamo[/]", title_align="left",
                            subtitle=f"[dim]{time.time()-t0:.1f}s[/]", subtitle_align="right"))
    try: resp = litellm.stream_chunk_builder(chunks, messages=messages)
    except Exception:
        class _R: pass
        resp = _R(); resp.choices = [type("c", (), {"message": type("m", (), {"content": text, "tool_calls": None})()})()]
    return resp, text

def run_agent(messages, tools, extra, max_steps=25):
    text = ""
    for _ in range(max_steps):
        resp, text = stream_completion(messages, tools, extra); _track(resp)
        m = resp.choices[0].message; messages.append(_msg_to_dict(m))
        if not m.tool_calls: return text
        for tc in m.tool_calls:
            try: args = json.loads(tc.function.arguments or "{}")
            except Exception: args = {}
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name,
                             "content": exec_tool(tc.function.name, args)})
    warn("step limit reached"); return text

# ═══════════════════════════════════════════════════════════════════════════
#  MULTI MODE (parallel agent team)
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
            _track(r); m = r.choices[0].message; msgs.append(_msg_to_dict(m))
            if not m.tool_calls: status[role] = "done"; return m.content or ""
            for tc in m.tool_calls:
                try: args = json.loads(tc.function.arguments or "{}")
                except Exception: args = {}
                try: res = TOOL_FUNCS[tc.function.name](**args)
                except Exception as e: res = f"ERROR: {e}"
                status[role] = tc.function.name
                msgs.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": res})
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
    "init":     ("Explore project", "Explore this project (directory layout, main files, dependencies) and write a short summary."),
}

# ═══════════════════════════════════════════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════════════════════════════════════════
HELP = f"""
[bold {ACC}]/model[/]            switch model (same provider)
[bold {ACC}]/provider[/]         switch between saved providers
[bold {ACC}]/key[/]              add a new API key (auto-detected)
[bold {ACC}]/thinkmode 1-5[/]    reasoning depth (1 off → 5 max)
[bold {ACC}]/multimode 1-3[/]    number of parallel agents
[bold {ACC}]/skills[/]           list skills  →  /review, /fix, /test ...
[bold {ACC}]/yolo[/]             run shell commands without confirmation (careful)
[bold {ACC}]/clear[/]            reset chat        [bold {ACC}]/cost[/]  show spend
[bold {ACC}]/cd <dir>[/]         change directory  [bold {ACC}]/exit[/]  quit
[bold {ACC2}]!command[/]          run a shell command directly
"""

def handle_command(line):
    parts = line.strip().split(maxsplit=1)
    cmd, arg = parts[0].lower(), (parts[1] if len(parts) > 1 else "")
    if cmd in ("/exit", "/quit", "/q"): raise SystemExit
    elif cmd == "/help": console.print(Panel(HELP.strip(), title="[bold]Commands[/]", border_style=ACC, expand=False))
    elif cmd == "/clear": S.messages.clear(); console.clear(); ok("chat cleared")
    elif cmd == "/cost": console.print(f"  [bold]${S.cost:.4f}[/] · {S.tokens} tokens")
    elif cmd == "/yolo": S.yolo = not S.yolo; warn(f"YOLO {'ON — commands run without confirmation!' if S.yolo else 'off'}")
    elif cmd == "/cd":
        try: os.chdir(os.path.expanduser(arg or "~")); ok(os.getcwd())
        except Exception as e: err(e)
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
    elif cmd == "/skills":
        t = Table(box=box.SIMPLE); t.add_column("Command", style=ACC); t.add_column("Description")
        for k, (d, _) in SKILLS.items(): t.add_row(f"/{k}", d)
        console.print(Panel(t, title="[bold]Skills[/]", border_style=ACC, expand=False))
    elif cmd == "/key": setup_provider(); S.messages.clear()
    elif cmd == "/provider":
        ids = list(S.cfg["providers"])
        if len(ids) < 2: warn("only one provider saved — add another with /key"); return
        pid = pick("Provider", ids, [PROVIDERS[i]["label"] for i in ids])
        S.cfg["current"]["provider"] = pid; save_cfg(); handle_command("/model")
    elif cmd == "/model":
        pid, _, key, base = cur()
        with console.status(f"[{ACC}]fetching models...[/]", spinner="dots12"): st, data = fetch_models(pid, key, base)
        model = choose_model(data) if st == "ok" else Prompt.ask("Model name").strip()
        S.cfg["current"]["model"] = model; save_cfg(); ok(f"model → [{ACC2}]{model}[/]")
    elif cmd[1:] in SKILLS:
        return SKILLS[cmd[1:]][1].format(a=arg or "this project")
    else: err(f"unknown command: {cmd}  (try /help)")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════
def chat(user_text):
    extra, hint = think_params()
    sysmsg = {"role": "system", "content": system_prompt(hint)}
    if not S.messages: S.messages.append(sysmsg)
    else: S.messages[0] = sysmsg
    content = user_text
    if S.cfg["multimode"] > 1:
        reports = multi_run(user_text, extra)
        content = (f"{user_text}\n\n---\nYour team's parallel analysis reports are below. Synthesize them, resolve "
                   f"conflicts, and apply changes with tools if appropriate:\n{reports}")
    S.messages.append({"role": "user", "content": content})
    try: run_agent(S.messages, TOOLS, extra)
    except KeyboardInterrupt: warn("cancelled")
    except Exception as e:
        err(f"API error: {str(e)[:400]}")
        if S.messages and S.messages[-1]["role"] == "user": S.messages.pop()

def read_input(session):
    if HAS_PT:
        return session.prompt(HTML(f'<style fg="{ACC}"><b>mamo</b></style> <style fg="{ACC2}">❯</style> '))
    return input("mamo ❯ ")

def main():
    load_cfg(); banner()
    if not S.cfg.get("current") or not S.cfg["current"].get("model"):
        if not setup_provider(): return
    session = None
    if HAS_PT:
        words = ["/model", "/provider", "/key", "/thinkmode", "/multimode", "/skills", "/yolo", "/clear",
                 "/cost", "/cd", "/help", "/exit"] + [f"/{k}" for k in SKILLS]
        session = PromptSession(completer=WordCompleter(words, sentence=True))
    console.print(Panel(f"[bold]Welcome![/] Ask anything, let me edit files, or type [bold {ACC}]/help[/].",
                        border_style=ACC2, expand=False))
    while True:
        status_bar()
        try: line = read_input(session).strip()
        except (EOFError, KeyboardInterrupt): console.print("\n[dim]bye 👋[/]"); break
        if not line: continue
        try:
            if line.startswith("!"):
                r = subprocess.run(line[1:], shell=True, capture_output=True, text=True)
                console.print(Text((r.stdout + r.stderr).strip() or f"exit={r.returncode}", style="dim"))
            elif line.startswith("/"):
                prompt = handle_command(line)
                if prompt: chat(prompt)
            else: chat(line)
        except SystemExit: console.print(f"[dim]bye 👋 · total ${S.cost:.4f}[/]"); break
        except KeyboardInterrupt: warn("cancelled")
        console.print()

if __name__ == "__main__":
    main()
