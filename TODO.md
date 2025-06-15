# RAG System Math Fixes - TODO

## 🔥 CRITICAL MATH FIXES (Breaking the Exploration)

### 1. Fix Score Confusion - BREAKING BUG
- [ ] **Fix LanceDB distance → similarity conversion** in `app/services/embedding.py:query_embeddings()`
  - Current: `"score": res_item["_distance"]` (distance - lower is better)
  - Fix: `"score": 1.0 / (1.0 + res_item["_distance"])` (similarity - higher is better)
  - **OR** use: `"score": 1.0 - min(res_item["_distance"], 1.0)` if distances are normalized
  - **Impact**: This breaks MMR, reranking, and all score-based logic

### 2. Fix MMR Implementation Math
- [ ] **Verify MMR cosine similarity calculations** in `app/services/rag.py:apply_mmr()`
  - MMR expects similarity scores (higher = better) but currently receives distances
  - After fixing #1, verify MMR math is correct
  - Test MMR diversity vs relevance trade-off is working as expected
  - **Keep MMR**: It's a key RAG concept to explore

### 3. Fix Cross-Encoder Score Normalization
- [ ] **Review score normalization logic** in `app/services/rerankers.py:normalize_scores()`
  - Current: `(score + 5.0) * 1.0` - verify this makes sense for your model
  - Cross-encoder scores are typically in [-10, 10] range
  - Ensure normalized scores are comparable with LLM reranker scores
  - Document the expected score ranges for each reranker

### 4. Fix Theme Boosting Math
- [ ] **Verify boost calculations** in `app/services/rerankers.py:apply_theme_based_boost()`
  - Current: `candidate["score"] = candidate["score"] * (1 + boost)`
  - Verify this multiplicative boost makes sense with your score ranges
  - Consider additive boost: `candidate["score"] = candidate["score"] + boost`
  - Test that boosting doesn't break relative ordering

## 🧮 MATHEMATICAL CONSISTENCY

### 5. Standardize Score Semantics
- [ ] **Document score semantics throughout the pipeline**
  - LanceDB: distance (lower = better) → convert to similarity
  - MMR: expects similarity (higher = better)
  - Cross-encoder: raw scores → normalize to [0, 10]
  - LLM reranker: outputs scores in [0, 10]
  - Theme boosting: operates on normalized scores
  - **Goal**: All components work with similarity scores (higher = better)

### 6. Fix Embedding Dimension Handling
- [ ] **Stop truncating embeddings** in `app/services/embedding.py`
  - Current: Truncates embeddings, destroying semantic information
  - Fix A: Use full OpenAI dimensions (3072 for text-embedding-3-large)
  - Fix B: Request specific dimensions from OpenAI: `dimensions=1024`
  - Update LanceDB schema to match chosen dimensions
  - **Impact**: Proper dimensions will improve vector search quality

### 7. Validate Fiction-Specific Thresholds
- [ ] **Review fiction threshold logic** in `app/services/rerankers.py:rerank_crossencoder()`
  - Current thresholds assume normalized scores - verify after score fixes
  - `FICTION_CE_THRESHOLD = 3.0` vs `CE_NEUTRAL_THRESHOLD = 3.5`
  - Test that fiction content gets appropriate threshold adjustments
  - **Keep fiction logic**: It's an interesting RAG concept to explore

### 8. Fix MMR Lambda Parameters
- [ ] **Verify MMR lambda values make sense** in settings
  - `MMR_LAMBDA = 0.5` (balanced relevance/diversity)
  - `FICTION_MMR_LAMBDA = 0.95` (high relevance, low diversity)
  - Test edge cases: lambda=0.0 (pure diversity) and lambda=1.0 (pure relevance)
  - Ensure lambda values produce expected behavior

## 🔍 MATHEMATICAL VALIDATION

### 9. Add Score Validation Tests
- [ ] **Create unit tests for score conversions**
  - Test distance → similarity conversion edge cases
  - Test MMR with known document similarities
  - Test cross-encoder score normalization
  - Test theme boosting doesn't break score ordering

### 10. Add End-to-End Math Tests
- [ ] **Test complete pipeline with known inputs**
  - Use synthetic documents with known similarities
  - Verify higher similarity scores = better ranking
  - Test MMR produces diverse results with low lambda
  - Test fiction detection affects scoring as expected

### 11. Score Distribution Analysis
- [ ] **Analyze score distributions at each stage**
  - Log score histograms before/after each transformation
  - Verify scores stay in expected ranges
  - Check for score compression or expansion issues
  - Add diagnostic tools to visualize score flows

## 🧪 EXPLORATION ENHANCEMENTS

### 12. Add MMR Visualization
- [ ] **Create MMR selection visualization**
  - Show which documents MMR selects vs raw similarity ranking
  - Visualize relevance vs diversity trade-offs
  - Add MMR diagnostics to understand selection process
  - **Goal**: Better understand MMR behavior for learning

### 13. Add Cross-Encoder vs LLM Comparison
- [ ] **Compare reranking approaches side-by-side**
  - Run both cross-encoder and LLM reranker on same inputs
  - Compare score distributions and final rankings
  - Analyze when each approach works better
  - **Goal**: Understand trade-offs between approaches

### 14. Add Fiction Detection Analytics
- [ ] **Analyze fiction vs non-fiction behavior**
  - Track when fiction detection triggers
  - Compare theme boosting effectiveness
  - Analyze narrative query detection accuracy
  - **Goal**: Understand domain-specific RAG adaptations

## 🚀 IMPLEMENTATION PRIORITY

**Week 1** (Fix Core Math):
- Fix score conversion (#1) - this enables everything else
- Fix embedding dimensions (#6) - improves base vector quality
- Validate MMR math (#2) - core RAG concept

**Week 2** (Validate & Test):
- Standardize score semantics (#5)
- Add score validation tests (#9)
- Fix cross-encoder normalization (#3)

**Week 3** (Enhance Exploration):
- Add MMR visualization (#12)
- Compare reranking approaches (#13)
- Analyze fiction detection (#14)

## ⚠️ TESTING CHECKLIST

Before making changes:
- [ ] Run current system with debug logging to capture score distributions
- [ ] Document current behavior for comparison
- [ ] Test with your Sherlock Holmes dataset to establish baseline

After each fix:
- [ ] Verify scores increase monotonically with document relevance
- [ ] Test MMR produces different results than raw similarity ranking
- [ ] Check all exploration features still work correctly

---

**Philosophy**: Fix the math to make your RAG exploration meaningful. Keep all the advanced features - they're valuable for learning about RAG systems. The goal is to have mathematically sound implementations of all the concepts you want to explore.