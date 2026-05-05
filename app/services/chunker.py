def chunk_code(text, chunk_size=120):
    lines = text.split("\n")
    chunks = []

    for i in range(0, len(lines), chunk_size):
        chunk = "\n".join(lines[i:i + chunk_size]).strip()

        if chunk:
            chunks.append(chunk)

    return chunks