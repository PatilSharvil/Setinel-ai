import os, subprocess, shutil
from pathlib import Path
from langchain_core.tools import tool
from .config import project_root, EXCLUDED_DIRS
from .findings import FindingsStore
from .scanner import (run_gitleaks, run_semgrep, search_security_patterns as run_security_patterns, redact, RG)

# global state
STATE = {"root": None, "store": None}

def init_state(root=None, store=None):
    STATE["root"] = (root or project_root()).resolve()
    STATE["store"] = store or FindingsStore()

def root() -> Path:
    if STATE["root"] is None:
        init_state()
    return STATE["root"]

def store() -> FindingsStore:
    if STATE["store"] is None:
        init_state()
    return STATE["store"]

def _inside(p: Path) -> bool:
    try:
        p.resolve().relative_to(root().resolve())
        return True
    except Exception:
        return False

@tool
def list_files(path: str = ".") -> str:
    """List relevant source files and directories in the project."""
    print("  ⏺ Discover project files")
    base = (root() / path).resolve()
    if not _inside(base) and base != root():
        return "Error: path outside project."
    out = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for fn in filenames:
            full = Path(dirpath) / fn
            if not _inside(full):
                continue
            try:
                if full.is_symlink():
                    continue
            except Exception:
                continue
            out.append(str(full.relative_to(root())))
            count += 1
            if count >= 300:
                out.append("... truncated (300 file limit)")
                break
        if count >= 300:
            break
    return "\n".join(out) if out else "No files found."

@tool
def read_file(path: str, start_line: int = 1, end_line: int = 200) -> str:
    """Read a file within the project, with optional line range."""
    print(f"  ⏺ Read {path}")
    target = (root() / path).resolve()
    if not _inside(target):
        return "Error: path outside project or invalid."
    if not target.is_file():
        return "Error: not a file."
    if target.is_symlink():
        return "Error: symlinks not allowed."
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return f"Error reading file: {e}"
    start = max(1, start_line)
    end = min(len(lines), end_line, start + 199)
    chunk = lines[start-1:end]
    text = "".join(chunk)
    text = redact(text)
    if len(text) > 8000:
        text = text[:8000] + "\n... truncated"
    return f"{path} (lines {start}-{end} of {len(lines)}):\n{text}"

@tool
def search_code(query: str, path: str = ".") -> str:
    """Search project code using ripgrep. Returns paths and line numbers."""
    print(f"  ⏺ Search: {query}")
    if not RG:
        return "ripgrep (rg) not installed."
    base = (root() / path).resolve()
    if not _inside(base):
        return "Error: path outside project."
    cmd = ["rg", "-n", "--max-count", "100", "-e", query, str(base)]
    for d in EXCLUDED_DIRS:
        cmd.insert(1, "--glob")
        cmd.insert(2, f"!{d}/**")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "Search timed out."
    except Exception as e:
        return f"Search failed: {e}"
    lines = (proc.stdout or "").splitlines()[:100]
    out = []
    for ln in lines:
        # make relative
        if ln.startswith(str(base)):
            ln = ln[len(str(base))+1:]
        out.append(ln)
    text = "\n".join(out) if out else "No matches."
    if len(text) > 8000:
        text = text[:8000] + "\n... truncated"
    return text

@tool
def scan_secrets() -> str:
    """Run Gitleaks secret scan on the project."""
    print("  ⏺ Run Gitleaks (secret scan)")
    msg = run_gitleaks(root(), store())
    return msg

@tool
def scan_vulnerabilities() -> str:
    """Run Semgrep vulnerability scan on the project."""
    print("  ⏺ Run Semgrep (vulnerability scan)")
    msg = run_semgrep(root(), store())
    return msg

@tool
def search_security_patterns() -> str:
    """Search for common security anti-patterns using ripgrep."""
    print("  ⏺ Search security patterns")
    msg = run_security_patterns(root(), store())
    return msg

@tool
def get_findings(severity: str = "", category: str = "", source: str = "", finding_id: str = "") -> str:
    """Retrieve stored findings with optional filters."""
    print("  ⏺ Read findings")
    res = store().get(
        fid=finding_id or None,
        severity=severity or None,
        category=category or None,
        source=source or None,
    )
    text = store().to_text(res)
    if len(text) > 8000:
        text = text[:8000] + "\n... truncated"
    return text

ALL_TOOLS = [list_files, read_file, search_code, scan_secrets, scan_vulnerabilities, search_security_patterns, get_findings]
