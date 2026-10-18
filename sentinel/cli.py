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

import threading, time
from rich.live import Live
from rich.text import Text


def _run_with_thinking(console, fn):
    box = {}
    def runner():
        try:
            box["value"] = fn()
        except Exception as e:
            box["error"] = e
    t = threading.Thread(target=runner, daemon=True)
    frames = ["", ".", "..", "..."]
    with Live(Text("Thinking", style="#ff8800"), console=console, refresh_per_second=12, transient=True) as live:
        t.start()
        i = 0
        while t.is_alive():
            live.update(Text(f"Thinking{frames[i % 4]}", style="#ff8800"))
            time.sleep(0.12)
            i += 1
        t.join()
    if "error" in box:
        raise box["error"]
    return box.get("value", "")


app = typer.Typer(add_completion=False)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
console = Console()

def _banner():
    try:
        import pyfiglet
        return pyfiglet.figlet_format("Sentinel-AI", font="ansi_shadow", width=max(60, console.width))
    except Exception:
        return "[bold #ff8800]Sentinel-AI[/bold #ff8800]"

WELCOME = """[bold #ff8800]AST[/bold #ff8800]  Welcome!

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
    def show_banner():
        console.print()
        console.print(_banner(), style="#ff8800", markup=False, highlight=False)
        console.print(WELCOME)
        console.print()
    show_banner()
    last_size = os.get_terminal_size().columns
    console.print(f"[dim]project  {root}[/dim]")
    console.print(f"[dim]provider {settings.provider}[/dim]")
    console.print("[dim]/help for commands · natural language is primary[/dim]\n")
    try:
        session.configure()
    except Exception as e:
        console.print(f"[yellow]Provider not configured: {e}. Use /provider to set.[/yellow]")
    while True:
        try:
            size = os.get_terminal_size().columns
        except OSError:
            size = console.width
        if size != last_size:
            last_size = size
            show_banner()
        try:
            user = console.input("[bold cyan]You >[/bold cyan] ")
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
            answer = _run_with_thinking(console, lambda: session.ask(user))
        except Exception as e:
            answer = f"Error: {e}"
        safe_answer = answer.encode("cp1252", "replace").decode("cp1252")
        console.print("\n[bold #ff8800]Agent >[/bold #ff8800]")
        console.print(Markdown(safe_answer))

if __name__ == "__main__":
    app()
    # fallback if run as script
    main()
