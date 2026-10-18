import os, warnings, logging
from pathlib import Path
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from .config import Settings, project_root, EXCLUDED_DIRS
from .tools import init_state
from .findings import FindingsStore
import contextlib, io
with contextlib.redirect_stderr(io.StringIO()):
    from .agent import Session

app = typer.Typer(add_completion=False)
console = Console()

BANNER = """+--------------------------------------------------+
|       AST - AI Security & Code Assistant         |
|       ReAct Agent | Project-aware Chat           |
+--------------------------------------------------+"""

def main():
    root = project_root()
    settings = Settings()
    init_state(root, FindingsStore())
    session = Session(settings)
    console.print(Panel(BANNER, style="cyan"))
    console.print(f"Project: {root}")
    console.print(f"Provider: {settings.provider}")
    console.print("Type /help for commands. Natural language is primary.\n")
    try:
        session.configure()
    except Exception as e:
        console.print(f"[yellow]Provider not configured: {e}. Use /provider to set.[/yellow]")
    while True:
        try:
            user = console.input("[bold green]You >[/bold green] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye.")
            break
        user = user.strip()
        if not user:
            continue
        if user.startswith("/"):
            cmd = user.split()[0].lower()
            if cmd == "/exit":
                break
            elif cmd == "/clear":
                session.reset()
                console.print("Conversation cleared.")
                continue
            elif cmd == "/help":
                console.print("/scan /findings /clear /provider /exit")
                continue
            elif cmd == "/findings":
                from .tools import store
                console.print(store().to_text())
                continue
            elif cmd == "/scan":
                user = "Run a complete security scan of this project and summarize findings."
            elif cmd == "/provider":
                parts = user.split()
                if len(parts) >= 2:
                    settings.provider = parts[1].lower()
                    if len(parts) >= 3:
                        settings.model = parts[2]
                    try:
                        session.configure(settings.provider, settings.model or None)
                        console.print(f"Provider set to {settings.provider} model {settings.model or '(default)'}")
                    except Exception as e:
                        console.print(f"Error: {e}")
                else:
                    console.print("Usage: /provider groq|openrouter [model]")
                continue
            else:
                console.print("Unknown command.")
                continue
        try:
            with console.status("[bold blue]AST >[/bold blue] Thinking...", spinner="dots"):
                answer = session.ask(user)
        except Exception as e:
            answer = f"Error: {e}"
        safe_answer = answer.encode("cp1252", "replace").decode("cp1252")
        console.print(f"\n[bold blue]AST >[/bold blue]")
        console.print(Markdown(safe_answer))

if __name__ == "__main__":
    app()
    # fallback if run as script
    main()
