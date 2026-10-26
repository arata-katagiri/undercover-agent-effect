"""Routed LLM client for Liar's Bar (provider selected by the shared repo-root compute.env).

The experiments were originally run against four local Hugging Face checkpoints
(7-8B instruct models on H100s) through `LocalLLMClient`. This client keeps that
interface -- `chat(messages, model) -> (content, reasoning_content)` -- along with the
per-model sampling parameters, the cap on generated tokens and the response clean-up
the local client applied, so the game logic sees the same kind of text. Only the
inference moves from local GPUs to the shared routed provider config (Nebius default,
OpenRouter fallback) selected by the repo-root compute.env.

`player.py` always imported an `LLMClient` from this module; the file was missing from
the published repository, so this also restores the import.
"""
from __future__ import annotations

import json
import os
import re
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

    # Short name -> Hugging Face / Nebius model id (used as-is; nothing rewritten).
    # llama-3.1-8b and qwen2.5-7b are the original checkpoints. The other two replace
    # models that are no longer readily served (Meta-Llama-3-8B-Instruct and
    # Mistral-7B-Instruct-v0.3); both substitutes are drawn from the authors' own
    # extended model table. See notes/llm-agent-collusion-2.md for the decision.
    MODEL_MAP = {
        "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
        "qwen2.5-7b":   "Qwen/Qwen2.5-7B-Instruct",
        "llama-3.2-3b": "meta-llama/Llama-3.2-3B-Instruct",       # was llama-3-8b
        "ministral-8b": "mistralai/Ministral-8B-Instruct-2410",   # was mistral-7b
    }

    def __init__(self):
        # Client built by the repo-root llm_config utility (compute.env selects provider +
        # base_url + key).
        self._client = make_client()
        print(f"LLMClient initialized. Models: {list(self.MODEL_MAP)}")

    # ------------------------------------------------------------------
    # Sampling: exactly what the local client used, per model family, including its
    # hard cap on new tokens (256 for Llama/Qwen, 512 for the rest) that overrode the
    # 4096 default of chat().
    # ------------------------------------------------------------------
    @staticmethod
    def _sampling(model: str) -> Dict[str, Any]:
        name = model.lower()
        if "llama" in name:
            return dict(max_tokens=256, temperature=0.8, top_p=0.95, top_k=40, repetition_penalty=1.1)
        if "qwen" in name:
            return dict(max_tokens=256, temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.05)
        return dict(max_tokens=512, temperature=0.7, top_p=0.9, top_k=50, repetition_penalty=1.02)

    def chat(self, messages: List[Dict[str, str]], model: str = "llama-3.1-8b",
             max_new_tokens: int = 4096) -> Tuple[str, str]:
        """Chat with a model.

        Returns:
            tuple: (content, reasoning_content) -- reasoning_content is always "" here,
            as it was for the local models.
        """
        if model not in self.MODEL_MAP:
            raise ValueError(
                f"Unsupported model '{model}'. Supported: {list(self.MODEL_MAP)}. "
                f"Not substituting another model — add it to MODEL_MAP or pick a supported one."
            )
        try:
            print(f"LLM Request to {model}: {messages}")
            params = self._sampling(model)
            completion = self._client.chat.completions.create(
                model=resolve_model(self.MODEL_MAP[model]),
                messages=messages,
                max_tokens=min(max_new_tokens, params["max_tokens"]),
                temperature=params["temperature"],
                top_p=params["top_p"],
                # Not first-class in the OpenAI SDK; OpenRouter reads them from the body.
                extra_body={"top_k": params["top_k"], "repetition_penalty": params["repetition_penalty"]},
            )
            response = self._clean_response(completion.choices[0].message.content or "", model)
            print(f"LLM Response: {response}")
            return response, ""
        except Exception as e:
            # Re-raise fatal misconfiguration (bad key / unknown model / bad request) so the game stops
            # with a clear error rather than running on empty responses; only genuinely transient
            # errors are caught and retried.
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

    # ------------------------------------------------------------------
    # Response clean-up, verbatim from the local client.
    # ------------------------------------------------------------------
    def _clean_response(self, response: str, model: str) -> str:
        """Clean response to remove hallucinations and formatting issues"""
        response = re.sub(r'^(Assistant:|AI:|Human:|User:)', '', response).strip()
        response = re.sub(r'\n(Assistant:|AI:|Human:|User:).*$', '', response, flags=re.MULTILINE | re.DOTALL)
        for stop_phrase in ["Human:", "User:", "\n\n---", "```\n\n", "<|", "[INST]"]:
            if stop_phrase in response:
                response = response.split(stop_phrase)[0].strip()
        if response.strip().startswith('{') or '```json' in response:
            response = self._extract_clean_json(response)
        return response.strip()

    def _extract_clean_json(self, response: str) -> str:
        """Extract and clean JSON from response"""
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        for stop_phrase in ["Human:", "User:", "Assistant:"]:
            if stop_phrase in response:
                response = response.split(stop_phrase)[0].strip()
        json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', response)
        if json_match:
            json_str = json_match.group(1)
            json_str = re.sub(r':\s*(?!true\b|false\b|null\b)([A-Za-z][A-Za-z0-9]*)', r': "\1"', json_str)
            json_str = re.sub(r'\[\s*(?!true\b|false\b|null\b)([A-Za-z0-9]+)\s*,\s*(?!true\b|false\b|null\b)([A-Za-z0-9]+)\s*\]', r'["\1", "\2"]', json_str)
            json_str = re.sub(r'\[\s*(?!true\b|false\b|null\b)([A-Za-z0-9]+)\s*\]', r'["\1"]', json_str)
            try:
                parsed = json.loads(json_str)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                return json_str
        return response.strip()

    # Kept for interface compatibility with the local client.
    def list_available_models(self) -> List[str]:
        return list(self.MODEL_MAP)

    def get_model_info(self) -> Dict[str, Any]:
        return {"backend": "openrouter", "models": dict(self.MODEL_MAP)}
