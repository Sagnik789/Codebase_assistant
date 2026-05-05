import logging
import os
import time
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_K_M"


def get_model_name():
    return os.getenv("LLM_MODEL_NAME", DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME


LLM_PROFILE = os.getenv("LLM_PROFILE", "quality").lower()

PROFILE_DEFAULTS = {
    "fast": {
        "max_context_chunks": 3,
        "max_chars_per_chunk": 700,
        "max_tokens": 140,
    },
    "balanced": {
        "max_context_chunks": 4,
        "max_chars_per_chunk": 900,
        "max_tokens": 180,
    },
    "quality": {
        "max_context_chunks": 6,
        "max_chars_per_chunk": 1200,
        "max_tokens": 220,
    },
}

default_profile = PROFILE_DEFAULTS.get(LLM_PROFILE, PROFILE_DEFAULTS["quality"])
MAX_CONTEXT_CHUNKS = int(os.getenv("LLM_MAX_CONTEXT_CHUNKS", str(default_profile["max_context_chunks"])))
MAX_CHARS_PER_CHUNK = int(os.getenv("LLM_MAX_CHARS_PER_CHUNK", str(default_profile["max_chars_per_chunk"])))
MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", str(default_profile["max_tokens"])))

logging.info(
    "Loaded Ollama profile=%s model=%s chunks=%s chunk_chars=%s max_new_tokens=%s",
    LLM_PROFILE,
    get_model_name(),
    MAX_CONTEXT_CHUNKS,
    MAX_CHARS_PER_CHUNK,
    MAX_NEW_TOKENS,
)


def _build_prompt(query, context_chunks):
    context = "\n\n".join([
        f"[Source: {c.get('source', 'unknown')}]\n{c['text'][:MAX_CHARS_PER_CHUNK]}"
        for c in context_chunks[:MAX_CONTEXT_CHUNKS]
    ])

    return f"""
You are a senior backend engineer.

Explain the code using ONLY the relevant parts.

Do NOT repeat code.
Summarize and explain.

Answer format:
1) What it does
2) Key functions
3) Flow

Context:
{context}

Question:
{query}
"""


def generate_answer(query, context_chunks, history=None):
    if history is None:
        history = []

    if not context_chunks:
        return "No relevant code found."

    prompt = _build_prompt(query, context_chunks)
    start = time.time()

    model_name = get_model_name()

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": MAX_NEW_TOKENS,
            "temperature": 0,
        },
    }

    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()
        if not answer:
            return "I could not find this in the codebase."
        return answer
    except Exception as exc:
        logging.exception("Ollama generate failed: %s", exc)
        return f"LLM error: {exc}"
    finally:
        logging.info("LLM (%s via Ollama) took %.2fs", model_name, time.time() - start)