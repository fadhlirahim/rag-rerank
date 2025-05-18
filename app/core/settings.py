from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., env_var="OPENAI_API_KEY")
    EMBEDDING_MODEL: str = Field("text-embedding-3-large", env_var="EMBEDDING_MODEL")
    EMBEDDING_DIMENSIONS: int = Field(1024, env_var="EMBEDDING_DIMENSIONS")
    RERANK_MODEL: str = Field("gpt-4o-mini", env_var="RERANK_MODEL")
    ANSWER_MODEL: str = Field("gpt-4o", env_var="ANSWER_MODEL")

    # Cross-Encoder Configuration
    USE_CROSS_ENCODER: bool = Field(True, env_var="USE_CROSS_ENCODER")
    CROSS_ENCODER_MODEL: str = Field("BAAI/bge-reranker-large", env_var="CROSS_ENCODER_MODEL")
    DEVICE: str = Field("cpu", env_var="DEVICE")
    RERANK_BATCH: int = Field(16, env_var="RERANK_BATCH")
    CE_MAX_PAIRS: int = Field(100, env_var="CE_MAX_PAIRS")
    CE_SCORE_SHIFT: float = Field(5.0, env_var="CE_SCORE_SHIFT")
    CE_SCORE_SCALE: float = Field(1.0, env_var="CE_SCORE_SCALE")
    CE_NEUTRAL_THRESHOLD: float = Field(3.5, env_var="CE_NEUTRAL_THRESHOLD")
    LLM_FALLBACK_THRESHOLD: float = Field(6.5, env_var="LLM_FALLBACK_THRESHOLD")

    # Fiction-specific Configuration
    FICTION_MMR_LAMBDA: float = Field(0.95, env_var="FICTION_MMR_LAMBDA")
    FICTION_CE_THRESHOLD: float = Field(3.0, env_var="FICTION_CE_THRESHOLD")
    FICTION_KEYWORD_BOOST: float = Field(0.3, env_var="FICTION_KEYWORD_BOOST")

    # Theme Boosting Configuration
    THEME_MATCH_BOOST: float = Field(0.2, env_var="THEME_MATCH_BOOST")
    THEME_KEYWORD_BOOST: float = Field(0.15, env_var="THEME_KEYWORD_BOOST")
    NARRATIVE_ELEMENT_BOOST: float = Field(0.5, env_var="NARRATIVE_ELEMENT_BOOST")
    ENABLE_THEME_DETECTION: bool = Field(True, env_var="ENABLE_THEME_DETECTION")

    # Pinecone Configuration
    PINECONE_API_KEY: str = Field(..., env_var="PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = Field(..., env_var="PINECONE_INDEX_NAME")

    # Retrieval Configuration
    DEFAULT_RETRIEVAL_TOP_K: int = Field(50, env_var="DEFAULT_RETRIEVAL_TOP_K")
    DEFAULT_RERANK_TOP_N: int = Field(15, env_var="DEFAULT_RERANK_TOP_N")
    CHUNK_SIZE: int = Field(700, env_var="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(100, env_var="CHUNK_OVERLAP")
    MMR_LAMBDA: float = Field(0.5, env_var="MMR_LAMBDA")

    # Service Configuration
    DEBUG: bool = Field(False, env_var="DEBUG")

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
