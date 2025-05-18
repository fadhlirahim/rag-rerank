#!/usr/bin/env python3
"""
Evaluation script for the Sherlock Holmes RAG system.
Tests specific queries related to 'A Scandal in Bohemia' and other stories.
"""
import os
import sys
import json
import asyncio
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import get_logger
from app.services.rag import query_knowledge
from app.utils.diagnostic import inspect_raw_retrieval, compare_retrieval_methods

logger = get_logger("sherlock_eval")

# Test queries focusing on the wedding witness scene from "A Scandal in Bohemia"
TEST_QUERIES = [
    {
        "query": "What sequence of events led to Holmes unexpectedly becoming a witness at a wedding in 'A Scandal in Bohemia'?",
        "search_terms": ["wedding", "witness", "St. Monica", "church", "Bohemia"],
        "expected_terms": ["witness", "wedding", "St. Monica"],
        "story": "A Scandal in Bohemia"
    },
    {
        "query": "Describe the scene where Holmes is asked to be a witness at Irene Adler's wedding.",
        "search_terms": ["wedding", "witness", "St. Monica", "register", "Norton"],
        "expected_terms": ["witness", "St. Monica"],
        "story": "A Scandal in Bohemia"
    },
    {
        "query": "How was Holmes recruited to be a witness at St. Monica's church?",
        "search_terms": ["St. Monica", "witness", "church", "register"],
        "expected_terms": ["St. Monica", "witness"],
        "story": "A Scandal in Bohemia"
    },
    {
        "query": "What was Holmes doing at the church in 'A Scandal in Bohemia'?",
        "search_terms": ["church", "witness", "St. Monica"],
        "expected_terms": ["church", "witness"],
        "story": "A Scandal in Bohemia"
    },
    {
        "query": "Why was Holmes at St. Monica's Church during 'A Scandal in Bohemia'?",
        "search_terms": ["St. Monica", "church", "witness", "wedding"],
        "expected_terms": ["St. Monica", "church"],
        "story": "A Scandal in Bohemia"
    }
]


async def evaluate_query(query_data: Dict[str, Any], output_dir: str, diagnostic: bool = True) -> Dict[str, Any]:
    """Evaluate a single query and return the results."""
    query = query_data["query"]
    search_terms = query_data.get("search_terms", [])
    expected_terms = query_data.get("expected_terms", [])
    story = query_data.get("story", "")

    logger.info(f"Evaluating query: {query}")

    results = {}

    # Run raw retrieval diagnostic first
    if diagnostic:
        output_path = os.path.join(output_dir, f"raw_{hash(query)}.json")
        raw_results = inspect_raw_retrieval(
            query=query,
            top_k=50,
            search_terms=search_terms,
            output_path=output_path
        )

        # Check if expected terms were found in raw results
        term_found = {term: False for term in expected_terms}
        raw_positions = {term: [] for term in expected_terms}

        for result in raw_results["raw_results"]:
            for term in expected_terms:
                if term.lower() in result["text"].lower():
                    term_found[term] = True
                    raw_positions[term].append(result["position"])

        # Compare raw vs MMR
        comparison_path = os.path.join(output_dir, f"compare_{hash(query)}.json")
        comparison = compare_retrieval_methods(
            query=query,
            search_terms=expected_terms,
            output_path=comparison_path
        )

        # Store diagnostic results
        results["diagnostic"] = {
            "raw_retrieval": {
                "all_terms_found": all(term_found.values()),
                "term_positions": raw_positions,
                "file_path": output_path
            },
            "comparison": {
                "term_statistics": comparison["term_statistics"],
                "file_path": comparison_path
            }
        }

    # Run the actual RAG query
    top_ks = [25, 50]
    top_ns = [5, 10]

    rag_results = {}
    for top_k in top_ks:
        for top_n in top_ns:
            config_key = f"k{top_k}_n{top_n}"
            logger.info(f"Running RAG query with top_k={top_k}, top_n={top_n}")

            start_time = asyncio.get_event_loop().time()
            response = await query_knowledge(query, top_k=top_k, top_n=top_n)
            end_time = asyncio.get_event_loop().time()

            # Check if expected terms are in the answer
            answer_has_terms = {term: term.lower() in response["answer"].lower() for term in expected_terms}

            rag_results[config_key] = {
                "answer": response["answer"],
                "execution_time": round(end_time - start_time, 2),
                "expected_terms_in_answer": answer_has_terms,
                "all_expected_terms_found": all(answer_has_terms.values()),
                "sources_count": len(response["sources"]) if "sources" in response else 0
            }

    results["rag_results"] = rag_results
    return results


async def run_evaluation(output_dir: str = "eval_results"):
    """Run evaluation on all test queries."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    all_results = {}

    for i, query_data in enumerate(TEST_QUERIES):
        query_id = f"query_{i+1}"
        logger.info(f"Processing {query_id}: {query_data['query']}")

        results = await evaluate_query(query_data, output_dir)
        all_results[query_id] = {
            "query_data": query_data,
            "results": results
        }

    # Calculate overall stats
    stats = {
        "total_queries": len(TEST_QUERIES),
        "configs_tested": []
    }

    # Get all configs from the first result
    if all_results:
        first_query = next(iter(all_results.values()))
        if "rag_results" in first_query["results"]:
            configs = first_query["results"]["rag_results"].keys()

            for config in configs:
                success_count = sum(
                    1 for q in all_results.values()
                    if q["results"]["rag_results"][config]["all_expected_terms_found"]
                )

                stats["configs_tested"].append({
                    "config": config,
                    "success_rate": f"{success_count}/{len(TEST_QUERIES)} ({success_count/len(TEST_QUERIES)*100:.1f}%)"
                })

    # Write overall results
    all_results["stats"] = stats
    results_path = os.path.join(output_dir, "evaluation_results.json")

    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Evaluation complete. Results saved to {results_path}")

    # Print summary
    print("\n=== EVALUATION SUMMARY ===")
    print(f"Total queries tested: {stats['total_queries']}")
    print("\nConfigurations:")
    for config in stats["configs_tested"]:
        print(f"  {config['config']}: {config['success_rate']}")
    print(f"\nDetailed results saved to: {results_path}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())