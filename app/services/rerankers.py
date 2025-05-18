from typing import Any, Dict, List, Optional, Tuple
import statistics
from functools import lru_cache
import threading
from sentence_transformers import CrossEncoder
import os

from app.core import get_logger, settings, LLMError
import app.services.llm as llm_service

# Setup logger
logger = get_logger(__name__)

# Custom domain exceptions
class RerankError(Exception):
    """Base exception for reranking errors."""
    pass

class ValidationError(RerankError):
    """Exception raised when candidate validation fails."""
    pass

class InitializationError(RerankError):
    """Exception raised when cross-encoder initialization fails."""
    pass

class ScoreMismatchError(RerankError):
    """Exception raised when score count doesn't match candidate count."""
    pass

# Thread lock for singleton initialization
_encoder_lock = threading.Lock()
_cross_encoder_instance = None


@lru_cache(maxsize=1)
def get_cross_encoder() -> Optional[CrossEncoder]:
    """
    Return a singleton instance of the cross-encoder.
    Thread-safe, lazy initialization to avoid loading model at import time.
    """
    global _cross_encoder_instance
    if _cross_encoder_instance is None:
        with _encoder_lock:
            # Double-check locking pattern
            if _cross_encoder_instance is None:
                try:
                    logger.info(f"Initializing CrossEncoder with model: {settings.CROSS_ENCODER_MODEL}")
                    _cross_encoder_instance = CrossEncoder(
                        settings.CROSS_ENCODER_MODEL,
                        device=settings.DEVICE
                    )
                    logger.info("CrossEncoder initialized successfully")
                except (OSError, FileNotFoundError, ValueError) as e:
                    logger.error(f"Failed to initialize CrossEncoder: {str(e)}")
                    raise InitializationError(f"Failed to load model: {str(e)}") from e
                except Exception as e:
                    logger.exception(f"Unexpected error initializing CrossEncoder: {str(e)}")
                    raise InitializationError(f"Unexpected error: {str(e)}") from e
    return _cross_encoder_instance


def normalize_scores(
    scores: List[float],
    shift: float = settings.CE_SCORE_SHIFT,
    scale: float = settings.CE_SCORE_SCALE
) -> List[float]:
    """
    Normalize cross-encoder scores to a comparable range.

    Args:
        scores: Raw scores from cross-encoder
        shift: Value to add to each score (default: 5.0 to convert [-5,5] to [0,10])
        scale: Value to multiply each score by after shifting

    Returns:
        List of normalized scores
    """
    return [(float(s) + shift) * scale for s in scores]


def validate_candidates(candidates: List[Dict[str, Any]]) -> None:
    """
    Validate that candidates have the expected structure.

    Args:
        candidates: List of candidate documents

    Raises:
        ValidationError: If candidates structure is invalid
    """
    if not candidates:
        raise ValidationError("No candidates provided for reranking")

    for i, c in enumerate(candidates[:3]):  # Check first few for efficiency
        if "text" not in c:
            raise ValidationError(f"Candidate at index {i} missing 'text' field: {c.keys()}")
        if "id" not in c:
            raise ValidationError(f"Candidate at index {i} missing 'id' field: {c.keys()}")


def fallback_to_llm(
    reason: str,
    query: str,
    candidates: List[Dict[str, Any]],
    top_n: int
) -> List[Dict[str, Any]]:
    """
    Log the reason for fallback and delegate to LLM reranker.

    Args:
        reason: Reason for falling back to LLM
        query: Original query
        candidates: List of candidate documents
        top_n: Number of top candidates to return

    Returns:
        Reranked candidates from LLM reranker
    """
    logger.warning(f"Falling back to LLM reranker: {reason}")
    return llm_service.rerank(query, candidates, top_n)


def rerank_crossencoder(
    query: str, candidates: List[Dict[str, Any]], top_n: int = settings.DEFAULT_RERANK_TOP_N
) -> List[Dict[str, Any]]:
    """Rerank candidates using a local cross-encoder model."""
    try:
        # Validate inputs
        validate_candidates(candidates)

        # Get the cross-encoder model (lazy initialization)
        try:
            ce = get_cross_encoder()
        except InitializationError as e:
            return fallback_to_llm(f"Model initialization failed: {str(e)}", query, candidates, top_n)

        logger.debug(f"Reranking {len(candidates)} candidates with cross-encoder, top_n={top_n}")

        # Create query-document pairs for the cross-encoder
        pairs = [(query, c["text"]) for c in candidates]

        # Limit number of pairs to prevent resource exhaustion
        original_pair_count = len(pairs)
        if len(pairs) > settings.CE_MAX_PAIRS:
            logger.warning(
                f"Limiting cross-encoder pairs from {len(pairs)} to {settings.CE_MAX_PAIRS}"
            )
            pairs = pairs[:settings.CE_MAX_PAIRS]
            candidates = candidates[:settings.CE_MAX_PAIRS]

        # Predict scores in batches
        scores = ce.predict(pairs, batch_size=settings.RERANK_BATCH)

        # Validate output length matches input length
        if len(scores) != len(candidates):
            raise ScoreMismatchError(
                f"Score count mismatch: got {len(scores)} scores for {len(candidates)} candidates"
            )

        # Log raw score statistics (sample-based to avoid log bloat)
        if settings.DEBUG:
            min_score = min(float(s) for s in scores) if scores else 0
            max_score = max(float(s) for s in scores) if scores else 0
            logger.debug(f"Raw score range: min={min_score:.6f}, max={max_score:.6f}")

        # Normalize scores
        normalized_scores = normalize_scores(
            scores,
            shift=settings.CE_SCORE_SHIFT,
            scale=settings.CE_SCORE_SCALE
        )

        # Assign normalized scores to candidates
        for c, s in zip(candidates, normalized_scores):
            c["score"] = float(s)

        # Log normalized scores in debug mode only
        if settings.DEBUG and normalized_scores:
            logger.debug(
                f"Normalized score range: min={min(normalized_scores):.2f}, "
                f"max={max(normalized_scores):.2f}"
            )

        # Calculate mean score to check if we need to fallback
        mean_score = statistics.mean(normalized_scores) if normalized_scores else 0
        logger.debug(f"Cross-encoder normalized mean score: {mean_score:.2f}")

        # Only fall back if normalized mean score is below neutral threshold
        if mean_score < settings.CE_NEUTRAL_THRESHOLD:
            logger.info(
                f"Cross-encoder normalized mean score {mean_score:.2f} below "
                f"threshold {settings.CE_NEUTRAL_THRESHOLD}"
            )
            return fallback_to_llm("Mean score below threshold", query, candidates, top_n)

        # Sort by score (descending) and return top n
        reranked_candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)[:top_n]
        logger.debug(f"Cross-encoder reranking complete, returning top {top_n} candidates")
        return reranked_candidates

    except ValidationError as e:
        return fallback_to_llm(f"Validation failed: {str(e)}", query, candidates, top_n)
    except ScoreMismatchError as e:
        return fallback_to_llm(f"Score mismatch: {str(e)}", query, candidates, top_n)
    except (ValueError, KeyError) as e:
        # Handle predictable errors
        return fallback_to_llm(f"Predictable error: {str(e)}", query, candidates, top_n)
    except (MemoryError, KeyboardInterrupt) as e:
        # Don't catch these critical errors - let them bubble up
        logger.exception(f"Critical error in cross-encoder: {str(e)}")
        raise
    except Exception as e:
        # Log other errors but still try to recover
        logger.exception(f"Unexpected error in cross-encoder: {str(e)}")
        return fallback_to_llm(f"Unexpected error: {str(e)}", query, candidates, top_n)


def rerank(
    query: str, candidates: List[Dict[str, Any]], top_n: int = settings.DEFAULT_RERANK_TOP_N
) -> List[Dict[str, Any]]:
    """Main reranking function that switches between cross-encoder and LLM reranker."""
    logger.info(f"Reranking method selection: USE_CROSS_ENCODER={settings.USE_CROSS_ENCODER}")

    if settings.USE_CROSS_ENCODER:
        try:
            logger.info(f"Using cross-encoder model: {settings.CROSS_ENCODER_MODEL}")
            return rerank_crossencoder(query, candidates, top_n)
        except (KeyboardInterrupt, MemoryError):
            # Let critical errors bubble up
            raise
        except Exception as e:
            return fallback_to_llm(f"Error in cross-encoder flow: {str(e)}", query, candidates, top_n)
    else:
        logger.info("Using LLM reranker as configured")
        return llm_service.rerank(query, candidates, top_n)