"""Embedding generation utilities.

TODO: Integrate with configurable embedding model providers.
"""


def generate_embedding(text: str, size: int = 8) -> list[float]:
    """Generate a deterministic placeholder embedding vector.

    TODO: Replace placeholder hashing with model inference.
    """
    seed = sum(ord(char) for char in text) % 101
    return [float(seed) / float(i + 1) for i in range(size)]
