from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., env_var="OPENAI_API_KEY")
    EMBEDDING_MODEL: str = Field("text-embedding-3-large", env_var="EMBEDDING_MODEL")
    EMBEDDING_DIMENSIONS: int = Field(1024, env_var="EMBEDDING_DIMENSIONS")
    RERANK_MODEL: str = Field("gpt-4o-mini", env_var="RERANK_MODEL")
    ANSWER_MODEL: str = Field("gpt-4o", env_var="ANSWER_MODEL")

    # Pinecone Configuration
    PINECONE_API_KEY: str = Field(..., env_var="PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = Field(..., env_var="PINECONE_INDEX_NAME")

    # Retrieval Configuration
    DEFAULT_RETRIEVAL_TOP_K: int = Field(25, env_var="DEFAULT_RETRIEVAL_TOP_K")
    DEFAULT_RERANK_TOP_N: int = Field(5, env_var="DEFAULT_RERANK_TOP_N")
    CHUNK_SIZE: int = Field(512, env_var="CHUNK_SIZE")

    # Service Configuration
    DEBUG: bool = Field(False, env_var="DEBUG")

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
