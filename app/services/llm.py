from transformers import pipeline
import time

generator = pipeline(
    "text-generation",
    model="microsoft/phi-2",
    device_map="auto",
    pad_token_id=50256
)

def generate_answer(query, context_chunks, history=[]):
    if not context_chunks:
        return "No relevant code found."

    # 🔥 KEEP STRUCTURE — NO FLATTENING
    context = "\n\n".join([
        c["text"][:300]
        for c in context_chunks[:2]
    ])

    # 🔥 SIMPLE PROMPT (THIS IS KEY)
    prompt = f"""
You are a backend engineer analyzing a real codebase.

Answer ONLY from the given context.

If not found, say:
"I could not find this in the codebase."

Context:
{context}

Question:
{query}

Answer with:
- explanation
- key functions
- flow if applicable
"""

    start = time.time()

    output = generator(
        prompt,
        max_new_tokens=120,
        do_sample=False
    )

    print(f"LLM took {time.time() - start:.2f}s")

    # 🔥 CLEAN ONLY PROMPT (NOTHING ELSE)
    text = output[0]["generated_text"]
    answer = text.replace(prompt, "").strip()

    return answer