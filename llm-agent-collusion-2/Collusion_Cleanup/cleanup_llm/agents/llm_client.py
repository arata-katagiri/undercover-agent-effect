"""Routed LLM client for Cleanup (provider selected by the shared repo-root compute.env).

Replaces `LocalLLMClient`, which ran Hugging Face checkpoints on H100s. Same interface
(`generate(...) -> str` and `chat(...) -> (content, reasoning_content)`), same fixed
sampling parameters, same handling of the token budget -- only the inference moves to
the shared routed provider config (Nebius default, OpenRouter fallback) selected by the
repo-root compute.env.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

from poseidon_compute import make_client, resolve_model

# This project's own .env (llm-agent-collusion-2/.env), by explicit path so a .env in
# a parent directory can never leak in.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")


class LLMClient:
    """Chat client with the same contract as the original local client."""

    # Short name -> Hugging Face / Nebius model id (used as-is; nothing rewritten). Entries marked
    # "was ..." replace the paper's original checkpoints with available equivalents; see
    # notes/llm-agent-collusion-2.md.
    MODEL_MAP = {
        # --roster small (the README default)
        "llama-3.1-8b":      "meta-llama/Llama-3.1-8B-Instruct",
        "qwen2.5-7b":        "Qwen/Qwen2.5-7B-Instruct",
        "llama-3.2-3b":      "meta-llama/Llama-3.2-3B-Instruct",             # was llama-3-8b
        "ministral-8b":      "mistralai/Ministral-8B-Instruct-2410",        # was mistral-7b
        # --roster large
        "llama-3.1-70b":     "meta-llama/Llama-3.1-70B-Instruct",
        "llama-3.3-70b":     "meta-llama/Llama-3.3-70B-Instruct",           # was llama-3-70b
        "mistral-small-24b": "mistralai/Mistral-Small-3.2-24B-Instruct-2506",  # was mixtral-8x7b
        "qwen2.5-72b":       "Qwen/Qwen2.5-72B-Instruct",                   # was qwen2.5-32b
    }

    # The local client sampled with these fixed values for every model and ignored the
    # `temperature` argument of generate(). Kept as-is so runs stay comparable.
    SAMPLING = dict(temperature=0.7, top_p=0.9, top_k=50, repetition_penalty=1.1)

    def __init__(self):
        # Client built by the repo-root llm_config utility (compute.env selects provider +
        # base_url + key).
        self._client = make_client()
        print(f"LLMClient initialized. Models: {list(self.MODEL_MAP)}")

    def generate(self, model_name: str, system_prompt: str, user_prompt: str,
                 temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate a response. `temperature` is accepted for interface compatibility
        but, as in the original client, the fixed SAMPLING values are what is sent."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response, _ = self.chat(messages, model=model_name, max_new_tokens=max_tokens)
        return response

    def chat(self, messages: List[Dict[str, str]], model: str = "llama-3.1-8b",
             max_new_tokens: int = 4096) -> Tuple[str, str]:
        """Returns (content, reasoning_content); reasoning_content is always ""."""
        if model not in self.MODEL_MAP:
            raise ValueError(
                f"Unsupported model '{model}'. Supported: {list(self.MODEL_MAP)}. "
                f"Not substituting another model — add it to MODEL_MAP or pick a supported one."
            )
        try:
            print(f"LLM Request to {model}: {messages}")
            completion = self._client.chat.completions.create(
                model=resolve_model(self.MODEL_MAP[model]),
                messages=messages,
                max_tokens=max_new_tokens,
                temperature=self.SAMPLING["temperature"],
                top_p=self.SAMPLING["top_p"],
                extra_body={"top_k": self.SAMPLING["top_k"],
                            "repetition_penalty": self.SAMPLING["repetition_penalty"]},
            )
            response = completion.choices[0].message.content or ""
            print(f"LLM Response: {response}")
            return response, ""
        except Exception as e:
            # Fail loudly on misconfiguration (bad key / unknown model / bad request) instead of
            # silently returning empty text. Only genuinely transient errors are swallowed.
            try:
                from openai import (AuthenticationError, NotFoundError, BadRequestError,
                                    PermissionDeniedError)
                _FATAL = (AuthenticationError, NotFoundError, BadRequestError, PermissionDeniedError)
            except Exception:
                _FATAL = ()
            if _FATAL and isinstance(e, _FATAL):
                raise
            print(f"LLM error: {str(e)}")
            return "", ""

    # Kept for interface compatibility with the local client.
    def list_available_models(self) -> List[str]:
        return list(self.MODEL_MAP)

    def get_model_info(self) -> Dict[str, Any]:
        return {"backend": "openrouter", "models": dict(self.MODEL_MAP)}
