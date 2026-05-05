def chunk_code(text: str, chunk_size: int = 150, overlap: int = 30):
    """
    Split code into overlapping line-based chunks.
    """
    lines = text.split("\n")
    chunks = []

    if chunk_size <= 0:
        chunk_size = 150
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    step = chunk_size - overlap
    for start in range(0, len(lines), step):
        end = start + chunk_size
        chunk = "\n".join(lines[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(lines):
            break

    return chunks