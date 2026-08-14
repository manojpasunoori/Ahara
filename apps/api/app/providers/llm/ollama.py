from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx


class LLMProviderError(RuntimeError):
    pass


class LLMProviderUnavailableError(LLMProviderError):
    pass


class LLMProviderTimeoutError(LLMProviderError):
    pass


class LLMProviderResponseError(LLMProviderError):
    pass


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate_structured(self, system_prompt: str, user_message: str, schema: dict[str, Any]) -> dict[str, Any]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class OllamaLLMProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float, client: httpx.Client | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._client = client

    @property
    def model(self) -> str:
        return self._model

    def is_available(self) -> bool:
        try:
            response = self._request("GET", "/api/tags")
            payload = response.json()
            return any(item.get("name") == self._model for item in payload.get("models", []) if isinstance(item, dict))
        except (httpx.HTTPError, ValueError):
            return False

    def generate_structured(self, system_prompt: str, user_message: str, schema: dict[str, Any]) -> dict[str, Any]:
        payload = {"model": self._model, "stream": False, "format": schema, "think": False, "options": {"temperature": 0.0, "num_predict": 220}, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]}
        try:
            response = self._request("POST", "/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
            content = body.get("message", {}).get("content") if isinstance(body, dict) else None
            if not isinstance(content, str):
                raise LLMProviderResponseError("Ollama returned no structured content.")
            parsed = __import__("json").loads(content)
            if not isinstance(parsed, dict):
                raise LLMProviderResponseError("Ollama structured content was not an object.")
            return parsed
        except httpx.TimeoutException as error:
            raise LLMProviderTimeoutError("Ollama inference timed out.") from error
        except httpx.HTTPError as error:
            raise LLMProviderUnavailableError("Ollama is unavailable.") from error
        except ValueError as error:
            raise LLMProviderResponseError("Ollama returned invalid structured output.") from error

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if self._client is not None:
            return self._client.request(method, f"{self._base_url}{path}", timeout=self._timeout_seconds, **kwargs)
        with httpx.Client(timeout=self._timeout_seconds) as client:
            return client.request(method, f"{self._base_url}{path}", **kwargs)