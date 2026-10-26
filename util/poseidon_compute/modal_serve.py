"""vLLM model server on Modal — an OpenAI-compatible endpoint for experiments Nebius can't serve.

You don't run this directly. `poseidon_compute.hosted_model` runs it ephemerally around an experiment (boots a
model, wires the endpoint into `llm_config`, tears it down):

    poseidon-host --model Qwen/Qwen2.5-7B-Instruct --gpu A10G -- <your experiment command>

SETUP (one-time): `pip install modal && modal setup` (browser auth). Gated models (e.g. Llama) need a
HF token: `modal secret create huggingface HF_TOKEN=hf_...`. Pick a GPU that fits the model: A10G (24GB)
~ up to 8B · A100-40GB ~ up to 32B · H100 for 70B (pass `--gpu` to hosted_model).

Advanced: `modal deploy poseidon_compute.modal_serve` gives a persistent shared endpoint; most teams won't need
it (the ephemeral hosted_model flow is simpler and leaves nothing running). Scaffolding ahead of live
credits — validate once your Modal account is funded.
"""
import os
import subprocess

import modal

# ---- config (override via env at deploy time) ----------------------------------------------------
MODEL = os.environ.get("MODAL_SERVE_MODEL", "Qwen/Qwen2.5-7B-Instruct")  # open by default (no HF gate)
GPU = os.environ.get("MODAL_SERVE_GPU", "A10G")
MAX_MODEL_LEN = int(os.environ.get("MODAL_SERVE_MAX_MODEL_LEN", "8192"))
VLLM_PORT = 8000

app = modal.App("hackathon-serve")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.6.6", "huggingface_hub[hf_transfer]==0.26.2")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# HF token (for gated models) + optional endpoint API key. ``Secret.from_name`` is lazy: it returns a
# handle even when the named secret does not exist, and Modal only raises ``NotFoundError`` later when
# the app starts.  Therefore a try/except around ``from_name`` cannot make a secret optional.  List the
# secrets that actually exist first and attach only those handles.
try:
    _existing_secret_names = {secret.name for secret in modal.Secret.objects.list()}
except Exception as exc:
    # Open models such as the default Qwen checkpoint need no secret.  If listing is unavailable, start
    # without optional secrets and let gated-model access checks report an actionable error later.
    print(f"[modal_serve] note: could not list optional Modal secrets ({exc}); continuing without them.")
    _existing_secret_names = set()

_secrets = []
for name in ("huggingface", "modal-serve"):
    if name in _existing_secret_names:
        _secrets.append(modal.Secret.from_name(name))
    else:
        print(f"[modal_serve] note: optional Modal secret '{name}' not found — skipping. "
              f"('huggingface' is needed for GATED models like Llama; 'modal-serve' only protects "
              f"the endpoint with a key.)")


@app.function(
    image=image,
    gpu=GPU,
    timeout=24 * 3600,
    scaledown_window=300,            # spin down after 5 min idle to save credits
    secrets=_secrets,
)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=VLLM_PORT, startup_timeout=900)
def serve():
    """Launch vLLM's OpenAI-compatible server; Modal proxies it to a public URL."""
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--served-model-name", MODEL,
        # Qwen advertises a 32k context window, but its 7B weights plus a 32k KV cache do not fit on
        # a 24 GB A10G.  The tournament prompts are much smaller, so 8k avoids an unnecessary startup
        # failure while remaining configurable through MODAL_SERVE_MAX_MODEL_LEN.
        "--max-model-len", str(MAX_MODEL_LEN),
        "--disable-log-requests",
    ]
    api_key = os.environ.get("MODAL_SERVE_API_KEY")
    if api_key:
        cmd += ["--api-key", api_key]   # clients must send this as their key
    subprocess.Popen(" ".join(cmd), shell=True)
