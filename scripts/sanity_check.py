#!/usr/bin/env python3
"""
Sanity Check Script for RAG System
Skips MMR & reranking to check if the raw retrieval contains key passages.
"""
import os
import sys
import json
import argparse
import asyncio
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import get_logger
from app.services.embedding import get_embedding, query_embeddings

logger = get_logger("sanity_check")

SEARCH_TERMS = [
    "wedding", "church", "St. Monica", "witness", "register",
    "Irene Adler", "Norton", "Godfrey",  # Names
    "carriage", "cab", "hansom",  # Travel
    "Scandal in Bohemia", "Bohemia",  # Story title
]


async def run_sanity_check(query: str, top_k: int = 20, output_file: str = "sanity_check_results.json"):
    """
    Run a basic sanity check to see if the raw retrieval includes key passages.

    Args:
        query: The query to check
        top_k: Number of results to retrieve
        output_file: Path to save the results
    """
    logger.info(f"Running sanity check for query: '{query}'")
    logger.info(f"Retrieving top {top_k} results WITHOUT MMR or reranking")

    # Get query embedding
    query_embedding = get_embedding(query)

    # Retrieve raw matches
    matches = query_embeddings(query_embedding, top_k)

    # Process matches for easier analysis
    results = []
    term_hits = {term: [] for term in SEARCH_TERMS}

    for i, match in enumerate(matches):
        text = match.metadata.get("text", "")
        filename = match.metadata.get("filename", "unknown")

        # Check for search terms
        matched_terms = []
        for term in SEARCH_TERMS:
            if term.lower() in text.lower():
                matched_terms.append(term)
                term_hits[term].append(i + 1)  # Store position

        # Add result to list
        results.append({
            "position": i + 1,
            "id": match.id,
            "score": float(match.score),
            "matched_terms": matched_terms,
            "has_match": len(matched_terms) > 0,
            "filename": filename,
            "text": text
        })

    # Summarize term occurrences
    term_summary = {}
    for term, positions in term_hits.items():
        term_summary[term] = {
            "occurrences": len(positions),
            "positions": positions,
            "found": len(positions) > 0,
        }

    # Prepare summary
    output = {
        "query": query,
        "top_k": top_k,
        "term_summary": term_summary,
        "all_terms_found": all(v["found"] for v in term_summary.values()),
        "results": results
    }

    # Save to file
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Results saved to {output_file}")

    # Print summary
    print("\n=== SANITY CHECK SUMMARY ===")
    print(f"Query: {query}")
    print(f"Retrieved {len(results)} documents")

    print("\nTerm occurrences:")
    for term, info in term_summary.items():
        status = "✅" if info["found"] else "❌"
        print(f"  {status} {term}: {info['occurrences']} occurrences at positions {info['positions']}")

    if output["all_terms_found"]:
        print("\n✅ All search terms were found in the raw retrieval results.")
        print("If your system is failing, the issue is in the MMR or reranking stages.")
    else:
        print("\n❌ Some search terms were not found in the raw retrieval.")
        print("The issue appears to be in the document ingestion or chunking process.")

        # List missing terms
        missing = [term for term, info in term_summary.items() if not info["found"]]
        print(f"Missing terms: {', '.join(missing)}")

    print(f"\nFull results saved to: {output_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="RAG Sanity Check Tool")
    parser.add_argument(
        "--query",
        type=str,
        default="What sequence of events led to Holmes unexpectedly becoming a witness at a wedding in 'A Scandal in Bohemia'?",
        help="Query to check"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of results to retrieve"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="sanity_check_results.json",
        help="Output file path"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_sanity_check(args.query, args.top_k, args.output))
