import os
from .config import Settings

def make_llm(settings: Settings, provider=None, model=None):
    provider = (provider or settings.provider).lower()
    model = model or settings.model
    if provider == "groq":
        if not settings.groq_key:
            raise RuntimeError("GROQ_API_KEY not set.")
        from langchain_groq import ChatGroq
        m = model or "llama-3.1-8b-instant"
        return ChatGroq(model=m, api_key=settings.groq_key, temperature=0)
    if provider == "openrouter":
        if not settings.openrouter_key:
            raise RuntimeError("OPENROUTER_API_KEY not set.")
        from langchain_openai import ChatOpenAI
        m = model or "openrouter/free"
        return ChatOpenAI(model=m, api_key=settings.openrouter_key, base_url="https://openrouter.ai/api/v1", temperature=0)
    raise RuntimeError(f"Unknown provider: {provider}")
