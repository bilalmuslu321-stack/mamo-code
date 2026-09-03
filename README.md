<div align="center">

```
███╗   ███╗ █████╗ ███╗   ███╗ ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
████╗ ████║██╔══██╗████╗ ████║██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
██╔████╔██║███████║██╔████╔██║██║   ██║    ██║     ██║   ██║██║  ██║█████╗
██║╚██╔╝██║██╔══██║██║╚██╔╝██║██║   ██║    ██║     ██║   ██║██║  ██║██╔══╝
██║ ╚═╝ ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
```

**A single-file AI coding assistant for your terminal. Works with 100+ AI APIs.**

Paste any API key → it detects the provider → pick a model → start coding.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Single File](https://img.shields.io/badge/size-one%20file-purple.svg)](mamo.py)

</div>

---

## What is Mamo Code?

Mamo Code is a Claude Code–style terminal agent that is **not locked to one vendor**. It's one Python file. You paste an API key from OpenAI, Anthropic, Google, Groq, DeepSeek, OpenRouter, Mistral, xAI, or any of 45+ other providers (or a local Ollama/LM Studio server), and it figures out the rest.

It can **read, write and edit files**, **search your codebase**, **run shell commands** (with your approval), and it has slash commands for reasoning depth (`/thinkmode`) and parallel multi-agent analysis (`/multimode`).

## Features

- 🔑 **Zero-config start** — paste a key, provider is auto-detected and verified against the real API
- 🌐 **100+ AI APIs** — 45+ providers built in, plus OpenRouter (300+ models) and any OpenAI-compatible URL
- 🛠 **Real coding agent** — reads/writes/edits files, greps your project, runs commands
- 🧠 **`/thinkmode 1-5`** — reasoning depth; uses native reasoning (Claude, o-series, DeepSeek-R1, Gemini) when the model supports it
- ⚡ **`/multimode 1-3`** — Architect / Reviewer / Implementer agents run in parallel, then a lead agent synthesizes
- 🎯 **Skills** — `/review`, `/fix`, `/test`, `/refactor`, `/explain`, `/docs`, `/commit`, `/init`
- 🎨 **Nice UI** — gradient logo, streaming markdown, spinners, live agent status, cost tracking
- 📄 **Single file** — no build step, no project structure, just `mamo.py`
- 🔒 **Safe by default** — every shell command asks for confirmation (disable with `/yolo`)

## Installation

**Requirements:** Python 3.9+

```bash
# 1. Get the file
git clone https://github.com/bilalmuslu321-stack/mamo-code.git
cd mamo-code

# 2. Install dependencies
pip install litellm rich requests prompt_toolkit

# 3. Run
python mamo.py
```

That's it. On first launch it will ask for an API key.

### Make it a global command (optional)

**macOS / Linux**
```bash
mkdir -p ~/.local/bin
cp mamo.py ~/.local/bin/mamo
chmod +x ~/.local/bin/mamo
# make sure ~/.local/bin is in your PATH, then:
mamo
```

**Windows (PowerShell)**
```powershell
# put mamo.py somewhere permanent, e.g. C:\mamo\mamo.py
notepad $PROFILE
# add this line and save:
function mamo { python C:\mamo\mamo.py }
```
Restart the terminal and type `mamo`.

## Quick Start

```
$ python mamo.py

🔑  ▸ paste your key (hidden)

✓ Provider: Groq
✓ Valid key · 14 models available

┌─ Pick a model ──────────────┐
│ 1  llama-3.3-70b-versatile  │
│ 2  deepseek-r1-distill-...  │
│ ...                         │
└─────────────────────────────┘
Number / type to filter / Enter = first: 1

✓ Ready: Groq → llama-3.3-70b-versatile

 ◆ Groq · llama-3.3-70b-versatile · think 1/5 · agents 1/3 · $0.0000
mamo ❯ create a fastapi hello world in app.py and run it
```

## Usage

Just type what you want. Mamo will use tools when it needs to:

```
mamo ❯ what does this project do?
mamo ❯ add input validation to the login function in auth.py
mamo ❯ find every place we call requests.get and add a timeout
mamo ❯ why does pytest fail? fix it
```

### Commands

| Command | What it does |
|---|---|
| `/model` | Switch model (same provider) |
| `/provider` | Switch between saved providers |
| `/key` | Add another API key (auto-detected) |
| `/thinkmode 1-5` | Reasoning depth — `1` off, `5` maximum |
| `/multimode 1-3` | Number of parallel agents |
| `/skills` | List available skills |
| `/yolo` | Toggle: run shell commands without asking |
| `/clear` | Reset the conversation |
| `/cost` | Show token usage and estimated cost |
| `/cd <dir>` | Change working directory |
| `/help` | Show all commands |
| `/exit` | Quit |
| `!<cmd>` | Run a shell command directly (e.g. `!git status`) |

### Skills

Skills are one-shot prompts with a target:

| Skill | Example |
|---|---|
| `/init` | `/init` — explore and summarize the project |
| `/review` | `/review src/api/` |
| `/fix` | `/fix TypeError on line 42 of utils.py` |
| `/test` | `/test parser.py` |
| `/refactor` | `/refactor the User class` |
| `/explain` | `/explain main.py` |
| `/docs` | `/docs cli.py` |
| `/commit` | `/commit` — reads `git diff`, proposes a commit message |

### Think Mode

```
mamo ❯ /thinkmode 4
  🧠 think mode → ●●●●○ 4/5
```

| Level | Native reasoning models (Claude, o1/o3, R1, Gemini…) | Other models |
|---|---|---|
| 1 | off | off |
| 2 | `reasoning_effort: low` | brief thinking prompt |
| 3 | `reasoning_effort: medium` | brief thinking prompt |
| 4 | `reasoning_effort: high` | step-by-step prompt |
| 5 | `high` + deep-analysis prompt | deep-analysis prompt |

The model's reasoning stream is shown in a separate dim panel.

### Multi Mode

```
mamo ❯ /multimode 3
  ⚡ multi mode → 3 agent(s) (Architect, Reviewer, Implementer + synthesis)
```

With `2` or `3`, each prompt is first analyzed in parallel by:

- **Architect** — structure, design, best approach
- **Reviewer** — bugs, edge cases, security, performance
- **Implementer** — concrete file-by-file plan

Workers are read-only. Their reports are shown, then the lead agent synthesizes them and applies changes with full tools. Costs roughly 3–4× a single request.

## Supported Providers

Keys are detected by their format. Ambiguous formats (like `sk-…`) are resolved by probing the candidate APIs in parallel — the one that authenticates wins.

| Category | Providers |
|---|---|
| **Major labs** | OpenAI, Anthropic (Claude), Google Gemini, xAI (Grok), Mistral, Cohere, DeepSeek, Perplexity, AI21 |
| **Fast inference** | Groq, Cerebras, SambaNova, Together AI, Fireworks, DeepInfra, NVIDIA NIM, Hyperbolic, Nebius, Novita, Featherless, Chutes, Friendli, Kluster, Inference.net, Parasail, Targon, Lambda, Scaleway, Venice |
| **Routers** | OpenRouter (300+ models), Requesty, AiHubMix, Hugging Face, GitHub Models |
| **Asia** | Moonshot (Kimi), Zhipu (GLM), Alibaba Qwen, SiliconFlow, MiniMax, StepFun, 01.AI (Yi), Baichuan, Upstage (Solar) |
| **Local** | Ollama, LM Studio, vLLM / llama.cpp — press Enter with an empty key |
| **Custom** | Any OpenAI-compatible `/v1` endpoint |

### Key formats (for reference)

| Prefix | Provider |
|---|---|
| `sk-ant-` | Anthropic |
| `sk-or-` | OpenRouter |
| `sk-proj-` | OpenAI |
| `gsk_` | **Groq** |
| `xai-` | **xAI (Grok)** |
| `AIza` | Google Gemini |
| `pplx-` | Perplexity |
| `csk-` | Cerebras |
| `fw_` | Fireworks |
| `nvapi-` | NVIDIA |
| `hf_` | Hugging Face |
| `ghp_` / `github_pat_` | GitHub Models |
| `sk-` | OpenAI / DeepSeek / Moonshot / Qwen / SiliconFlow… (auto-probed) |
| no prefix | Mistral / Together / Cohere / … (auto-probed) |

Adding a provider is a one-line change in `PROVIDERS` and optionally one line in `KEY_PATTERNS`.

## Configuration

Everything is stored in `~/.mamo/config.json` (file permissions `600`):

```json
{
  "providers": {
    "groq":      { "key": "gsk_...", "base": null },
    "anthropic": { "key": "sk-ant-...", "base": null }
  },
  "current": { "provider": "groq", "model": "llama-3.3-70b-versatile" },
  "thinkmode": 1,
  "multimode": 1
}
```

Delete this file to start fresh.

## Safety

- Shell commands are shown and require a `y` before running. `/yolo` disables this — use it only in throwaway environments.
- `edit_file` requires an exact, unique match, so the model can't silently clobber the wrong block.
- Tool output is truncated at 12k chars to keep context usage sane.
- Multi-mode workers have **read-only** tools; only the lead agent can write.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Missing packages` | `pip install litellm rich requests prompt_toolkit` |
| `pip` not found | `python -m pip install ...` |
| Wrong provider detected | Answer *No* to "Try again?" → pick manually |
| `this model doesn't support tools` | Pick a model that supports function calling (most modern ones do) |
| Model list empty / manual entry | Some providers don't expose `/models`; just type the model ID |
| Garbled box characters | Use a terminal with a Nerd/Unicode font (Windows Terminal, iTerm2, etc.) |
| Want to reset everything | `rm ~/.mamo/config.json` |

## Roadmap

- [ ] Multi-line input
- [ ] Persistent chat history / `/resume`
- [ ] Azure OpenAI, AWS Bedrock, Vertex AI (need extra credentials)
- [ ] MCP server support
- [ ] `pip install mamo-code`

## Contributing

PRs welcome. Keep it in one file. To add a provider:

```python
# in PROVIDERS
"newai": P("New AI", "openai", "https://api.newai.com/v1"),

# in KEY_PATTERNS (optional, for auto-detect)
(r"^na-", "newai", "New AI keys start with na-"),
```

## License

[MIT](LICENSE)

---

<div align="center">
Built with <a href="https://github.com/BerriAI/litellm">LiteLLM</a> and <a href="https://github.com/Textualize/rich">Rich</a>.
</div>
