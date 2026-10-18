from __future__ import annotations
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from .tools import ALL_TOOLS
from .config import Settings

SYSTEM = ("You are AST, an AI security and code assistant. You have tools to inspect the project, "
          "run security scans, and search code. Use tools ONLY when the user's request requires inspecting or scanning the project. "
          "For greetings, general questions, or explanations, answer directly without calling tools. "
          "Never claim you ran a tool unless you did. Redact secrets. Be concise. "
          "Prioritize by severity/exploitability. Inform user that code snippets may be sent to provider.")

def build_agent(llm):
    tool_node = ToolNode(ALL_TOOLS)
    def agent_node(state: MessagesState):
        messages = [SystemMessage(content=SYSTEM)] + state["messages"]
        resp = llm.bind_tools(ALL_TOOLS).invoke(messages)
        return {"messages": [resp]}
    def should_continue(state: MessagesState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            return "tools"
        return "end"
    g = StateGraph(MessagesState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tool_node)
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    g.add_edge("tools", "agent")
    return g.compile()

class Session:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = None
        self.graph = None
        self.messages: List = []
        self.max_iter = settings.max_iterations
        self._using_fallback = False
    def configure(self, provider=None, model=None):
        from .providers import make_llm
        self.llm = make_llm(self.settings, provider, model)
        self.graph = build_agent(self.llm)
    def reset(self):
        self.messages = []
    def ask(self, text: str) -> str:
        if self.graph is None:
            self.configure()
        self.messages.append(HumanMessage(content=text))
        # bound messages: keep last 40
        if len(self.messages) > 40:
            self.messages = self.messages[-40:]
        try:
            result = self.graph.invoke({"messages": list(self.messages)}, config={"recursion_limit": self.max_iter*4+10})
        except Exception as e:
            if not self._using_fallback and self.settings.fallback_provider:
                try:
                    self.configure(self.settings.fallback_provider, self.settings.fallback_model)
                    self._using_fallback = True
                    result = self.graph.invoke({"messages": list(self.messages)}, config={"recursion_limit": self.max_iter*4+10})
                    msgs = result["messages"]
                    self.messages = [m for m in msgs if not isinstance(m, SystemMessage)]
                    final = ""
                    for m in reversed(msgs):
                        if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
                            final = m.content
                            break
                    return ("[Primary provider failed; switched to fallback "
                            f"{self.settings.fallback_provider}/{self.settings.fallback_model}.] "
                            + (final or "(no response)"))
                except Exception as e2:
                    return f"Agent error: {e}; fallback also failed: {e2}"
            return f"Agent error: {e}"
        msgs = result["messages"]
        # update stored messages (exclude system)
        self.messages = [m for m in msgs if not isinstance(m, SystemMessage)]
        # final answer: last AIMessage without tool_calls
        final = ""
        for m in reversed(msgs):
            if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
                final = m.content
                break
        return final or "(no response)"
