# Build Plan

Goal: Get a bare-bones, two-stage RAG that uses:
* Retrieval text-embedding-3-large (or small if you’re broke).  ￼
* Rerank GPT-4-o via a cheap JSON-scoring prompt (no OpenAI cross-encoder exists, deal with it).
* Answer GPT-4-o with the reranked top-n chunks in the system prompt.

Tech stack: Python 3.11, FastAPI, and Pinecone.

0. Infrastructure (one-time)

| What                         | Why                                           | Non-BS Tips                                                              |
|------------------------------|-----------------------------------------------|---------------------------------------------------------------------------|
| Create an OpenAI org & keys | You can’t run without them.                  | Separate keys per env; throttle at the gateway.                         |
| Spin up Pinecone (Starter)  | Fast vector look-ups; free until you hit real scale. | Use the “starter” pod; 1K dim limit means set dimensions=1024 on the embedding call. |
| GPU?                         | Only needed if you ditch GPT reranking later. | Leave it for v2.                                                         |


1. Data Ingestion

```python
docs = load_your_docs()                 # any loader you want
chunks = split_text(docs, 512)         # stay <3-4 KB per chunk
embs = openai.embeddings.create(
    model="text-embedding-3-large",
    input=[c.text for c in chunks],
    dimensions=1024                    # shrinks cost & Pinecone dims
)
pinecone.upsert(zip(chunk_ids, embs, meta))
```

Reality check: embedding is the slow part—~0.3s per 1K tokens. Parallel-batch or it drags.

2. Fast Retrieval Endpoint

```python
def retrieve(query: str, k: int = 25):
    q_emb = openai.embeddings.create(
        model="text-embedding-3-large",
        input=query,
        dimensions=1024
    )["data"][0]["embedding"]
    matches = pinecone.query(vector=q_emb, top_k=k, include_metadata=True)
    return matches
```

Latency ≈ 80–120 ms.

3. GPT-4-o Reranker (Brutal but Works)

```python
def rerank(query, candidates, n=5):
    prompt = {
        "role": "system",
        "content": (
          "Score each document 0-10 for relevance to the query. "
          "Return JSON: [{id:…, score:…}, …]. "
          "Query: " + query
        )
    }
    msgs = [prompt] + [
        {"role":"user", "content":f"## DOC {c.id}\n{c.text}"}
        for c in candidates
    ]
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",   # cheaper, enough for scoring
        messages=msgs,
        temperature=0,
        response_format={"type":"json_object"}
    )
    scores = json.loads(resp.choices[0].message.content)
    top = sorted(candidates, key=lambda c: scores[str(c.id)], reverse=True)[:n]
    return top
```

Budget: 25 docs × 5 tokens each ≈ 125 input + 100 output ≈ $0.002/query—fine for a prototype.

4. Final Answer

```python
def answer(query, docs):
    context = "\n\n".join(d.text for d in docs)
    sys = (
        "You are a helpful assistant. Use ONLY the context below. "
        "If the answer isn't there, say so."
    )
    completion = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
           {"role":"system","content":sys},
           {"role":"user","content":f"Context:\n{context}"},
           {"role":"user","content":query}
        ],
        temperature=0.2
    )
    return completion.choices[0].message.content
```

5. Wrap It Up (FastAPI)

* /ingest POST raw docs
* /ask GET query → runs retrieve → rerank → answer

Keep it stateless; store doc metadata & embeddings, not the raw text, in Pinecone.

6. Test Matrix

| Case                    | Expect        | Why                                     |
|-------------------------|---------------|------------------------------------------|
| Query that is in corpus | Perfect answer | Checks recall path.                      |
| Near-duplicate phrasing | Same answer   | Embeddings quality.                      |
| Query outside corpus    | “I don’t know.” | Hallucination guard.                     |
| 50 concurrent queries   | <1 s p95      | Measures GPT concurrency + Pinecone.     |


7. Hard Truths & Next Steps

1.	Latency ceiling: GPT rerank dominates. 25 doc pairs ≈ 300–400 ms even with batching; tolerate it or swap in a local cross-encoder on GPU.

2.	Cost spiral: At volume, GPT rerank gets ugly—either fine-tune a smaller cross-encoder (bge-reranker-base) or wait for OpenAI to drop one.

3.	Long-term: add caching, dynamic k, user-feedback loops, or switch to streaming answers.

4.	Security: you’re pushing raw docs into third-party LLMs—scrub PII or run an on-prem model.

This is not for production use!
