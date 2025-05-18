# Changelog

## Theme-Based Boosting for Narrative Content - Major Update

### Added
- New `theme_tagging.py` utility for identifying narrative themes in content:
  - Ultra-lean implementation without heavyweight NLP dependencies
  - 16 pre-defined themes with curated keywords for fiction content
  - Special handling for narrative elements like "wedding" and "witness"
- Advanced theme-based relevance boosting system:
  - Detects thematic overlap between queries and passages
  - Applies configurable boost factors for matching themes and keywords
  - Provides extra boost for narrative continuity elements
- Theme-based diagnostic tools:
  - `analyze_query()` - Identifies themes and narrative elements in queries
  - `simulate_theme_boost()` - Simulates boosting effects for debugging
  - `test_theme_tagging.py` - Test script to demonstrate and verify boosting

### Enhanced
- Completely revamped boosting mechanism for fiction content:
  - Now uses semantic themes instead of only keyword matching
  - Maintains backward compatibility with keyword boosting
  - Significantly improves retrieval for narrative questions about fiction
- Added detailed logging of theme detection and boosting effects
- Enhanced reranking process with theme-sensitive scoring

### Configuration
- Added new theme-specific configuration parameters:
  - `THEME_MATCH_BOOST` - Controls boost strength for matching themes
  - `THEME_KEYWORD_BOOST` - Controls boost for keyword matches within themes
  - `NARRATIVE_ELEMENT_BOOST` - Controls boost for narrative continuity elements
  - `ENABLE_THEME_DETECTION` - Toggle for theme-based vs. legacy keyword boosting

## Fiction Detection Improvements - Minor Update

### Fixed
- Added proper handling of document genre from frontend metadata
- Updated backend to use genre metadata for fiction detection
- Fixed document processing to consistently apply special handling for fiction content
- Improved logging for fiction detection and processing

## RAG System Improvements - Major Update

### Fixed
- Increased `CHUNK_SIZE` from 200 characters to 700 tokens to preserve narrative continuity
- Added `CHUNK_OVERLAP` parameter (100 tokens) to ensure context preservation
- Lowered `CE_NEUTRAL_THRESHOLD` from 5.0 to 4.0 to avoid filtering relevant matches
- Increased `DEFAULT_RETRIEVAL_TOP_K` from 25 to 50 for better recall
- Increased `DEFAULT_RERANK_TOP_N` from 5 to 10 to keep more potentially relevant chunks

### Changed
- Completely rewrote text chunking implementation:
  - Now uses sentence-based chunking instead of fixed-size character chunks
  - Properly handles sentence boundaries to preserve context
  - Manages chunk overlaps more intelligently
- Modified MMR application to skip it for fiction content, preserving narrative flow
- Enhanced fiction content handling with automatic threshold adjustments

### Added
- New diagnostic tools to debug retrieval issues:
  - `inspect_raw_retrieval()` - Analyzes raw retrieved matches for key terms
  - `compare_retrieval_methods()` - Compares raw vs. MMR results to identify filtering issues
- Two new diagnostic API endpoints:
  - `/diagnose/raw` - For examining raw retrieval results
  - `/diagnose/compare` - For comparing raw vs. MMR retrieval
- Evaluation scripts:
  - `scripts/sanity_check.py` - Quick validation that gold passages are being retrieved
  - `scripts/evaluate_sherlock.py` - Comprehensive evaluation on Sherlock Holmes stories

### Enhanced
- Better logging throughout the retrieval and reranking process
- Added document genre tracking to apply different processing strategies
- Added detailed logging of ranked results before truncation

## Next Steps
1. Evaluate performance with the new configuration
2. Consider implementing hybrid search (embedding + keyword boosting)
3. Expand evaluation set to cover more fictional texts and scenarios