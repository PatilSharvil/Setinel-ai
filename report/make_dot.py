dot = r"""digraph AST {
  rankdir=TB;
  bgcolor="white";
  node [shape=box, style="rounded,filled", fontname="Helvetica", fillcolor="#E8F0FE", color="#1A73E8"];
  edge [color="#5F6368"];
  User [label="User (PowerShell/CMD)", fillcolor="#FCE8E6", color="#D93025"];
  CLI [label="CLI (Typer/Rich)", fillcolor="#E6F4EA", color="#1E8E3E"];
  Agent [label="ReAct Agent (LangGraph)", fillcolor="#E8F0FE", color="#1A73E8"];
  LLM [label="LLM Provider\n(Groq / OpenRouter)", fillcolor="#FEF7E0", color="#F9AB00"];
  Tools [label="Tools\nlist_files, read_file, search_code,\nscan_secrets, scan_vulnerabilities,\nsearch_security_patterns, get_findings", fillcolor="#E8F0FE", color="#1A73E8"];
  Scanners [label="External Scanners\nGitleaks, Semgrep, ripgrep", fillcolor="#FCE8E6", color="#D93025"];
  Findings [label="Findings Store", fillcolor="#E6F4EA", color="#1E8E3E"];
  User -> CLI -> Agent;
  Agent -> LLM;
  LLM -> Agent;
  Agent -> Tools;
  Tools -> Scanners;
  Tools -> Findings;
  Findings -> Agent;
}
"""
open(r"C:/Users/patil/OneDrive/Desktop/Projects/appsentinel v2/report/fig/arch.dot","w",encoding="utf-8").write(dot)
import subprocess, os
os.environ["PATH"] = r"C:/Program Files/Graphviz/bin;" + os.environ["PATH"]
subprocess.run(["dot","-Tpng","-Gdpi=200", r"C:/Users/patil/OneDrive/Desktop/Projects/appsentinel v2/report/fig/arch.dot", "-o", r"C:/Users/patil/OneDrive/Desktop/Projects/appsentinel v2/report/fig/arch.png"], check=True)
print("rendered")
