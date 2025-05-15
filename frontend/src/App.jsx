import React, { useState } from 'react';
import DocumentIngest from './components/DocumentIngest';
import QueryInterface from './components/QueryInterface';
import { healthCheck } from './api/ragApi';
import { useQuery } from '@tanstack/react-query';

// CSS for Markdown content
const markdownStyles = `
  .markdown-content {
    line-height: 1.6;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  }

  .markdown-content h1,
  .markdown-content h2,
  .markdown-content h3,
  .markdown-content h4,
  .markdown-content h5,
  .markdown-content h6 {
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    font-weight: 600;
    line-height: 1.25;
  }

  .markdown-content h1 { font-size: 2em; }
  .markdown-content h2 { font-size: 1.5em; }
  .markdown-content h3 { font-size: 1.25em; }

  .markdown-content p {
    margin-top: 0;
    margin-bottom: 1rem;
  }

  .markdown-content a {
    color: #0366d6;
    text-decoration: none;
  }

  .markdown-content a:hover {
    text-decoration: underline;
  }

  .markdown-content pre {
    background-color: #f6f8fa;
    border-radius: 3px;
    padding: 16px;
    overflow: auto;
  }

  .markdown-content code {
    font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace;
    background-color: rgba(27, 31, 35, 0.05);
    border-radius: 3px;
    padding: 0.2em 0.4em;
    font-size: 85%;
  }

  .markdown-content pre code {
    background-color: transparent;
    padding: 0;
  }

  .markdown-content blockquote {
    margin-left: 0;
    padding-left: 1em;
    color: #6a737d;
    border-left: 0.25em solid #dfe2e5;
  }

  .markdown-content ul,
  .markdown-content ol {
    padding-left: 2em;
    margin-top: 0;
    margin-bottom: 1rem;
  }

  .markdown-content img {
    max-width: 100%;
    box-sizing: border-box;
  }

  .markdown-content table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1rem;
  }

  .markdown-content table th,
  .markdown-content table td {
    padding: 6px 13px;
    border: 1px solid #dfe2e5;
  }

  .markdown-content table tr {
    background-color: #fff;
    border-top: 1px solid #c6cbd1;
  }

  .markdown-content table tr:nth-child(2n) {
    background-color: #f6f8fa;
  }
`;

function App() {
  const [activeTab, setActiveTab] = useState('ingest');

  // Check if the API is healthy
  const { data: healthStatus, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
  });

  return (
    <div style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Add the markdown styling */}
      <style>{markdownStyles}</style>

      <header>
        <h1>RAG Embeddings Demo</h1>
        {isLoading ? (
          <div>Checking API status...</div>
        ) : isError ? (
          <div style={{ color: 'red' }}>
            API is not available. Make sure the backend is running.
          </div>
        ) : (
          <div style={{ color: 'green' }}>
            API Status: {healthStatus?.status}
          </div>
        )}
      </header>

      <div style={{ marginTop: '20px' }}>
        <div style={{
          display: 'flex',
          gap: '10px',
          borderBottom: '1px solid #ddd',
          marginBottom: '20px'
        }}>
          <button
            onClick={() => setActiveTab('ingest')}
            style={{
              padding: '10px 15px',
              backgroundColor: activeTab === 'ingest' ? '#007bff' : '#f0f0f0',
              color: activeTab === 'ingest' ? 'white' : 'black',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Document Ingest
          </button>
          <button
            onClick={() => setActiveTab('query')}
            style={{
              padding: '10px 15px',
              backgroundColor: activeTab === 'query' ? '#007bff' : '#f0f0f0',
              color: activeTab === 'query' ? 'white' : 'black',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Query Knowledge
          </button>
        </div>

        {activeTab === 'ingest' ? (
          <DocumentIngest />
        ) : (
          <QueryInterface />
        )}
      </div>
    </div>
  );
}

export default App;