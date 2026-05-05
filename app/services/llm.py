import logging
import os
from transformers import pipeline
import time

MODEL_NAME = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-Coder-7B-Instruct")
LLM_PROFILE = os.getenv("LLM_PROFILE", "quality").lower()

PROFILE_DEFAULTS = {
    "fast": {
        "max_context_chunks": 3,
        "max_chars_per_chunk": 700,
        "max_new_tokens": 140,
    },
    "balanced": {
        "max_context_chunks": 4,
        "max_chars_per_chunk": 900,
        "max_new_tokens": 180,
    },
    "quality": {
        "max_context_chunks": 6,
        "max_chars_per_chunk": 1200,
        "max_new_tokens": 220,
    },
}

default_profile = PROFILE_DEFAULTS.get(LLM_PROFILE, PROFILE_DEFAULTS["quality"])
MAX_CONTEXT_CHUNKS = int(os.getenv("LLM_MAX_CONTEXT_CHUNKS", str(default_profile["max_context_chunks"])))
MAX_CHARS_PER_CHUNK = int(os.getenv("LLM_MAX_CHARS_PER_CHUNK", str(default_profile["max_chars_per_chunk"])))
MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_NEW_TOKENS", str(default_profile["max_new_tokens"])))

generator = pipeline(
    "text-generation",
    model=MODEL_NAME,
    device_map="auto",
    trust_remote_code=True
)

logging.info(
    "Loaded LLM profile=%s model=%s chunks=%s chunk_chars=%s max_new_tokens=%s",
    LLM_PROFILE,
    MODEL_NAME,
    MAX_CONTEXT_CHUNKS,
    MAX_CHARS_PER_CHUNK,
    MAX_NEW_TOKENS,
)

def generate_answer(query, context_chunks, history=None):
    if history is None:
        history = []
    if not context_chunks:
        return "No relevant code found."

    context = "\n\n".join([
        f"[Source: {c.get('source', 'unknown')}]\n{c['text'][:MAX_CHARS_PER_CHUNK]}"
        for c in context_chunks[:MAX_CONTEXT_CHUNKS]
    ])

    prompt = f"""
You are a senior backend engineer analyzing a real codebase.

Answer ONLY from the provided context snippets.
If the context is insufficient, explicitly state what is missing.

Output format:
1) Short answer
2) Key functions/files
3) Execution flow
4) Uncertainties

Context:
{context}

Question:
{query}

"""

    start = time.time()

    output = generator(
        prompt,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=False,
        temperature=0.0
    )

    logging.info("LLM (%s) took %.2fs", MODEL_NAME, time.time() - start)

    # 🔥 CLEAN ONLY PROMPT (NOTHING ELSE)
    text = output[0]["generated_text"]
    answer = text.replace(prompt, "").strip()

    return answer
