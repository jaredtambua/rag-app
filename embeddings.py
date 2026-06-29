from clients import client
from config import EMBEDDING_MODEL


# create an embedding for text
def embed_text(text):
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)

    return response.data[0].embedding
