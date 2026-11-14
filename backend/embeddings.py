import config
from clients import get_client
from fakes import fake_embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts in batches, one API call per batch."""
    if not texts:
        return []

    if config.fake_openai():
        return fake_embeddings(texts)

    embeddings = []
    size = config.EMBEDDING_BATCH_SIZE

    for start in range(0, len(texts), size):
        batch = texts[start : start + size]
        response = get_client().embeddings.create(
            model=config.EMBEDDING_MODEL, input=batch
        )
        embeddings.extend(item.embedding for item in response.data)

    return embeddings


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
