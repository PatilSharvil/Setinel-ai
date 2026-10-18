# AST - AI Security & Code Assistant

## Install (Windows)
```powershell
cd "C:\Users\patil\OneDrive\Desktop\Projects\appsentinel v2"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```
Refresh shell, then `ast`.

## Configure
Copy `.env.example` to `.env`, set `GROQ_API_KEY` or `OPENROUTER_API_KEY`. Default provider groq.

## External tools
- gitleaks, ripgrep available; semgrep optional (pip install semgrep).

## Usage
```powershell
cd C:\projects\my-app
ast
```
Commands: /scan /findings /clear /provider /help /exit.

## Notes
Code snippets may be sent to provider. Read-only by default.
```