Mamo Code V3
A single-file AI coding assistant for your terminal.
Connect a cloud provider or local model, choose a model, and start coding.

Python
License

Features
Multiple providers — OpenAI, Anthropic, Gemini, Groq, DeepSeek, OpenRouter, and more.
Local models — Ollama, LM Studio, and OpenAI-compatible servers.
Coding tools — read, search, write, and edit files; run approved shell commands.
Plan & build modes — inspect first, implement when ready.
Reasoning & agents — adjustable reasoning depth and parallel analysis.
Sessions — save, load, export, and back up conversations.
New in V3
/menu — quick-action menu.
/doctor — environment and connection checks.
/favorites — save and switch favorite models.
/a11y — accessibility review skill.
Installation
Requires Python 3.9+.

Bash

git clone https://github.com/bilalmuslu321-stack/mamo-code.git
cd mamo-code
python -m pip install litellm rich requests prompt_toolkit pyperclip
python mamo.py
Quick Start
text

/key                 Configure a cloud provider
/local               Connect a running local server
/model               Select a model
/mode plan           Use read-only model tools
/mode build          Enable implementation tools
/help                Show available commands
Ask naturally or use a skill:



Explain this project's architecture.
/review src/
/fix Login fails when the session expires
/test src/auth.py
/a11y src/components/
Useful Commands
Command	Purpose
/thinkmode 1-5	Adjust reasoning depth
/multimode 1-3	Configure parallel analysis
/favorites add	Favorite the current model
/save name	Save the conversation
/load name	Resume a saved session
/compact	Summarize older history
/skills	List task shortcuts
/exit	Exit
Safety
File writes and edits ask for approval. Model shell commands also ask unless /yolo is enabled.

/yolo skips shell approval—it does not improve answer quality. Shell commands are not sandboxed, and /undo does not revert file changes.

Cloud providers receive submitted prompts and code. Configuration and backups may contain unencrypted API keys. Model availability, tool support, and API costs depend on your provider.

License
MIT · Built by MaymunMamo
