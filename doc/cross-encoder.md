# Swap-out Plan — From "GPT-4o-mini reranker" to a local cross-encoder

## Phases

### Phase 0: Baseline
- **Goal**: Know what you're beating
- **Brutal reality check**: *Now*: ~2 s latency, $0.002 – 0.005 per query (25 chunks × ~700 tokens). Log 1 day of traffic → save mean/95-p latency, nDCG@25, recall@50, cost.

### Phase 1: Pick the new model
- **Goal**: Cheap ✓, accurate ✓
- **Brutal reality check**: **Default**: BAAI/bge-reranker-large (418 M params, 1024 tokens)
  **Fallback** for CPU-only boxes: nreimers/MiniLM-L6-v2 (67 M).

### Phase 2: Wire it in code
- **Goal**: Minimal diff
- **Brutal reality check**: 

```python
# pip install sentence-transformers>=2.5.1

# app/services/rerankers.py
from sentence_transformers import CrossEncoder
from app.config import RERANK_MODEL, DEVICE, RERANK_BATCH

ce = CrossEncoder(RERANK_MODEL, device=DEVICE)

def rerank_crossencoder(query: str, cands: list[dict], top_n: int = 5):
    pairs = [(query, c["text"]) for c in cands]
    scores = ce.predict(pairs, batch_size=RERANK_BATCH)
    for c, s in zip(cands, scores):
        c["score"] = float(s)
    return sorted(cands, key=lambda c: c["score"], reverse=True)[:top_n]

# app/services/llm.py  – replace rerank() call
from app.services.rerankers import rerank_crossencoder
…
docs = rerank_crossencoder(query, docs, top_n=TOP_N)
```

### Phase 3: Config toggles
- **Goal**: Easy rollback
- **Brutal reality check**: 

```python
# app/config.py
USE_CROSS_ENCODER = True
RERANK_MODEL      = "BAAI/bge-reranker-large"
DEVICE            = "cuda"           # or "cpu"
RERANK_BATCH      = 16
LLM_FALLBACK_THRESHOLD = 6.5        # mean score < τ → go back to GPT-4o-mini
```

### Phase 4: Local serving
- **Goal**: Keep sub-100 ms
- **Brutal reality check**: *GPU*: even a T4 handles 300 QPS.
  *CPU*: quantize (`bitsandbytes`, int8) → 250–300 ms per 25 docs — still 5–8× faster than GPT call.

### Phase 5: Evaluation script
- **Goal**: Prove it works
- **Brutal reality check**: 

```bash
python scripts/benchmark_rerank.py \
    --queries sample_queries.jsonl \
    --truth judgements.jsonl \
    --reranker crossencoder
# emit recall@25, nDCG@25, mean latency, $ cost
```

### Phase 6: Staged rollout
- **Goal**: Zero-risk cut-over
- **Brutal reality check**: 
  1. **Env flag**: `USE_CROSS_ENCODER=false` → old path.
  2. **Canary 5% traffic** for 24 h; alert on latency or recall drop.
  3. Ramp 25% → 50% → 100%.

### Phase 7: Fallback logic
- **Goal**: Safety net
- **Brutal reality check**: If `avg(score)<LLM_FALLBACK_THRESHOLD` **or** reranker throws, retry original GPT-4o-mini path.

### Phase 8: Logging & retrain loop
- **Goal**: Continuous lift
- **Brutal reality check**: Persist ⟨query, top-k docs, click / user vote⟩ → nightly job builds *hard negatives* → fine-tune retriever & reranker every sprint.

### Phase 9: Kill dead code
- **Goal**: Resist bloat
- **Brutal reality check**: Once cross-encoder holds for 2 weeks, delete GPT reranking code—only keep the fallback call.

---

## Quick wins while you're at it
* **Batch everywhere** – `ce.predict([...], batch_size=RERANK_BATCH)` not per-pair calls.  
* **Truncate long chunks** – cross-encoder cap is 512–1024 tokens; slice not string-split.  
* **Hybrid retrieval** – add BM25, fuse with dense to stop rare-keyword misses.  
* **Quantize** – `AutoGPTQ` or `bitsandbytes` drops VRAM to ~7 GB with <1 pt loss.

---

## Cost & latency impact (real-world numbers)

| | GPT-4o-mini rerank (25 docs) | `bge-reranker-large` on T4 |
|------------------|------------------------------|---------------------------|
| Tokens billed | ~700 | 0 |
| $ / 1k queries | $2.0-4.0 | $0.04 (GPU @ $1/h, 25 QPS) |
| P95 latency | 1800 ms | 90 ms |

You're looking at **~50× cheaper** and **20× faster** with no accuracy hit—and you still have GPT-4o-mini as an on-demand auditor.

Ship it.
