import json, subprocess, shutil, tempfile, os
from pathlib import Path
from .config import EXCLUDED_DIRS
from .findings import Finding

def is_git_tracked(root: Path, rel: str) -> bool:
    if not (root / ".git").exists():
        return False
    try:
        proc = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", rel],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        return proc.returncode == 0
    except Exception:
        return False

def redact(text: str) -> str:
    import re
    patterns = [
        (r"(?i)(api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{8,})['\"]?", r"\1: [REDACTED]"),
        (r"(?i)sk-[A-Za-z0-9]{20,}", "[REDACTED]"),
        (r"(?i)gh[pousr]_[A-Za-z0-9]{20,}", "[REDACTED]"),
    ]
    for p, r in patterns:
        text = re.sub(p, r, text)
    return text

GITLEAKS = shutil.which("gitleaks")
SEMGREP = shutil.which("semgrep")
RG = shutil.which("rg")

def run_gitleaks(root: Path, store, timeout=120):
    if not GITLEAKS:
        return "Gitleaks not installed."
    report = Path(tempfile.gettempdir()) / "gitleaks-report.json"
    try:
        report.unlink(missing_ok=True)
    except Exception:
        pass
    cmd = [GITLEAKS, "detect", "--source", str(root), "--report-format", "json", "--report-path", str(report), "--no-git", "-v"]
    # try git history if repo
    if (root / ".git").exists():
        cmd = [GITLEAKS, "detect", "--source", str(root), "--report-format", "json", "--report-path", str(report), "-v"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(root), encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "Gitleaks timed out."
    except Exception as e:
        return f"Gitleaks execution failed: {e}"
    # gitleaks exits 1 when leaks found
    if not report.exists():
        # maybe no leaks or failure
        if proc.returncode not in (0, 1):
            return f"Gitleaks failed (rc={proc.returncode}): {redact(proc.stderr[:500])}"
        return "Gitleaks completed with no findings."
    try:
        data = json.loads(report.read_text(encoding="utf-8", errors="ignore") or "[]")
    except Exception:
        return f"Gitleaks produced invalid JSON. stderr: {redact(proc.stderr[:300])}"
    count = 0
    for item in data or []:
        rel = item.get("File", "")
        tracked = is_git_tracked(root, rel)
        ev = redact(item.get("Match", "")[:200])
        if tracked:
            ev = ev + " [git-tracked: yes, treat as compromised]"
        else:
            ev = ev + " [git-tracked: no]"
        f = Finding(
            id="",
            source="gitleaks",
            category="secret",
            severity="high",
            title=item.get("RuleID", "secret leak"),
            path=rel,
            line=item.get("StartLine"),
            evidence=ev,
            confidence="high",
        )
        store.add(f)
        count += 1
    return f"Gitleaks completed: {count} finding(s)."

def run_semgrep(root: Path, store, timeout=180):
    if not SEMGREP:
        return "Semgrep not installed."
    cmd = [SEMGREP, "scan", "--config", "auto", "--json", "--quiet", str(root)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(root), encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return "Semgrep timed out."
    except Exception as e:
        return f"Semgrep execution failed: {e}"
    if proc.returncode not in (0, 1):
        return f"Semgrep failed (rc={proc.returncode}): {redact(proc.stderr[:500])}"
    try:
        data = json.loads(proc.stdout or "{}")
    except Exception:
        return f"Semgrep produced invalid JSON. stderr: {redact(proc.stderr[:300])}"
    results = data.get("results", []) or []
    count = 0
    for r in results:
        sev = (r.get("extra", {}).get("severity") or "medium").lower()
        sev_map = {"error": "high", "warning": "medium", "info": "low"}
        severity = sev_map.get(sev, sev)
        f = Finding(
            id="",
            source="semgrep",
            category="vulnerability",
            severity=severity,
            title=r.get("check_id", "semgrep finding"),
            path=str(Path(r.get("path", "")).relative_to(root)) if r.get("path","").startswith(str(root)) else r.get("path",""),
            line=r.get("start", {}).get("line"),
            evidence=redact((r.get("extra", {}).get("message") or "")[:300]),
            confidence="medium",
        )
        store.add(f)
        count += 1
    status = "completed" if proc.returncode in (0,1) else "partial"
    return f"Semgrep {status}: {count} finding(s)."

SECURITY_PATTERNS = [
    ("hardcoded secret", r"(?i)(password|api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
    ("disabled TLS verify", r"(?i)verify\s*=\s*False"),
    ("dangerous eval", r"\beval\s*\("),
    ("dangerous exec", r"\bexec\s*\("),
    ("unsafe subprocess shell", r"subprocess\.(run|call|Popen)\([^)]*shell\s*=\s*True"),
    ("debug mode", r"(?i)debug\s*=\s*True"),
    ("insecure CORS", r"(?i)allow_origins\s*=\s*\[\s*['\"]?\*['\"]?\s*\]"),
    ("security TODO", r"(?i)(TODO|FIXME).*(security|secret|auth|password)"),
]

def search_security_patterns(root: Path, store, timeout=60):
    if not RG:
        return "ripgrep not installed."
    count = 0
    for name, pat in SECURITY_PATTERNS:
        cmd = ["rg", "--json", "-n", "--max-count", "50", pat, str(root)]
        # exclude dirs
        for d in EXCLUDED_DIRS:
            cmd[1:1] = []  # noop placeholder
        # simpler: add globs
        cmd = ["rg", "-n", "--max-count", "50", "-e", pat, str(root)]
        for d in EXCLUDED_DIRS:
            cmd.insert(1, "--glob")
            cmd.insert(2, f"!{d}/**")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        except Exception as e:
            continue
        for line in (proc.stdout or "").splitlines()[:100]:
            # format path:line:content
            parts = line.split(":", 2)
            if len(parts) < 3:
                continue
            p, ln, content = parts[0], parts[1], parts[2]
            try:
                rel = str(Path(p).relative_to(root))
            except Exception:
                rel = p
            if any(seg in Path(rel).parts for seg in EXCLUDED_DIRS):
                continue
            f = Finding(
                id="",
                source="pattern",
                category="heuristic",
                severity="low",
                title=name,
                path=rel,
                line=int(ln) if ln.isdigit() else None,
                evidence=redact(content.strip()[:200]),
                confidence="low",
            )
            store.add(f)
            count += 1
    return f"Pattern scan completed: {count} heuristic match(es)."
