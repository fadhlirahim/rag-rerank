import openai
import json
from typing import List, Dict, Any
from app.config import OPENAI_API_KEY, RERANK_MODEL, ANSWER_MODEL
from app.services.text_processing import TextChunk

# Initialize OpenAI - no proxy settings
openai.api_key = OPENAI_API_KEY

def rerank(query: str, candidates: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    """Rerank candidates using GPT-4o-mini."""
    system_content = (
        "Score each document 0-10 for relevance to the query. "
        "Return JSON: [{\"id\":\"...\", \"score\":...}, ...]. "
        f"Query: {query}"
    )

    messages = [{"role": "system", "content": system_content}]

    for candidate in candidates:
        doc_content = f"## DOC {candidate['id']}\n{candidate['text']}"
        messages.append({"role": "user", "content": doc_content})

    try:
        response = openai.chat.completions.create(
            model=RERANK_MODEL,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Extract scores and sort candidates
        id_to_score = {item["id"]: item["score"] for item in result}

        # Sort candidates by score
        sorted_candidates = sorted(
            candidates,
            key=lambda c: id_to_score.get(c["id"], 0),
            reverse=True
        )

        # Return top n candidates
        return sorted_candidates[:n]

    except Exception as e:
        print(f"Error during reranking: {e}")
        # If reranking fails, fallback to the first n candidates
        return candidates[:n]

def generate_answer(query: str, documents: List[Dict[str, Any]]) -> str:
    """Generate an answer using GPT-4o."""
    # Combine document texts
    context = "\n\n".join(f"Document {i+1}:\n{doc['text']}" for i, doc in enumerate(documents))

    system_content = (
        "You are a helpful assistant. Use ONLY the context below. "
        "If the answer isn't in the context, say so."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": f"Context:\n{context}"},
        {"role": "user", "content": query}
    ]

    try:
        response = openai.chat.completions.create(
            model=ANSWER_MODEL,
            messages=messages,
            temperature=0.2
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error during answer generation: {e}")
        return "I'm sorry, I couldn't generate an answer at this time."