from dotenv import load_dotenv
from openai import OpenAI

import chromadb

from config import VECTORSTORE_PATH, COLLECTION_NAME

# load environment variables
load_dotenv()


# openai client
client = OpenAI()


# chroma client
chroma_client = chromadb.PersistentClient(path=VECTORSTORE_PATH)


# document collection
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
