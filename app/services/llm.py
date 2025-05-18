import json
from typing import Any
import os

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
        # Extract document information for better citations
        enhanced_docs = []
        for i, doc in enumerate(documents):
            doc_num = i + 1

            # Get filename from metadata
            filename = doc.get("metadata", {}).get("filename", "")
            if not filename:
                source_name = "Document " + str(doc_num)
            else:
                # Get just the base filename without extension
                base_name = os.path.basename(filename)
                source_name = os.path.splitext(base_name)[0].replace("_", " ")

            # Get approximate excerpt location for citation
            start_pos = doc.get("metadata", {}).get("start_char", 0)

            # Save first few words of the chunk for reference
            first_words = doc["text"].split()[:5]
            first_words_text = " ".join(first_words) + "..."

            # Add citation info to the document
            citation_info = f"[{doc_num}] Source: \"{source_name}\" (ID: {doc['id']})"

            enhanced_docs.append({
                "num": doc_num,
                "id": doc["id"],
                "source": source_name,
                "start_pos": start_pos,
                "first_words": first_words_text,
                "text": doc["text"],
                "citation": citation_info
            })

        # Combine document texts with identifiers and citation info
        context = "\n\n".join(
            f"{doc['citation']}\n{doc['text']}"
            for doc in enhanced_docs
        )

        system_content = (
            "You are a helpful assistant. Follow these instructions carefully:\n\n"
            "1. Use ONLY the information in the provided context documents.\n"
            "2. For each statement in your answer, cite your source using the reference number from the context.\n"
            "3. Use citations in this format: [1] for information from the first source, [2] for the second, etc.\n"
            "4. When quoting text directly, add the citation immediately after the quote.\n"
            "5. If you cannot find evidence for a detail, state 'The provided documents don't contain information about this.'\n"
            "6. NEVER make up information or citations.\n"
            "7. Keep citations concise and integrated into your answer.\n"
            "8. If a piece of information appears in multiple sources, you may cite all relevant sources: [1,2].\n"
            "9. Strive for accuracy and precision in your citations to maintain credibility."
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Context:\n{context}"},
            {"role": "user", "content": f"Answer the following query with appropriate citations: {query}"},
        ]

        logger.debug(
            f"Generating answer with {len(documents)} documents using model {settings.ANSWER_MODEL}"
        )
        response = openai.chat.completions.create(
            model=settings.ANSWER_MODEL, messages=messages, temperature=0.2
        )

        answer = response.choices[0].message.content
        logger.debug(f"Generated answer of length {len(answer)}")

        # Verify citations are included
        if len(documents) > 0 and not any(f"[{i+1}]" in answer for i in range(min(2, len(documents)))):
            logger.warning("Answer missing citations - regenerating with stronger instructions")
            messages[0]["content"] += "\n\nWARNING: Your previous response lacked proper citations. " \
                                     "You MUST include numbered citations like [1], [2], etc. for EVERY claim you make.\n" \
                                     "Example: Holmes observed six parallel cuts on Watson's left shoe [1]."
            response = openai.chat.completions.create(
                model=settings.ANSWER_MODEL, messages=messages, temperature=0.1
            )
            answer = response.choices[0].message.content

        return answer

    except Exception as e:
        logger.error(f"Error during answer generation: {str(e)}")
        raise LLMError(f"Failed to generate answer: {str(e)}")
