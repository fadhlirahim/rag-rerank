import json
from typing import Any

import openai

from app.core import LLMError, get_logger, settings

# Setup logger
logger = get_logger(__name__)

# Initialize OpenAI - no proxy settings
openai.api_key = settings.OPENAI_API_KEY


def rerank(
    query: str, candidates: list[dict[str, Any]], n: int = settings.DEFAULT_RERANK_TOP_N
) -> list[dict[str, Any]]:
    """Rerank candidates using GPT-4o-mini."""
    try:
        logger.debug(f"Reranking {len(candidates)} candidates with top_n={n}")

        system_content = (
            "Score each document 0-10 for relevance to the query. "
            'Return JSON: [{"id":"...", "score":...}, ...]. '
            f"Query: {query}"
        )

        messages = [{"role": "system", "content": system_content}]

        for candidate in candidates:
            doc_content = f"## DOC {candidate['id']}\n{candidate['text']}"
            messages.append({"role": "user", "content": doc_content})

        logger.debug(
            f"Sending reranking request to OpenAI with model {settings.RERANK_MODEL}"
        )
        response = openai.chat.completions.create(
            model=settings.RERANK_MODEL,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # Extract scores and sort candidates
        id_to_score = {item["id"]: item["score"] for item in result}

        # Sort candidates by score
        sorted_candidates = sorted(
            candidates, key=lambda c: id_to_score.get(c["id"], 0), reverse=True
        )

        # Return top n candidates
        logger.debug(f"Reranked candidates, returning top {n}")
        return sorted_candidates[:n]

    except Exception as e:
        logger.error(f"Error during reranking: {str(e)}")
        # If reranking fails, fallback to the first n candidates
        logger.info("Falling back to first N candidates due to reranking error")
        return candidates[:n]


def generate_answer(query: str, documents: list[dict[str, Any]]) -> str:
    """Generate an answer using GPT-4o."""
    try:
        # Combine document texts
        context = "\n\n".join(
            f"Document {i + 1}:\n{doc['text']}" for i, doc in enumerate(documents)
        )

        system_content = (
            "You are a helpful assistant. Use ONLY the context below. "
            "If the answer isn't in the context, say so."
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Context:\n{context}"},
            {"role": "user", "content": query},
        ]

        logger.debug(
            f"Generating answer with {len(documents)} documents using model {settings.ANSWER_MODEL}"
        )
        response = openai.chat.completions.create(
            model=settings.ANSWER_MODEL, messages=messages, temperature=0.2
        )

        answer = response.choices[0].message.content
        logger.debug(f"Generated answer of length {len(answer)}")
        return answer

    except Exception as e:
        logger.error(f"Error during answer generation: {str(e)}")
        raise LLMError(f"Failed to generate answer: {str(e)}")
