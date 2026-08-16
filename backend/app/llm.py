"""LLM clients - CyberBite uses a local private model (Ollama) when possible,
and transparently falls back to a hosted OpenAI-compatible provider (Groq,
OpenAI, OpenRouter, ...) when a key is configured (e.g. serverless hosts where
Ollama cannot run)."""
from __future__ import annotations

import json
import time
from typing import Dict, List, Optional

import httpx

from .config import settings


class OllamaError(Exception):
    pass


class HostedLLMError(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_url).rstrip("/")
        self.model = model or settings.ollama_model
        self._healthy: Optional[bool] = None

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            self._healthy = r.status_code == 200
        except Exception:
            self._healthy = False
        return bool(self._healthy)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
             max_tokens: int = 1500, timeout: int = 120) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            r = httpx.post(f"{self.base_url}/api/chat", json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "").strip()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return self._chat_via_generate(messages, temperature, max_tokens, timeout)
            body = (e.response.text or "").strip()
            detail = body[:300] + ("..." if len(body) > 300 else "")
            raise OllamaError(
                f"Ollama /api/chat returned HTTP {e.response.status_code}. "
                f"Response: {detail or 'no response body'}"
            ) from e
        except httpx.RequestError as e:
            raise OllamaError(f"Ollama request failed: {e}") from e

    def _chat_via_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        timeout: int,
    ) -> str:
        prompt = self._messages_to_prompt(messages)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            r = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            text = data.get("response", "").strip()
            if not text:
                raise OllamaError(
                    "Ollama /api/generate returned an empty response. "
                    "Check model availability with `ollama list`."
                )
            return text
        except httpx.HTTPStatusError as e:
            body = (e.response.text or "").strip()
            detail = body[:300] + ("..." if len(body) > 300 else "")
            raise OllamaError(
                "Ollama does not support /api/chat and the /api/generate fallback failed "
                f"with HTTP {e.response.status_code}. Response: {detail or 'no response body'}"
            ) from e
        except httpx.RequestError as e:
            raise OllamaError(f"Ollama fallback request failed: {e}") from e

    @staticmethod
    def _messages_to_prompt(messages: List[Dict[str, str]]) -> str:
        lines = []
        for m in messages:
            role = m.get("role", "user").strip().upper()
            content = m.get("content", "").strip()
            if not content:
                continue
            lines.append(f"{role}: {content}")
        lines.append("ASSISTANT:")
        return "\n\n".join(lines)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embeddings via Ollama (nomic-embed-text or similar)."""
        vectors = []
        for t in texts:
            payload = {"model": settings.embed_model, "prompt": t}
            r = httpx.post(f"{self.base_url}/api/embeddings", json=payload, timeout=30)
            r.raise_for_status()
            vectors.append(r.json()["embedding"])
        return vectors


class HostedLLMClient:
    """OpenAI-compatible chat completions provider (Groq, OpenAI, OpenRouter...)."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None,
                 api_key: Optional[str] = None):
        self.base_url = (base_url or settings.hosted_llm_url).rstrip("/")
        self.model = model or settings.hosted_llm_model
        self.api_key = api_key if api_key is not None else settings.hosted_llm_api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            r = httpx.get(f"{self.base_url}/models", timeout=5,
                          headers=self._headers())
            return r.status_code == 200
        except Exception:
            return False

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3,
             max_tokens: int = 1500, timeout: int = 120) -> str:
        if not self.api_key:
            raise HostedLLMError(
                "No hosted LLM API key configured (HOSTED_LLM_API_KEY)."
            )
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Some edge networks intermittently reject requests with a transient
        # 401/429/5xx. Retry a few times with backoff before giving up.
        last_error: Optional[Exception] = None
        for attempt in range(4):
            try:
                r = httpx.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                    timeout=timeout,
                )
                if r.status_code == 200:
                    data = r.json()
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if not text:
                        raise HostedLLMError(
                            f"{self.model} returned an empty response. "
                            "Check the model name and your plan's quota."
                        )
                    return text
                body = (r.text or "").strip()
                detail = body[:400] + ("..." if len(body) > 400 else "")
                if r.status_code in (401, 429) or r.status_code >= 500:
                    last_error = HostedLLMError(
                        f"{self.model} returned HTTP {r.status_code}. Response: {detail or 'no response body'}"
                    )
                    time.sleep(0.6 * (attempt + 1))
                    continue
                raise HostedLLMError(
                    f"{self.model} returned HTTP {r.status_code}. Response: {detail or 'no response body'}"
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 429) or e.response.status_code >= 500:
                    last_error = HostedLLMError(
                        f"{self.model} returned HTTP {e.response.status_code}. "
                        f"Response: {(e.response.text or '')[:400]}"
                    )
                    time.sleep(0.6 * (attempt + 1))
                    continue
                raise
            except httpx.RequestError as e:
                last_error = HostedLLMError(f"Hosted LLM request failed: {e}")
                time.sleep(0.6 * (attempt + 1))
                continue
        raise last_error or HostedLLMError(f"{self.model} request failed after retries")


ollama = OllamaClient()
hosted = HostedLLMClient()


def active_provider_name() -> str:
    """Name of the provider currently driving replies."""
    if settings.llm_provider == "hosted":
        return "hosted"
    if settings.llm_provider == "ollama":
        return "ollama"
    return "hosted" if hosted.configured else "ollama"


def get_llm() -> object:
    """Return the LLM client to use based on LLM_PROVIDER."""
    provider = active_provider_name()
    return hosted if provider == "hosted" else ollama


def is_llm_available() -> bool:
    try:
        return get_llm().is_available()
    except Exception:
        return False
