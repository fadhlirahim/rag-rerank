# RAG System Fixes - TODO

## 🔥 CRITICAL FIXES (Do First)

### 1. Fix Score Confusion - BREAKING BUG
- [ ] **Fix LanceDB distance → similarity conversion** in `app/services/embedding.py:query_embeddings()`
  - Current: `"score": res_item["_distance"]` (distance - lower is better)
  - Fix: `"score": 1.0 / (1.0 + res_item["_distance"])` (similarity - higher is better)
  - **Impact**: This breaks the entire ranking pipeline

### 2. Fix MMR Implementation
- [ ] **Verify MMR math works with similarity scores** in `app/services/rag.py:apply_mmr()`
  - Current MMR assumes similarity scores but receives distances
  - Test MMR with corrected similarity scores
  - **Alternative**: Remove MMR entirely for simplicity (recommended)

### 3. Fix Embedding Dimension Handling
- [ ] **Stop truncating embeddings** in `app/services/embedding.py`
  - Option A: Use full OpenAI embedding dimensions (3072 for text-embedding-3-large)
  - Option B: Request specific dimensions from OpenAI API (`dimensions=1024`)
  - Update `EMBEDDING_DIMENSIONS` setting to match reality
  - **Impact**: Truncation destroys 2/3 of semantic information

### 4. Fix Error Handling
- [ ] **Make LanceDB initialization fail fast** in `app/services/embedding.py`
  - Current: Logs error but continues, causes crashes later
  - Fix: Raise exception immediately if DB connection fails
  - Add health check endpoint to verify DB status

## 🎯 HIGH IMPACT SIMPLIFICATIONS

### 5. Simplify Reranking Strategy
- [ ] **Choose ONE reranking approach**
  - Current: Cross-encoder + LLM fallback + theme boosting + fiction logic
  - **Recommended**: Use LLM reranking only (GPT-4o-mini as per your docs)
  - Remove `app/services/rerankers.py` complexity
  - Keep simple `app/services/llm.py:rerank()` function

### 6. Remove Over-Engineering
- [ ] **Remove fiction-specific logic** unless proven beneficial
  - Remove: `FICTION_*` settings, theme detection, narrative query detection
  - Remove: `app/services/theme_tagging.py` (if not proven better than baseline)
  - Simplify: Use same logic for all content types
  - **Test first**: Measure performance impact before removing

### 7. Configuration Cleanup
- [ ] **Reduce configuration parameters** from 20+ to ~5 core settings
  - Keep: `EMBEDDING_MODEL`, `RERANK_MODEL`, `ANSWER_MODEL`
  - Keep: `DEFAULT_RETRIEVAL_TOP_K`, `DEFAULT_RERANK_TOP_N`
  - Remove: All `CE_*`, `THEME_*`, `FICTION_*`, `MMR_*` parameters
  - Document why each remaining parameter exists

## ⚡ ARCHITECTURE DECISIONS

### 8. Implement "Brutal But Works" Baseline
- [ ] **Create simple baseline implementation**
  ```python
  # Simple flow: vector_search(k=25) → llm_rerank(n=5) → answer
  def simple_rag(query: str):
      # 1. Vector search
      query_emb = get_embedding(query)
      matches = query_embeddings(query_emb, top_k=25)

      # 2. LLM rerank
      reranked = llm_rerank(query, matches, top_n=5)

      # 3. Generate answer
      return generate_answer(query, reranked)
  ```

### 9. A/B Test Complex vs Simple
- [ ] **Compare current system vs baseline**
  - Metrics: Answer quality, latency, cost
  - Use your existing evaluation scripts in `scripts/`
  - **Hypothesis**: Simple version will perform better
  - Keep whichever performs better

## 🧪 TESTING & VALIDATION

### 10. Add Integration Tests
- [ ] **Test score conversion fix**
  - Verify higher scores = better results after fix
  - Test with known good/bad document pairs

### 11. Validate Embedding Dimensions
- [ ] **Verify embedding dimensions end-to-end**
  - Check OpenAI API response dimensions
  - Verify LanceDB schema matches
  - Test query embedding dimensions

### 12. Performance Testing
- [ ] **Benchmark before/after changes**
  - Query latency
  - Answer quality (using your Sherlock evaluation)
  - Token usage/cost

## 📚 DOCUMENTATION UPDATES

### 13. Update Architecture Docs
- [ ] **Align `doc/rag.md` with actual implementation**
  - Remove outdated Pinecone references
  - Document current LanceDB flow
  - Update code examples to match reality

### 14. Simplify README
- [ ] **Update setup instructions**
  - Remove unused configuration options
  - Simplify environment variables
  - Add troubleshooting section for common issues

## 🚀 IMPLEMENTATION PRIORITY

**Week 1** (Critical Path):
- Fix score conversion (#1)
- Fix embedding dimensions (#3)
- Make DB initialization fail fast (#4)

**Week 2** (High Impact):
- Implement simple baseline (#8)
- A/B test vs current system (#9)
- Remove over-engineering based on results (#5, #6)

**Week 3** (Polish):
- Configuration cleanup (#7)
- Testing & validation (#10, #11, #12)
- Documentation updates (#13, #14)

## ⚠️ TESTING CHECKLIST

Before making changes:
- [ ] Run `python check_index.py` to verify current DB state
- [ ] Run existing evaluation scripts to establish baseline metrics
- [ ] Create branch for each major change
- [ ] Test with your Sherlock Holmes dataset

After each fix:
- [ ] Verify no regressions in query quality
- [ ] Check latency hasn't increased significantly
- [ ] Ensure error handling works as expected

---

**Philosophy**: Start simple, add complexity only when proven necessary. Your "brutal but works" instinct from the docs was right - the current system is too complex for the problem it's solving.