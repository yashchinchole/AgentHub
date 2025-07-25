from functools import cache
from typing import TypeAlias

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from core.settings import settings
from schema.models import (
    AllModelEnum,
    GroqModelName,
    OllamaModelName,
    OpenAIModelName,
)

_MODEL_TABLE = (
    {m: m.value for m in OpenAIModelName}
    | {m: m.value for m in GroqModelName}
    | {m: m.value for m in OllamaModelName}
)

ModelT: TypeAlias = (
    ChatOpenAI
    | ChatGroq
    | ChatOllama
)


@cache
def get_model(model_name: AllModelEnum, /) -> ModelT:
    api_model_name = _MODEL_TABLE.get(model_name)
    if not api_model_name:
        raise ValueError(f"Unsupported model: {model_name}")

    if model_name in OpenAIModelName:
        return ChatOpenAI(model=api_model_name, temperature=0.5, streaming=True)
    if model_name in GroqModelName:
        if getattr(model_name, 'LLAMA_GUARD_4_12B', None) and model_name == GroqModelName.LLAMA_GUARD_4_12B:
            return ChatGroq(model=api_model_name, temperature=0.0)
        return ChatGroq(model=api_model_name, temperature=0.5)
    if model_name in OllamaModelName:
        if settings.OLLAMA_BASE_URL:
            return ChatOllama(
                model=settings.OLLAMA_MODEL,
                temperature=0.5,
                base_url=settings.OLLAMA_BASE_URL,
            )
        return ChatOllama(model=settings.OLLAMA_MODEL, temperature=0.5)

    raise ValueError(f"Unsupported model: {model_name}")
