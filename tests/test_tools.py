import tempfile, os
from pathlib import Path
from sentinel.tools import init_state, read_file, list_files
from sentinel.findings import FindingsStore

def test_path_traversal_blocked():
    with tempfile.TemporaryDirectory() as d:
        init_state(Path(d), FindingsStore())
        # create file outside? attempt traversal
        res = read_file.invoke({"path": "../outside.txt"})
        assert "outside project" in res or "not a file" in res or "Error" in res

def test_read_file_redacts():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.py"
        p.write_text('password = "supersecret123456"\n')
        init_state(Path(d), FindingsStore())
        res = read_file.invoke({"path": "a.py"})
        assert "REDACTED" in res
        assert "supersecret123456" not in res

def test_list_files():
    with tempfile.TemporaryDirectory() as d:
        (Path(d)/"x.py").write_text("print(1)")
        init_state(Path(d), FindingsStore())
        res = list_files.invoke({"path": "."})
        assert "x.py" in res
