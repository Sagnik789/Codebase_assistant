from transformers import pipeline
import torch
import time

# Load model (CPU-safe; will use GPU if available)
generator = pipeline(
    "text-generation",
    model="microsoft/phi-2",
    device_map="auto",
    torch_dtype=torch.float32
)


def generate_answer(query, context_chunks):
    if not context_chunks:
        return "No relevant code found."

    # 🔥 Use slightly larger context for better reasoning
    context = "\n\n".join([
        c["text"][:200].replace("\n", " ")
        for c in context_chunks[:2]
    ])

    # 🔥 Strong prompt (this is what gave you best results)
    prompt = f"""
You are a backend engineer analyzing a real codebase.

Answer ONLY from the given context.

If the answer is not present, say:
"I could not find this in the codebase."

Explain clearly:
- what it does
- key functions involved
- flow (if applicable)

Context:
{context}

Question:
{query}

Answer:
"""

    start = time.time()

    output = generator(
        prompt,
        max_new_tokens=120,   # more tokens = better explanation
        do_sample=False
    )

    print(f"LLM took {time.time() - start:.2f}s")

    text = output[0]["generated_text"]

    # 🔥 Clean output
    answer = text.replace(prompt, "").strip()

    # remove prompt leakage if any
    stop_tokens = ["Context:", "Question:", "You are a backend engineer"]
    for token in stop_tokens:
        if token in answer:
            answer = answer.split(token)[0]

    return answer.strip()