"""
The shared contract between Member A's retrieval code and Member B's
agentic/generation code. Both sides depend on this file — change it only
after checking with your teammate, since it will break the other person's code.
"""
from dataclasses import dataclass, asdict
import json


@dataclass
class Chunk:
    id: str            # unique id, e.g. "doc0042_chunk03"
    text: str           # the actual chunk text
    source: str          # filename or doc title this chunk came from
    score: float = 0.0    # similarity score from retrieval (filled in by retriever.py)

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Chunk":
        return Chunk(**d)


def save_chunks(chunks: list[Chunk], path):
    """Write chunks to a .jsonl file, one JSON object per line."""
    with open(path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict()) + "\n")


def load_chunks(path) -> list[Chunk]:
    """Read chunks back from a .jsonl file."""
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(Chunk.from_dict(json.loads(line)))
    return chunks
