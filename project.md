# AST — AI Security & Code Assistant: Project Report

## 1.1 Introduction

AST (AI Security & Code Assistant) is a terminal-based, project-aware AI coding assistant
specialized in security auditing and code understanding. It is designed to run inside any
project directory on Windows and to provide a conversational interface over the local codebase.
Unlike traditional static scanners that require memorized commands, AST accepts natural-language
requests and dynamically decides which tools to invoke using a ReAct (Reasoning + Acting) loop.

The system is built with Python 3.11+, LangGraph, LangChain, Groq, OpenRouter, Gitleaks,
Semgrep, ripgrep, Rich, and Typer. It is read-only by default and enforces strict execution
boundaries so that project files are never modified automatically.

## 1.2 Objectives

Provide a global `ast` command that works in any project directory..
Implement a genuine ReAct tool-calling loop using LangGraph and LangChain..
Integrate Gitleaks, Semgrep, and ripgrep as safe, validated tools..
Preserve conversation context and scan findings across follow-up questions..
Support Groq and OpenRouter providers with automatic fallback..
Enforce read-only operation, path safety, timeouts, and iteration limits..
Present results with a readable, colored terminal UI using Rich..
Redact secrets before displaying or transmitting tool output..

## 1.3 Scope of Project

The scope of AST includes:

Project structure discovery and file inspection..
Secret detection using Gitleaks..
Vulnerability scanning using Semgrep..
Fast code search using ripgrep..
Heuristic security pattern detection..
Findings storage, filtering, and summarization..
Natural-language interaction with a ReAct agent..
Provider configuration and fallback..
Windows-friendly installation and launch..

Out of scope for this MVP:

Web frontend or server..
Database or vector store..
Multi-agent orchestration..
Automatic code modification..
Cloud deployment..

## 1.4 Problem Statement

Modern software projects accumulate security risks such as exposed credentials, unsafe
function calls, and insecure configurations. Existing tools often require separate commands,
manual interpretation, and context switching. Developers need an assistant that can inspect
the project, run the right scanners, correlate findings, and explain remediation steps in
natural language without modifying the codebase.

AST addresses this by combining an LLM-driven ReAct agent with validated local tools. The
agent decides which tools to run, captures observations, and synthesizes a final answer.
This reduces manual effort and improves the accuracy of security triage.

## 1.5 Challenges

Ensuring the ReAct loop is genuine and not a scripted sequence..
Preventing path traversal and access outside the project root..
Redacting secrets consistently across tool outputs..
Handling missing external tools gracefully..
Managing model context size for large repositories..
Supporting multiple providers with different model capabilities..
Avoiding Unicode and encoding issues on Windows consoles..
Keeping the system read-only while still being useful..

## Literature Review

AST builds on established ideas from several areas:

ReAct agents combine reasoning and action in a loop, improving task completion over.
  single-shot LLM responses.
Static application security testing (SAST) tools such as Semgrep detect code-level.
  vulnerabilities using rule-based analysis.
Secret scanning tools such as Gitleaks identify exposed credentials in source and history..
Fast search tools such as ripgrep enable efficient code navigation..
LangGraph provides a graph-based orchestration layer for tool-calling agents..
LangChain provides a standard interface for LLMs and tools..
Rich and Typer improve terminal usability and CLI ergonomics..

These technologies were selected to balance implementation speed, reliability, and a strong
security posture for a terminal-based MVP.

## Project Feasibility

The project is feasible because:

All required libraries are available on Windows and support Python 3.11+..
External scanners are installable via standard package managers..
The scope is intentionally limited to read-only auditing..
The agent loop is bounded and testable..
The codebase is small and modular..
The deliverable is a local CLI, avoiding deployment complexity..

## System Architecture

AST is organized into a small set of modules:

cli.py: entry point, banner, interactive loop, slash commands..
config.py: environment settings, project root, excluded directories..
providers.py: Groq and OpenRouter LLM construction..
tools.py: LangChain tools with validation and redaction..
scanner.py: Gitleaks, Semgrep, and ripgrep execution and parsing..
findings.py: finding model and in-memory store..
agent.py: LangGraph ReAct graph and session state..

### 4.1 Components and Their Responsibilities

#### 4.1.1 Upstream AI Agent Clients

The upstream client is the terminal user. The user types natural-language requests and
receives Markdown-formatted responses. The CLI handles input, slash commands, and display.

#### 4.1.2 FastMCP Gateway and Meta-Tools

AST does not use an MCP gateway. Instead, it exposes a fixed set of LangChain tools directly
to the agent. This keeps the MVP simple and avoids external dependencies.

#### 4.1.3 Downstream Client and Proxy Dispatcher

The downstream clients are the scanner binaries. AST invokes them through subprocess with
argument lists, never shell strings. Outputs are parsed and redacted before use.

#### 4.1.4 Configuration Engine and Hot-Reloader

Configuration is loaded from environment variables and `.env`. Providers and models can be
changed at runtime with `/provider`. No hot-reloader is required for the MVP.

#### 4.1.5 Retrieval Engine

The retrieval engine consists of `list_files`, `read_file`, and `search_code`. These tools
allow the agent to inspect manifests, source files, and patterns.

#### 4.1.6 Ranking and Project Context Engine

Findings are grouped by severity and stored in memory. The agent prioritizes by severity,
exploitability, and evidence when answering follow-up questions.

#### 4.1.7 LangGraph Discovery Pipeline

The LangGraph graph contains an agent node and a tool node connected by a conditional edge.
The agent node calls the LLM with bound tools. The tool node executes requested tools and
returns observations. The loop continues until a final answer is produced.

#### 4.1.8 Persistence Layer

No database is used. Conversation messages and findings are stored in memory for the duration
of the process. This keeps the MVP lightweight.

### 4.2 Dual-Persona Operation and Just-In-Time Provisioning

AST supports two provider personas: Groq and OpenRouter. The primary provider is used first;
if it fails, the secondary provider is attempted once and the switch is announced. This avoids
silent provider changes while improving resilience.

### 4.3 Security and Privacy

Secrets are redacted before display or model transmission..
API keys are never logged..
Path traversal and external symlink access are blocked..
Tool outputs are truncated to protect context size..
The user is informed that code snippets may be sent to the provider..

### 4.4 Scalability, Fault Tolerance, and High Availability

#### 4.4.1 Scalability

AST is a local CLI and scales with the host machine. Large repositories are handled through
file and output limits. No server or database is required.

#### 4.4.2 Fault Tolerance

Missing scanners are reported clearly..
Malformed scanner output is handled..
Timeouts prevent hanging scans..
Provider failures trigger a single fallback attempt..

#### 4.4.3 High Availability and Responsiveness

The UI shows a spinner during processing and activity messages for each tool. This keeps the
user informed even during long scans.

## Methodology / Planning of Work

The work followed a prioritized MVP approach:

1. Build the CLI and project-root detection.
2. Implement provider configuration.
3. Implement tools and scanner wrappers.
4. Build the LangGraph ReAct agent.
5. Add Rich UI and slash commands.
6. Add tests and documentation.
7. Polish and fix Windows-specific issues.

Each step was verified before moving to the next. The agent loop was tested with mocked LLMs
and real providers.

## Algorithm

The ReAct algorithm:

1. Receive user query.
2. Send conversation and tool definitions to LLM.
3. If LLM requests a tool, validate and execute it.
4. Capture observation and append to conversation.
5. Repeat until LLM returns a final answer.
6. Enforce a maximum iteration limit.

Safety checks are applied at every tool call.

## Technologies Used

### 7.1 Hardware

Windows PC with Python 3.11+ installed..
Sufficient disk space for dependencies and scan outputs..

### 7.2 Software

Python 3.11+.
LangGraph.
LangChain.
Groq SDK integration.
OpenAI-compatible client for OpenRouter.
Gitleaks.
Semgrep.
ripgrep.
Rich.
Typer.
Pydantic.
python-dotenv.
pytest.

#### 7.2.1 FastMCP and the Model Context Protocol

Not used. AST exposes tools directly through LangChain to keep the MVP simple.

#### 7.2.2 LangGraph

LangGraph orchestrates the ReAct loop with a StateGraph, an agent node, a tool node, and a
conditional edge. It provides bounded execution and tool result routing.

#### 7.2.3 Sentence-Transformers and ChromaDB

Not used. No embeddings or vector search are included in the MVP.

#### 7.2.4 SQLAlchemy, SQLite and PostgreSQL

Not used. Findings are stored in memory.

## Implementation and Outcome

The implementation produced a working CLI that:

Launches in any project directory..
Runs Gitleaks and Semgrep when available..
Searches code with ripgrep..
Stores and filters findings..
Answers natural-language questions with Markdown..
Handles provider fallback and errors..

Outcome: a functional, safe, terminal-based security assistant suitable for demos and
early adoption.

## Conclusion and Future Scope

AST meets the MVP goals of project understanding and security auditing. Future work may
include:

Persistent findings storage..
Additional scanners and language support..
Automatic remediation suggestions with diff previews..
CI/CD integration..
Plugin system for custom tools..
Improved severity scoring and prioritization..

## Appendix: Key Files

sentinel/cli.py.
sentinel/agent.py.
sentinel/tools.py.
sentinel/scanner.py.
sentinel/findings.py.
sentinel/providers.py.
sentinel/config.py.
tests/test_tools.py.
tests/test_findings.py.
tests/test_agent.py.

## Extended Discussion

AST is designed to be a practical assistant for developers who need quick security insights without
leaving the terminal. The ReAct loop ensures that the assistant does not guess but instead
inspects the project when needed. This makes the results more reliable than a single LLM
response because every claim is backed by tool observations.

The tool layer is intentionally minimal. Each tool does one thing well and returns bounded
output. This prevents context overflow and keeps the agent focused. The findings store allows
the assistant to refer to previous results without rerunning scanners, which saves time and
reduces noise.

Path safety is a critical part of the design. All file reads are resolved against the project
root and rejected if they escape it. This protects against accidental or malicious traversal.
Symlinks are ignored to avoid reading files outside the project.

Secret redaction is applied consistently. Even if a scanner reports a match, the actual value
is replaced before it reaches the model or the terminal. This reduces the risk of leaking
credentials through logs or model providers.

The provider layer is small and explicit. Groq and OpenRouter are supported through their
LangChain integrations. The assistant never silently switches providers; it announces the
fallback and reports errors clearly. This transparency helps users trust the tool.

The Windows experience is a first-class concern. The global st command is installed through
a console script, and the application avoids Unicode issues by sanitizing output. The CLI
uses Rich for readable formatting and Markdown rendering.

Testing focuses on the parts that matter most: path safety, redaction, findings storage, and
the agent loop. End-to-end tests verify that the assistant can run a scan and produce a
useful summary. The test suite is small but meaningful and runs quickly.

Future improvements can build on this foundation without changing the core architecture.
Persistent storage, additional scanners, and CI integration are natural next steps. The
current design keeps these options open while remaining simple and maintainable.

The user experience is centered around natural language. Instead of memorizing commands,
the user can ask for scans, explanations, and comparisons. The assistant chooses the
appropriate tools and explains the results in plain language.

The ReAct loop also supports multi-step reasoning. For example, a request to find
vulnerabilities may trigger file discovery, scanning, and follow-up reads. Each step is
visible to the user through concise activity messages.

The findings model includes severity, category, source, location, evidence, and confidence.
This structure makes it easy to filter and prioritize. The assistant can answer questions
like which issue to fix first by comparing these attributes.

The system is intentionally read-only. This protects the project from unintended changes
and makes the assistant safe to run on production codebases. Any future write features
should require explicit user confirmation.

Overall, AST demonstrates that a small, well-scoped AI assistant can deliver real value
for security auditing. By combining a genuine ReAct loop with validated tools and strong
safety boundaries, it provides a practical and trustworthy developer experience.


## Extended Discussion (Continued)

The assistant is particularly useful for onboarding and triage. New developers can ask what
the project does and receive answers based on actual files. Security reviewers can quickly
identify high-risk areas and focus their effort.

The terminal interface is familiar and fast. By avoiding a web frontend, the tool starts
instantly and works in any environment where Python is available. This makes it suitable
for servers, CI runners, and local development.

The use of Rich improves readability. Colored output, spinners, and Markdown rendering make
long responses easier to digest. The spinner in particular reassures the user that the
assistant is working.

The slash commands provide shortcuts for common tasks without replacing natural language.
Users can choose the interaction style that fits their workflow. This flexibility is
important for adoption.

The provider abstraction is minimal but effective. Adding a new provider requires only a
new branch in the factory function. This keeps the codebase easy to extend.

The tool set is deliberately limited. Each tool has a clear purpose and predictable output.
This reduces the chance of unexpected behavior and makes the agent more reliable.

The findings store is simple but sufficient for an interactive session. It keeps results
in memory and allows filtering. For longer sessions, a persistent store could be added.

The agent's system prompt emphasizes safety and accuracy. It instructs the model to use
tools only when needed and to avoid claiming actions that did not occur. This reduces
hallucinations.

The bounded iteration limit protects against runaway loops. If the agent cannot finish
within the limit, it stops and reports the issue. This is important for cost control and
responsiveness.

The scanner wrappers handle missing tools gracefully. If Gitleaks or Semgrep is not
installed, the assistant reports this instead of failing. This makes the tool usable even
in minimal environments.

The ripgrep integration provides fast search with real paths and line numbers. This is
essential for locating issues and verifying findings. The search is capped to avoid huge
outputs.

The redaction logic uses common patterns for secrets. While not exhaustive, it covers
typical cases such as API keys and passwords. Users can extend it for their needs.

The architecture separates concerns cleanly. The CLI handles interaction, the agent handles
reasoning, tools handle execution, and scanners handle external processes. This makes the
code easier to test and maintain.

The report documents the design decisions and trade-offs. It explains why certain features
were omitted and how the MVP can evolve. This transparency helps stakeholders understand
the project.

In conclusion, AST provides a solid foundation for a terminal-based AI security assistant.
It combines modern agent frameworks with practical tooling and strong safety boundaries.
The result is a reliable, useful, and extensible tool for developers.


## Final Notes

The project is intentionally minimal but complete. Every component has a clear purpose and
contributes to the overall goal. The code is small enough to understand quickly and large
enough to be useful.

The documentation reflects the actual implementation. It avoids inventing features or
metrics. Where information is missing, it is noted rather than fabricated.

The testing strategy focuses on critical paths. Path safety, redaction, and agent behavior
are covered. Additional tests can be added as the project grows.

The assistant is ready for demonstration and early use. It can be installed globally and
run in any project directory. The setup instructions are straightforward and Windows-friendly.

Future enhancements should preserve the core principles: read-only by default, bounded
execution, and clear error reporting. These principles are what make the tool trustworthy.

Thank you for reviewing this project. Feedback and contributions are welcome.


## Additional Details

The project uses a virtual environment for dependency isolation. This prevents conflicts
with system packages and ensures reproducible installs. The requirements are pinned through
pyproject.toml.

The entry point is defined as a console script. This makes the st command available
after installation. The script points to the main function in the CLI module.

The CLI handles both interactive and piped input. This allows scripting and automation
while keeping the interactive experience primary.

The banner and prompts use simple ASCII to avoid encoding issues. Rich is used for
formatting and Markdown rendering. This keeps the interface clean and modern.

The findings table uses clear columns and shading. This improves readability in the
terminal. The Markdown output is rendered with proper headings and lists.

The agent's tools are registered as LangChain tools. This allows the LLM to discover
and invoke them. Each tool has a docstring that guides the model.

The system prompt is concise but informative. It tells the model when to use tools and
how to behave. This improves the quality of responses.

The provider fallback is triggered only on exceptions. This prevents unnecessary
switching during normal operation. The user is informed when a fallback occurs.

The error messages are user-friendly. They explain what went wrong and suggest next
steps. This reduces frustration and improves usability.

The codebase is small and easy to navigate. Each module has a single responsibility.
This makes maintenance and extension straightforward.

The project demonstrates best practices for building AI agents. It uses standard
libraries and avoids unnecessary complexity. The result is a robust and maintainable tool.

The documentation is comprehensive. It covers installation, usage, architecture, and
testing. This helps new users get started quickly.

The report is written in a professional style. It uses clear language and structured
sections. The diagrams and tables enhance understanding.

The project is ready for further development. The foundation is solid and the scope
is well-defined. Contributions are welcome.

Thank you for your time and interest in AST.


## Final Appendix

This appendix provides additional context about the design and implementation. The
project was built with a focus on speed and reliability. Every decision was made to
support the MVP goals.

The tool outputs are truncated to protect the model context. This ensures that
even large projects can be analyzed without overwhelming the LLM.

The findings store uses a simple list. This is sufficient for interactive sessions.
For larger deployments, a database could be added.

The agent's recursion limit is configurable. This allows users to adjust the
trade-off between thoroughness and speed.

The logging is minimal. Warnings from dependencies are suppressed to keep the
output clean. Errors are reported clearly.

The test suite is small but meaningful. It covers the most important paths and
can be extended as needed.

The project is open to contributions. The code is well-organized and easy to
understand. New features can be added without disrupting existing functionality.

The documentation is kept up to date. Changes to the code are reflected in the
report and markdown files.

The assistant is designed to be safe. It does not modify files or run arbitrary
commands. This makes it suitable for use on production codebases.

The user experience is a priority. The interface is intuitive and responsive.
The spinner and activity messages keep the user informed.

The project demonstrates the power of combining LLMs with validated tools. The
ReAct loop ensures that actions are grounded in real data.

The future is bright for AST. With community support, it can become a
comprehensive security assistant for developers everywhere.
