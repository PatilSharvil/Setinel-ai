from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json

@dataclass
class Finding:
    id: str
    source: str
    category: str
    severity: str
    title: str
    path: str
    line: Optional[int] = None
    evidence: str = ""
    confidence: str = "medium"

    def to_dict(self):
        return asdict(self)


class FindingsStore:
    def __init__(self):
        self.findings: List[Finding] = []
        self._counter = 0

    def reset(self):
        self.findings = []
        self._counter = 0

    def add(self, finding: Finding):
        if not finding.id:
            self._counter += 1
            finding.id = f"F{self._counter:03d}"
        else:
            # ensure counter
            try:
                n = int(finding.id.lstrip("F"))
                if n > self._counter:
                    self._counter = n
            except Exception:
                pass
        self.findings.append(finding)
        return finding.id

    def get(self, fid=None, severity=None, category=None, source=None):
        out = self.findings
        if fid:
            out = [f for f in out if f.id == fid]
        if severity:
            out = [f for f in out if f.severity.lower() == severity.lower()]
        if category:
            out = [f for f in out if f.category.lower() == category.lower()]
        if source:
            out = [f for f in out if f.source.lower() == source.lower()]
        return out

    def summary(self):
        counts = {}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    def to_text(self, findings=None):
        findings = findings if findings is not None else self.findings
        lines = []
        for f in findings:
            loc = f.path + (f":{f.line}" if f.line else "")
            lines.append(f"{f.id} [{f.severity}] {f.title} ({f.source}/{f.category}) @ {loc}")
            if f.evidence:
                lines.append(f"   evidence: {f.evidence}")
        return "\n".join(lines) if lines else "No findings."
