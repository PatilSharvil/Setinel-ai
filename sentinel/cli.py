import os, sys, warnings, logging
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
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
console = Console()

WELCOME = """[orange]✳[/orange]  Welcome to [bold]AST[/bold]!

[dim]while(curious) {[/dim]
    [cyan]scan_project[/cyan]();
    [cyan]dig_deeper[/cyan]();
    [cyan]explain_findings[/cyan]();

    [dim]if (stuck) {[/dim]
        [magenta]keep_thinking[/magenta]();
    [dim]}[/dim]
[dim]}[/dim]"""

def main():
    root = project_root()
    settings = Settings()
    init_state(root, FindingsStore())
    session = Session(settings)
    console.print()
    console.print(WELCOME)
    console.print()
    console.print(f"[dim]project  {root}[/dim]")
    console.print(f"[dim]provider {settings.provider}[/dim]")
    console.print("[dim]/help for commands · natural language is primary[/dim]\n")
    try:
        session.configure()
    except Exception as e:
        console.print(f"[yellow]Provider not configured: {e}. Use /provider to set.[/yellow]")
    while True:
        width = min(console.width, 80)
        console.print("┌" + "─" * (width - 2) + "┐")
        try:
            user = console.input("│ [bold cyan]›[/bold cyan] ")
            console.print("└" + "─" * (width - 2) + "┘")
        except (EOFError, KeyboardInterrupt):
            console.print("└" + "─" * (width - 2) + "┘")
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
            with console.status("[orange]✳[/orange] Simmering...", spinner="dots"):
                answer = session.ask(user)
        except Exception as e:
            answer = f"Error: {e}"
        safe_answer = answer.encode("cp1252", "replace").decode("cp1252")
        console.print(f"\n[orange]✳[/orange]")
        console.print(Markdown(safe_answer))

if __name__ == "__main__":
    app()
    # fallback if run as script
    main()
