import React, { useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { queryKnowledge } from '../api/ragApi';
import useRagStore from '../stores/ragStore';
import MarkdownIt from 'markdown-it';

function QueryInterface() {
  const {
    queryInput,
    topK,
    topN,
    setQueryInput,
    setTopK,
    setTopN
  } = useRagStore();

  // Initialize markdown-it instance
  const md = useMemo(() => new MarkdownIt({
    html: false,        // Disable HTML tags in source
    breaks: true,       // Convert '\n' in paragraphs into <br>
    linkify: true,      // Autoconvert URL-like text to links
    typographer: true   // Enable smartquotes and other typographic replacements
  }), []);

  // Mutation for querying knowledge
  const queryMutation = useMutation({
    mutationFn: () => queryKnowledge({
      query: queryInput,
      top_k: topK,
      top_n: topN
    })
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    queryMutation.mutate();
  };

  const handleKeyDown = (e) => {
    // Check if Enter key is pressed without Shift key
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default behavior (new line)
      handleSubmit(e); // Trigger form submission
    }
  };

  // Render markdown content safely
  const renderMarkdown = (content) => {
    const renderedHtml = md.render(content || '');
    return <div dangerouslySetInnerHTML={{ __html: renderedHtml }} />;
  };

  return (
    <div>
      <h2>Ask a Question</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="queryInput" style={{ display: 'block', marginBottom: '5px' }}>
            Question:
          </label>
          <textarea
            id="queryInput"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question... (Press Enter to submit, Shift+Enter for new line)"
            rows={3}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ddd',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
          <div style={{ flex: 1 }}>
            <label htmlFor="topK" style={{ display: 'block', marginBottom: '5px' }}>
              Top K (Retrieval):
            </label>
            <input
              id="topK"
              type="number"
              min={1}
              max={50}
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor="topN" style={{ display: 'block', marginBottom: '5px' }}>
              Top N (Reranking):
            </label>
            <input
              id="topN"
              type="number"
              min={1}
              max={topK}
              value={topN}
              onChange={(e) => setTopN(parseInt(e.target.value))}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ddd'
              }}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={!queryInput || queryMutation.isPending}
          style={{
            padding: '10px 15px',
            backgroundColor: !queryInput || queryMutation.isPending ? '#cccccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: !queryInput || queryMutation.isPending ? 'not-allowed' : 'pointer'
          }}
        >
          {queryMutation.isPending ? 'Processing...' : 'Ask Question'}
        </button>

        {queryMutation.isError && (
          <div style={{ color: 'red', marginTop: '20px' }}>
            Error: {queryMutation.error.message}
          </div>
        )}
      </form>

      {queryMutation.isSuccess && (
        <div style={{ marginTop: '30px' }}>
          <h3>Answer</h3>
          <div
            style={{
              padding: '15px',
              backgroundColor: '#f8f9fa',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
            className="markdown-content"
          >
            {renderMarkdown(queryMutation.data.answer)}
          </div>

          <h3 style={{ marginTop: '20px' }}>Sources</h3>
          <div>
            {queryMutation.data.sources.map((source, index) => (
              <div
                key={index}
                style={{
                  padding: '10px',
                  marginBottom: '10px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '4px',
                  border: '1px solid #ddd'
                }}
              >
                <div style={{ fontWeight: 'bold' }}>
                  {source.metadata?.filename || 'Unknown source'}
                </div>
                <div style={{ fontSize: '0.9em', marginTop: '5px' }} className="markdown-content">
                  {renderMarkdown(source.text || source.content)}
                </div>
                <div style={{ fontSize: '0.8em', marginTop: '5px', color: '#666' }}>
                  Score: {source.score?.toFixed(4)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QueryInterface;