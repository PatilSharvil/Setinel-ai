from sentinel.findings import FindingsStore, Finding

def test_add_and_filter():
    s = FindingsStore()
    s.add(Finding(id="", source="gitleaks", category="secret", severity="high", title="t", path="a.py", line=1))
    assert len(s.findings) == 1
    assert s.get(severity="high")[0].id == "F001"
    assert s.summary()["high"] == 1
    assert "F001" in s.to_text()
