from typing import Any, Dict, List
import json
import os

from app.core import get_logger
from app.services.embedding import get_embedding, query_embeddings
from app.services.rag import apply_mmr

logger = get_logger(__name__)

def inspect_raw_retrieval(
    query: str,
    top_k: int = 50,
    search_terms: List[str] = None,
    output_path: str = "diagnostic_output.json"
) -> Dict[str, Any]:
    """
    Diagnose RAG retrieval issues by dumping raw matches.

    Args:
        query: The query to retrieve documents for
        top_k: Number of documents to retrieve
        search_terms: List of terms to highlight in the retrieved content
        output_path: Path to save diagnostic output (set to None to skip saving)

    Returns:
        Dictionary with diagnostic information
    """
    logger.info(f"Running diagnostic retrieval for: '{query}'")

    # Get query embedding
    query_embedding = get_embedding(query)

    # Retrieve raw matches without MMR or reranking
    matches = query_embeddings(query_embedding, top_k)

    # Convert to dictionary for easier manipulation
    raw_results = []

    for i, match in enumerate(matches):
        # Extract text and check for search terms
        text = match.metadata.get("text", "")
        filename = match.metadata.get("filename", "unknown")

        # Check if any search terms exist in the content
        term_matches = {}
        if search_terms:
            for term in search_terms:
                if term.lower() in text.lower():
                    term_matches[term] = True

        raw_results.append({
            "position": i + 1,
            "id": match.id,
            "score": float(match.score),
            "text": text,
            "filename": filename,
            "has_search_terms": bool(term_matches),
            "matched_terms": list(term_matches.keys()) if term_matches else [],
            "metadata": {k: v for k, v in match.metadata.items() if k != "text"}
        })

    # Count matches containing search terms
    search_term_stats = {}
    if search_terms:
        for term in search_terms:
            count = sum(1 for r in raw_results if term in r["matched_terms"])
            search_term_stats[term] = {
                "count": count,
                "percent": f"{(count / len(raw_results) * 100):.1f}%"
            }

    # Create diagnostic output
    diagnostic = {
        "query": query,
        "top_k": top_k,
        "search_terms": search_terms,
        "total_matches": len(raw_results),
        "search_term_statistics": search_term_stats,
        "raw_results": raw_results
    }

    # Save to file if path provided
    if output_path:
        try:
            with open(output_path, "w") as f:
                json.dump(diagnostic, f, indent=2)
            logger.info(f"Saved diagnostic output to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save diagnostic output: {str(e)}")

    return diagnostic


def compare_retrieval_methods(
    query: str,
    search_terms: List[str] = None,
    output_path: str = "retrieval_comparison.json"
) -> Dict[str, Any]:
    """
    Compare raw retrieval vs MMR to identify potential issues.

    Args:
        query: The query to analyze
        search_terms: Terms to look for in the results
        output_path: Where to save the comparison output

    Returns:
        Comparison results
    """
    logger.info(f"Running retrieval comparison for: '{query}'")

    # Get query embedding
    query_embedding = get_embedding(query)

    # Get raw retrieval results
    raw_matches = query_embeddings(query_embedding, 50)

    # Convert to candidate format
    candidates = [
        {
            "id": match.id,
            "text": match.metadata["text"],
            "score": match.score,
            "metadata": {k: v for k, v in match.metadata.items() if k != "text"},
            "position": i + 1
        }
        for i, match in enumerate(raw_matches)
    ]

    # Apply MMR
    mmr_candidates = apply_mmr(query_embedding, candidates, top_k=20)

    # Track position changes
    position_changes = {}
    for mmr_pos, mmr_doc in enumerate(mmr_candidates):
        doc_id = mmr_doc["id"]
        # Find original position
        for raw_doc in candidates:
            if raw_doc["id"] == doc_id:
                original_pos = raw_doc["position"]
                position_changes[doc_id] = {
                    "original_pos": original_pos,
                    "mmr_pos": mmr_pos + 1,
                    "change": original_pos - (mmr_pos + 1)
                }
                break

    # Check for search terms in both result sets
    term_stats = {
        "raw": {},
        "mmr": {}
    }

    if search_terms:
        for method, results in [("raw", candidates[:20]), ("mmr", mmr_candidates)]:
            for term in search_terms:
                term_positions = []
                for i, doc in enumerate(results):
                    if term.lower() in doc["text"].lower():
                        term_positions.append(i + 1)

                term_stats[method][term] = {
                    "found": len(term_positions) > 0,
                    "positions": term_positions,
                    "count": len(term_positions)
                }

    # Prepare comparison data
    comparison = {
        "query": query,
        "search_terms": search_terms,
        "term_statistics": term_stats,
        "position_changes": position_changes,
        "raw_top20": [
            {
                "position": i + 1,
                "id": doc["id"],
                "score": doc["score"],
                "text_snippet": doc["text"][:150] + "..."
            }
            for i, doc in enumerate(candidates[:20])
        ],
        "mmr_top20": [
            {
                "position": i + 1,
                "id": doc["id"],
                "score": doc["score"],
                "text_snippet": doc["text"][:150] + "...",
                "position_change": position_changes.get(doc["id"], {}).get("change", 0)
            }
            for i, doc in enumerate(mmr_candidates)
        ]
    }

    # Save to file if path provided
    if output_path:
        try:
            with open(output_path, "w") as f:
                json.dump(comparison, f, indent=2)
            logger.info(f"Saved retrieval comparison to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save retrieval comparison: {str(e)}")

    return comparison