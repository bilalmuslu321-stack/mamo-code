<div align="center">

Your terminal. Your models. Your code.
A single-file AI coding assistant with cloud and local model support.
Explore projects, edit files, write tests, and review code without leaving your terminal.

Python
Version
License: MIT
Single File

Quick Start · Features · Commands · Supported Providers · Safety

</div>
What is Mamo Code?
Mamo Code is a terminal coding assistant that is not locked to one AI vendor.

Connect your preferred cloud provider or a local model server, choose a model, and start working. Mamo can inspect your project, suggest improvements, edit files with your approval, and run commands to help verify its work.

Everything lives in one Python file: mamo.py.

text

mamo ❯ /local
        Scan local servers and select an installed model.

mamo ❯ /mode plan
        Explore and plan using read-only model tools.

mamo ❯ Explain the authentication flow and identify missing tests.

mamo ❯ /mode build

mamo ❯ Add tests for the edge cases you found.
What's New in V3?
Three new commands
Command	What it does
/menu	Opens an interactive menu for common actions.
/doctor	Checks dependencies, configuration, and optionally provider connectivity.
/favorites	Saves favorite models and lets you switch between them.
One new skill
/a11y reviews accessibility concerns such as semantic HTML, keyboard navigation, focus management, labels, contrast, and ARIA usage.

Improvements
Searchable, paginated provider and model selection.
Explicit provider selection before sending an API key.
Read-only tool permissions enforced for plan mode and analysis agents.
Confirmation prompts for file writes and edits.
Atomic configuration saves and validated session loading.
Controlled backup restoration with file and size checks.
Better recovery from interrupted tool calls and streaming failures.
/commands has been removed. Use /help to browse commands.

Features
Feature	Description
🌐 Multi-provider support	Use major cloud providers, model gateways, or a custom OpenAI-compatible endpoint.
🏠 Local models	Connect to Ollama, LM Studio, vLLM, Jan, and other local servers.
🛠️ Coding tools	Read files, inspect directory trees, search code, propose edits, and execute approved shell commands.
🗺️ Plan and build modes	Investigate with read-only model tools before enabling file changes.
🧠 Adjustable reasoning	Set /thinkmode 1-5; native reasoning parameters are used when detected as supported.
⚡ Parallel analysis	Architect, Reviewer, and Implementer roles analyze a task before the main agent acts.
⭐ Model favorites	Save useful provider/model combinations for quick switching.
📚 Task skills	Shortcuts for reviews, bug fixes, tests, documentation, security, accessibility, and more.
💾 Persistent sessions	Save, load, export, and back up your conversations.
🎨 Terminal interface	Streaming Markdown, syntax-highlighted diffs, searchable menus, and progress indicators.
📊 Usage visibility	Track tokens and available cost estimates; unknown costs are reported separately.
📄 Single-file setup	No build step or application server required.
Quick Start
1. Install
Requirements: Python 3.9+ and a terminal.

Bash

git clone https://github.com/bilalmuslu321-stack/mamo-code.git
cd mamo-code

python -m pip install litellm rich requests prompt_toolkit pyperclip
2. Run
Bash

python mamo.py
3. Connect a model
Cloud provider:

text

/key
Select your provider, enter its API key, and choose a model.

Local server:

text

/local
Mamo scans supported local server addresses and lists available models.

Custom local address:

text

/local http://127.0.0.1:8000/v1
For a remote custom endpoint that requires an API key, use /key and select Custom OpenAI-compatible endpoint.

4. Start coding
text

Explain this project's structure.

/review src/

/test src/auth.py

Find the cause of this failing test and propose a fix.
Your provider may charge for requests. Local model servers must be installed and running separately.

Local Model Setup
Ollama
Install Ollama, then download a model:

Bash

ollama pull qwen2.5-coder:7b
If the Ollama server is not already running:

Bash

ollama serve
In Mamo:

text

/local
LM Studio
Install LM Studio.
Download and load a model.
Start its local API server.
Run /local in Mamo.
Other servers
You can also connect to OpenAI-compatible servers such as vLLM or llama.cpp:

text

/local http://127.0.0.1:8000/v1
Model quality, hardware requirements, context size, and tool-call support depend on the model and server you choose. Mamo does not automatically download local models.

Supported Providers
Mamo includes definitions for many cloud providers and local servers.

Category	Examples
Major providers	OpenAI, Anthropic, Google Gemini, Mistral, xAI, Cohere
Inference platforms	Groq, Cerebras, Together AI, Fireworks AI, DeepInfra, NVIDIA NIM
Model gateways	OpenRouter, Hugging Face, GitHub Models, Vercel AI Gateway, Requesty
Additional providers	DeepSeek, Qwen, Moonshot, Z.ai, MiniMax, Perplexity, Upstage
Local servers	Ollama, LM Studio, vLLM, Jan, LocalAI, KoboldCpp, GPT4All
Custom endpoints	Services exposing a compatible OpenAI-style API
Model lists are fetched from the selected provider when possible. You can also enter an exact model ID manually.

Compatibility notes:

A registered provider endpoint does not guarantee that every model supports every feature.
Model access depends on your account, region, subscription, and provider availability.
Some services do not expose a complete model list.
Tool calling, reasoning controls, and token limits vary by model.
Use /info to see the number of provider definitions in your installed version.
Commands
Use /help for the full command list, or filter it:

text

/help model
/help session
Navigation and diagnostics
Command	Description
/menu	Open the quick-action menu.
/help [filter]	Browse or search command descriptions.
/doctor	Check the environment and optionally test provider connectivity.
/status	Show detailed application status.
/info	Show system information and feature counts.
/about	About Mamo Code.
/version	Show the application version.
/exit	Exit and attempt to save the active conversation as last.
Models and providers
Command	Description
/key	Configure a cloud provider or custom API endpoint.
/keys	List saved providers without displaying API keys.
/keys rm ID	Remove a saved provider.
/provider	Switch between saved providers.
/model [model-id]	Select a model or enter its exact ID.
/models [filter]	List models exposed by the selected provider.
/local [URL]	Scan local servers or connect to an address.
/favorites	Select a favorite model.
/favorites add	Add the current model to favorites.
/favorites use [N]	Switch to a favorite.
/favorites rm [N]	Remove a favorite.
/credits	Look up OpenRouter account credits.
Behavior
Command	Description
/mode plan|build	Choose read-only planning or implementation mode.
/thinkmode 1-5	Adjust reasoning depth.
/multimode 1-3	Set parallel analysis behavior.
/maxtokens N|off	Set the model output token limit.
/temp N|off	Set temperature or use the provider default.
/lang LANGUAGE|off	Set the response language or allow automatic selection.
/system TEXT	Set additional system instructions.
/system clear	Clear additional system instructions.
/yolo	Toggle automatic approval for model shell commands.
Context and conversations
Command	Description
/context [N|auto]	Show estimated context usage or set a limit.
/compact	Summarize older conversation history.
/compact auto	Toggle automatic compaction.
/add FILE_OR_GLOB	Attach files to the next message.
/undo	Remove the last conversation turn—not file changes.
/retry	Retry the last submitted task after confirmation.
/clear	Clear the conversation and pending attachments.
Sessions and output
Command	Description
/save [name]	Save the current session.
/load [name]	Load a saved session.
/sessions	List saved sessions.
/export [file.md]	Export the conversation as Markdown.
/copy	Copy the latest assistant response.
/backup	Back up configuration and saved sessions.
/restore	Restore a selected backup.
Project and settings
Command	Description
/tree [directory]	Display a directory tree.
/git	Show Git status and recent commits.
/diff [arguments]	Show Git changes.
/cd DIRECTORY	Change the working directory.
/skills	List task shortcuts.
/config	Display settings without provider credentials.
/stats	Show request, token, and session statistics.
/cost	Show tracked usage and cost statistics.
/debug	Toggle diagnostic logging.
/changelog [on|off]	Show changes or toggle the startup notice.
/reset	Reset settings and remove active saved provider credentials.
Direct shell and multiline input
Run an explicit shell command:

text

!git status
!python -m pytest
End a line with \ to continue your message:

text

Review the authentication module. \
Focus on session expiration and error handling. \
Suggest tests before changing anything.
Skills
Skills turn a short slash command into a focused coding task.

Skill	Purpose
/review	Review code for bugs and improvements.
/fix	Investigate and fix a reported issue.
/test	Write automated tests and cover edge cases.
/refactor	Improve structure while preserving intended behavior.
/explain	Explain architecture and code behavior.
/docs	Write documentation.
/commit	Inspect changes and suggest a commit message without committing.
/init	Explore the project and summarize its structure.
/security	Review potential security issues.
/perf	Analyze performance and suggest measurable improvements.
/types	Improve type annotations.
/todo	Find and prioritize TODO/FIXME comments.
/pr	Draft a pull request description.
/migrate	Plan and perform a migration.
/deps	Review dependencies and update risks.
/ci	Create a CI workflow.
/docker	Create container configuration.
/a11y	Audit accessibility and propose fixes.
Examples
text

/review src/api/

/fix Login fails when the session cookie expires

/test src/utils/validators.py

/security src/auth/

/a11y src/components/CheckoutForm.tsx

/docs Explain local development setup in README.md
Skills use the current model, mode, and tool permissions. An accessibility review is not a guarantee of complete WCAG compliance.

Reasoning and Multi-Agent Analysis
Reasoning depth
text

/thinkmode 3
Levels range from 1 to 5. Mamo adjusts its instructions and uses native reasoning parameters when support is detected.

Higher levels may increase response time and token usage. They do not guarantee a better result for every task.

Parallel analysis
text

/multimode 3
Setting	Behavior
1	The main coding agent works without a parallel analysis team.
2	Architect and Reviewer analyze the task, then the main agent continues.
3	Architect, Reviewer, and Implementer analyze the task, then the main agent continues.
The analysis agents have read-only tools. Their reports are supplied to the main agent, which follows your selected plan/build mode.

Parallel analysis creates additional API requests and can increase cost and latency.

Recommended Workflow
1. Inspect before changing
text

/mode plan
/init
/review src/
2. Implement a focused change
text

/mode build
/fix Describe the specific issue here
Review the displayed diffs before approving file changes.

3. Verify the result
text

/test src/changed_module.py
!python -m pytest
/diff
4. Save your progress
text

/save auth-fix
/export auth-fix.md
Safety & Privacy
Mamo works with real files and real shell commands. Review its actions as you would review another developer's changes.

Approval behavior
Model file tools are restricted to the current working directory and its descendants.
File writes and edits require confirmation.
Model shell commands require confirmation unless /yolo is enabled.
Analysis agents use read-only tools.
/mode plan restricts model tools, not explicit commands you type yourself.
What /yolo actually does
/yolo disables confirmation prompts for model shell commands.

It does not improve model intelligence or guarantee better answers. File write/edit tool confirmations remain enabled, but an automatically approved shell command can still modify or delete files.

Use it only when you understand the risks.

Important limitations
Shell execution is not sandboxed. Approved commands can access files and resources beyond the workspace.
!command executes your explicit shell instruction without a model approval prompt.
/undo removes conversation history; it does not revert changes on disk.
/retry may repeat actions that already completed.
File and tool output may be truncated by configured limits.
Compaction summarizes history and may omit details.
Use Git, backups, or a disposable development environment for important work.
Data and credentials
API keys are sent to the provider you explicitly select, rather than broadcast to multiple providers for detection.
Cloud requests can include your prompts, attached files, conversation history, and tool results.
Keys are stored in the local configuration file. They are not encrypted.
Saved sessions and backups may contain sensitive source code or conversation data.
Backups can include API keys and are not encrypted.
Removing a provider or resetting settings does not erase old backups.
Debug logs may contain sensitive request information.
File permissions are restricted where supported, but they are not a replacement for encryption or operating-system access controls.

Configuration & Storage
text

~/.mamo/
├── config.json          # Settings and saved provider credentials
├── config.json.bak      # Previous valid configuration
├── sessions/
│   └── last.json        # Last automatically saved conversation
└── backups/
    └── mamo_*.zip       # Configuration and session backups
Use /config to inspect settings and /status for a detailed runtime overview.

Setting	Purpose
max_tokens	Maximum requested model output tokens; 0 uses the provider default.
tool_output_chars	Character limit for displayed or returned tool output.
ctx_limit	Manual context token limit; 0 uses detected metadata or a fallback.
autocompact	Automatically summarize older conversation history.
lang	Preferred response language.
system_extra	Additional instructions for the assistant.
Context usage is estimated. Cost tracking depends on provider usage information and LiteLLM pricing metadata; your provider dashboard is the billing source of truth.

Make Mamo a Global Command
macOS / Linux
Bash

mkdir -p ~/.local/bin
cp mamo.py ~/.local/bin/mamo
chmod +x ~/.local/bin/mamo
Ensure ~/.local/bin is in your PATH, then run:

Bash

mamo
The Python interpreter used by the script must have Mamo's dependencies installed.

Windows PowerShell
Store the file in a permanent location, such as:

text

C:\mamo\mamo.py
Create your PowerShell profile if necessary:

PowerShell

if (!(Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

notepad $PROFILE
Add:

PowerShell

function mamo {
    python "C:\mamo\mamo.py"
}
Restart PowerShell and run:

PowerShell

mamo
Troubleshooting
No model selected
Configure a provider or connect a local server:

text

/key
/local
No local server found
Check that your server is running and its API is enabled. Try an explicit address:

text

/local http://127.0.0.1:1234/v1
For Docker, WSL, or a separate machine, use an address reachable from the environment running Mamo.

A model is missing from the list
Some providers return incomplete model lists. Enter the exact model ID:

text

/model your-model-id
This selects the ID but does not guarantee that your account has access.

Tool calls fail
Tool calling is not supported by every model or endpoint. Try a tool-capable model and verify your local server's configuration.

Context is too large
text

/compact
If necessary, save your work and start a fresh conversation:

text

/save before-reset
/clear
Copying does not work
/copy requires pyperclip and an available clipboard backend. Headless Linux environments may need an additional system clipboard utility.

Need more diagnostic information?
text

/doctor
/status
/doctor checks model-list connectivity, not actual inference, tool support, or available quota.

Contributing
Bug reports and focused pull requests are welcome.

When reporting a problem, include:

Operating system and Python version.
Mamo and LiteLLM versions.
Provider and model ID.
Steps to reproduce.
Relevant error messages with secrets removed.
Do not include API keys, private source code, or unredacted debug logs.

Open an issue · Submit a pull request

License
Released under the MIT License.

<div align="center">
V3 Built by MaymunMamo
