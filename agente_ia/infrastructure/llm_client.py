"""
Capa de acceso al modelo de lenguaje.
Abstrae el proveedor concreto (OpenAI, Anthropic, local) del resto del sistema.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LLMRequest:
    system_prompt: str
    user_message: str
    temperature: float = 0.2
    max_tokens: int = 4096
    model: Optional[str] = None


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int]
    raw: Any = None


# ---------------------------------------------------------------------------
# Interfaz base
# ---------------------------------------------------------------------------

class ModelProvider(ABC):
    """Contrato que deben cumplir todos los proveedores de LLM."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        ...


# ---------------------------------------------------------------------------
# Proveedor Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicLLMProvider(ModelProvider):
    """Proveedor usando la API de Anthropic (Claude)."""

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model or self.DEFAULT_MODEL

    @property
    def default_model(self) -> str:
        return self._model

    def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self._api_key)
            model = request.model or self._model

            message = client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                system=request.system_prompt,
                messages=[{"role": "user", "content": request.user_message}],
                temperature=request.temperature,
            )

            content = message.content[0].text if message.content else ""
            usage = {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            }
            return LLMResponse(content=content, model=model, usage=usage, raw=message)

        except ImportError:
            raise RuntimeError(
                "El paquete 'anthropic' no está instalado. "
                "Ejecuta: pip install anthropic"
            )


# ---------------------------------------------------------------------------
# Proveedor OpenAI
# ---------------------------------------------------------------------------

class OpenAILLMProvider(ModelProvider):
    """Proveedor usando la API de OpenAI."""

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model or self.DEFAULT_MODEL

    @property
    def default_model(self) -> str:
        return self._model

    def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            import openai

            client = openai.OpenAI(api_key=self._api_key)
            model = request.model or self._model

            response = client.chat.completions.create(
                model=model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_message},
                ],
            )

            content = response.choices[0].message.content or ""
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
            return LLMResponse(content=content, model=model, usage=usage, raw=response)

        except ImportError:
            raise RuntimeError(
                "El paquete 'openai' no está instalado. "
                "Ejecuta: pip install openai"
            )


# ---------------------------------------------------------------------------
# Proveedor Mock (para tests sin API key)
# ---------------------------------------------------------------------------

class MockLLMProvider(ModelProvider):
    """Proveedor simulado para desarrollo y tests."""

    def __init__(self, fixed_response: str = "# Código generado por MockLLMProvider\npass"):
        self._response = fixed_response

    @property
    def default_model(self) -> str:
        return "mock-model"

    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content=self._response,
            model="mock-model",
            usage={"input_tokens": 0, "output_tokens": 0},
        )


# ---------------------------------------------------------------------------
# Cliente principal (fachada)
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Fachada que el resto del sistema usa para llamar al LLM.
    Encapsula el proveedor concreto y añade logging opcional.
    """

    def __init__(self, provider: ModelProvider, logger=None):
        self._provider = provider
        self._logger = logger

    def complete(self, system_prompt: str, user_message: str, **kwargs) -> str:
        req = LLMRequest(
            system_prompt=system_prompt,
            user_message=user_message,
            **kwargs,
        )
        if self._logger:
            self._logger.log_llm_request(req)

        response = self._provider.complete(req)

        if self._logger:
            self._logger.log_llm_response(response)

        return response.content

    @classmethod
    def from_env(cls, logger=None) -> "LLMClient":
        """
        Crea un cliente detectando el proveedor según las variables de entorno.
        Prioridad: ANTHROPIC_API_KEY > OPENAI_API_KEY > Mock.
        """
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider: ModelProvider = AnthropicLLMProvider()
        elif os.environ.get("OPENAI_API_KEY"):
            provider = OpenAILLMProvider()
        else:
            provider = MockLLMProvider()
        return cls(provider=provider, logger=logger)
