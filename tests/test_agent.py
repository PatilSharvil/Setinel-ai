from unittest.mock import MagicMock
from sentinel.agent import Session
from sentinel.config import Settings

def test_agent_no_tool_final():
    s = Settings()
    s.provider = "groq"
    # mock session.configure
    session = Session(s)
    fake_llm = MagicMock()
    from langchain_core.messages import AIMessage
    fake_resp = AIMessage(content="Hello answer")
    fake_llm.bind_tools.return_value.invoke.return_value = fake_resp
    session.llm = fake_llm
    from sentinel.agent import build_agent
    session.graph = build_agent(fake_llm)
    out = session.ask("hi")
    assert "Hello answer" in out
