from enum import StrEnum, auto
from typing import TypeAlias


class Provider(StrEnum):
    OPENAI = auto()
    AZURE_OPENAI = auto()
    GROQ = auto()
    OLLAMA = auto()


class OpenAIModelName(StrEnum):
    """https://platform.openai.com/docs/models/gpt-4o"""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


class AzureOpenAIModelName(StrEnum):
    """Azure OpenAI model names"""
    AZURE_GPT_4O = "azure-gpt-4o"
    AZURE_GPT_4O_MINI = "azure-gpt-4o-mini"


class GroqModelName(StrEnum):
    """https://console.groq.com/docs/models"""
    LLAMA_31_8B = "llama-3.1-8b-instant"
    LLAMA_33_70B = "llama-3.3-70b-versatile"
    LLAMA_GUARD_4_12B = "meta-llama/llama-guard-4-12b"


class OllamaModelName(StrEnum):
    """https://ollama.com/search"""
    OLLAMA_GENERIC = "ollama"


AllModelEnum: TypeAlias = (
    OpenAIModelName
    | AzureOpenAIModelName
    | GroqModelName
    | OllamaModelName
)
