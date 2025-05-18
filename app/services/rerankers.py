from typing import Any, Dict, List, Optional, Tuple
import statistics
import re
from functools import lru_cache
import threading
from sentence_transformers import CrossEncoder
import os

from app.core import get_logger, settings, LLMError
import app.services.llm as llm_service
from app.services.theme_tagging import tag_themes, tokenize

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


def apply_theme_based_boost(query: str, candidates: List[Dict[str, Any]], is_fiction: bool = False) -> List[Dict[str, Any]]:
    """
    Apply sophisticated theme-based boosting for fiction content.
    Uses theme_tagging to identify narrative themes in both query and documents.

    Args:
        query: User query
        candidates: List of candidate documents
        is_fiction: Flag indicating if content is fiction

    Returns:
        List of candidates with boosted scores
    """
    if not is_fiction or not settings.ENABLE_THEME_DETECTION:
        return candidates  # Only apply for fiction when enabled

    # Extract themes from query
    query_themes = tag_themes(query)

    if not query_themes:
        # Fallback to simple tokenization if no themes detected
        query_tokens = set(tokenize(query))
        if not query_tokens:
            return candidates

        logger.debug(f"No themes detected in query, using token matching with {len(query_tokens)} tokens")

        # Apply token-based boosting
        for candidate in candidates:
            text = candidate["text"].lower()
            token_matches = sum(1 for token in query_tokens if token in text and len(token) > 3)

            # Special handling for narrative query elements
            narrative_elements = ["witness", "wedding", "church", "bride", "ceremony", "chapel"]
            narrative_matches = sum(1 for elem in narrative_elements if elem in text and elem in query.lower())

            if token_matches > 0 or narrative_matches > 0:
                boost = settings.FICTION_KEYWORD_BOOST * token_matches + settings.NARRATIVE_ELEMENT_BOOST * narrative_matches
                candidate["score"] = candidate["score"] * (1 + boost)
                logger.debug(f"Token boosted candidate {candidate['id'][:8]} by {boost:.2f} (tokens: {token_matches}, narrative: {narrative_matches})")
    else:
        # Apply theme-based boosting
        logger.info(f"Identified themes in query: {', '.join(query_themes.keys())}")

        for candidate in candidates:
            # Get themes in candidate text
            candidate_themes = tag_themes(candidate["text"])

            if not candidate_themes:
                continue

            # Calculate theme overlap
            theme_overlap = set(query_themes.keys()) & set(candidate_themes.keys())

            # Calculate keyword overlap within matching themes
            keyword_overlap_count = 0
            theme_match_strength = 0

            for theme in theme_overlap:
                # Count overlapping keywords within each theme
                query_keywords = set(query_themes[theme])
                candidate_keywords = set(candidate_themes[theme])
                keyword_overlap = query_keywords & candidate_keywords
                keyword_overlap_count += len(keyword_overlap)

                # Apply stronger boost for direct keyword matches
                if keyword_overlap:
                    theme_match_strength += 1.5
                else:
                    theme_match_strength += 1.0

                logger.debug(f"Theme match: {theme}, keywords: {', '.join(keyword_overlap) if keyword_overlap else 'none'}")

            # Special handling for certain narrative elements
            narrative_elements = ["witness", "wedding", "church", "bride", "ceremony", "chapel"]
            text_lower = candidate["text"].lower()
            query_lower = query.lower()
            narrative_matches = sum(1 for elem in narrative_elements if elem in text_lower and elem in query_lower)

            # Calculate total boost factor
            if theme_overlap or narrative_matches > 0:
                # Base theme boost + keyword boost + narrative boost
                theme_boost = settings.THEME_MATCH_BOOST * len(theme_overlap)
                keyword_boost = settings.THEME_KEYWORD_BOOST * keyword_overlap_count
                narrative_boost = settings.NARRATIVE_ELEMENT_BOOST * narrative_matches

                total_boost = theme_boost + keyword_boost + narrative_boost

                # Apply boost
                candidate["score"] = candidate["score"] * (1 + total_boost)

                if theme_overlap:
                    logger.debug(
                        f"Theme boosted candidate {candidate['id'][:8]} by {total_boost:.2f} "
                        f"(themes: {len(theme_overlap)}, keywords: {keyword_overlap_count}, narrative: {narrative_matches})"
                    )

    # Re-sort candidates by score
    return sorted(candidates, key=lambda c: c["score"], reverse=True)


def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text for boosting."""
    # Simple approach - extract nouns and proper nouns
    # A more sophisticated approach would use POS tagging or NER
    words = re.findall(r'\b[A-Za-z]{3,}\b', text)
    return [word.lower() for word in words]


def apply_keyword_boost(query: str, candidates: List[Dict[str, Any]], is_fiction: bool = False) -> List[Dict[str, Any]]:
    """
    Apply keyword-based score boosting for fiction content.
    Enhances scores of candidates that contain important query keywords.

    This is a legacy method kept for backward compatibility.
    For fiction content, the theme-based approach is now preferred.
    """
    if is_fiction:
        # Use the more sophisticated theme-based approach for fiction
        return apply_theme_based_boost(query, candidates, is_fiction=True)

    # Extract keywords from query (for non-fiction)
    query_keywords = extract_keywords(query)

    if not query_keywords:
        return candidates

    logger.debug(f"Applying keyword boost using keywords: {', '.join(query_keywords)}")

    # Define boost factor based on keyword matches
    for candidate in candidates:
        text = candidate["text"].lower()
        keyword_matches = sum(1 for keyword in query_keywords if keyword in text)

        # Apply boost proportional to matches
        if keyword_matches > 0:
            boost = settings.FICTION_KEYWORD_BOOST * keyword_matches
            candidate["score"] = candidate["score"] * (1 + boost)
            logger.debug(f"Boosted candidate {candidate['id'][:8]} by {boost:.2f} (keywords: {keyword_matches})")

    # Re-sort candidates after boosting
    return sorted(candidates, key=lambda c: c["score"], reverse=True)


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

        # Check if any candidates are fiction content to adjust threshold
        is_fiction = any(
            c.get("metadata", {}).get("is_fiction", False) or
            c.get("metadata", {}).get("genre") == "fiction" or
            c.get("metadata", {}).get("category") == "fiction"
            for c in candidates[:3]  # Check first few
        )

        # Store original scores for before/after comparison if debugging
        if settings.DEBUG and is_fiction:
            original_scores = {c["id"]: c["score"] for c in candidates[:10]}

        # Check for narrative keywords in query for fiction content
        narrative_query = is_fiction and any(term in query.lower() for term in [
            "sequence", "events", "witness", "what happened", "how did", "what led to"
        ])

        # Log narrative query detection
        if narrative_query:
            logger.info(f"Narrative query detected: '{query}'")

        # Apply theme-based boost for fiction content
        if is_fiction:
            if settings.ENABLE_THEME_DETECTION:
                logger.info("Fiction content detected, applying theme-based boosting")
                candidates = apply_theme_based_boost(query, candidates, is_fiction=True)
            else:
                logger.info("Fiction content detected, applying standard keyword boosting")
                candidates = apply_keyword_boost(query, candidates, is_fiction=True)

            # Log boosting effects for the top candidates if debugging
            if settings.DEBUG:
                logger.info("Score changes after boosting:")
                for c in sorted(candidates, key=lambda c: c["score"], reverse=True)[:10]:
                    if c["id"] in original_scores:
                        original = original_scores[c["id"]]
                        boost_pct = ((c["score"] - original) / original) * 100 if original > 0 else 0
                        logger.info(f"  ID {c['id'][:8]}: {original:.2f} → {c['score']:.2f} ({boost_pct:+.1f}%)")

        # Adjust threshold for fiction content - even lower for narrative queries
        if is_fiction:
            if narrative_query:
                # Use an even lower threshold for narrative queries about fiction
                threshold = settings.FICTION_CE_THRESHOLD
                logger.info(f"Using fiction narrative threshold: {threshold}")
            else:
                # Use regular fiction threshold
                threshold = settings.CE_NEUTRAL_THRESHOLD * 0.7
                logger.info(f"Using regular fiction threshold: {threshold}")
        else:
            # Standard threshold for non-fiction
            threshold = settings.CE_NEUTRAL_THRESHOLD

        # Sort by score (descending) for logging and return
        sorted_candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)

        # Log top 10 candidates with scores before truncation (helpful for debugging)
        if settings.DEBUG or is_fiction:  # Always log for fiction content
            for i, c in enumerate(sorted_candidates[:10]):
                snippet = c["text"][:100] + "..." if len(c["text"]) > 100 else c["text"]
                logger.debug(f"Candidate #{i+1}, ID={c['id']}, Score={c['score']:.2f}, Text: {snippet}")

        # Calculate mean score to check if we need to fallback
        mean_score = statistics.mean([c["score"] for c in candidates]) if candidates else 0
        logger.debug(f"Cross-encoder normalized mean score: {mean_score:.2f}")

        # Only fall back if normalized mean score is below adjusted threshold
        if mean_score < threshold:
            logger.info(
                f"Cross-encoder normalized mean score {mean_score:.2f} below "
                f"threshold {threshold:.2f} (is_fiction={is_fiction})"
            )
            return fallback_to_llm("Mean score below threshold", query, candidates, top_n)

        # For fiction content with narrative queries, use a higher top_n
        if is_fiction and narrative_query and top_n < 15:
            top_n = 15  # Ensure we get enough narrative context
            logger.info(f"Increased top_n to {top_n} for narrative fiction query")

        # Return top n candidates (already sorted by apply_theme_based_boost)
        reranked_candidates = sorted_candidates[:top_n]
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