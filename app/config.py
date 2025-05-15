import os
from dotenv import load_dotenv

load_dotenv(override=True)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 1024
RERANK_MODEL = "gpt-4o-mini"
ANSWER_MODEL = "gpt-4o"

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Retrieval Configuration
DEFAULT_RETRIEVAL_TOP_K = 25
DEFAULT_RERANK_TOP_N = 5
CHUNK_SIZE = 512