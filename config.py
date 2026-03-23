import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Configuration centrale du projet."""
    model: str = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    temperature: float = float(os.environ.get("OLLAMA_TEMPERATURE", "0.0"))
    max_retries: int = int(os.environ.get("MAX_RETRIES", "3"))
    code_execution_timeout: int = 10
    test_execution_timeout: int = 15


# Instance unique importée partout
config = Config()
