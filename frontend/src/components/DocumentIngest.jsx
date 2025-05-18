import React, { useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ingestDocument, resetVectors } from '../api/ragApi';
import useRagStore from '../stores/ragStore';

function DocumentIngest() {
  const {
    documentInput,
    documentName,
    documentMetadata,
    setDocumentInput,
    setDocumentName,
    setDocumentMetadata,
    resetDocumentForm
  } = useRagStore();

  const [resetSuccess, setResetSuccess] = useState(false);
  const [resetError, setResetError] = useState(null);

  const fileInputRef = useRef(null);

  // Mutation for document ingestion
  const ingestMutation = useMutation({
    mutationFn: () => ingestDocument({
      content: documentInput,
      filename: documentName || 'untitled-document.txt',
      metadata: documentMetadata
    }),
    onSuccess: () => {
      // Reset form on success
      resetDocumentForm();
    }
  });

  // Mutation for resetting vectors
  const resetMutation = useMutation({
    mutationFn: resetVectors,
    onSuccess: () => {
      setResetSuccess(true);
      setResetError(null);
      // Clear success message after 3 seconds
      setTimeout(() => setResetSuccess(false), 3000);
    },
    onError: (error) => {
      setResetError(error.message);
      setResetSuccess(false);
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    ingestMutation.mutate();
  };

  const handleReset = () => {
    // Confirm before resetting
    if (window.confirm('Are you sure you want to delete ALL vectors from the database? This action cannot be undone.')) {
      resetMutation.mutate();
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Only allow markdown files
    if (!file.name.endsWith('.md')) {
      alert('Only markdown (.md) files are supported');
      return;
    }

    // Set document name from file
    setDocumentName(file.name);

    // Read file content
    const reader = new FileReader();
    reader.onload = (e) => {
      setDocumentInput(e.target.result);
    };
    reader.readAsText(file);
  };

  const triggerFileUpload = () => {
    fileInputRef.current.click();
  };

  return (
    <div>
      <h2>Document Ingest</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="documentName" style={{ display: 'block', marginBottom: '5px' }}>
            Document Name:
          </label>
          <input
            id="documentName"
            type="text"
            value={documentName}
            onChange={(e) => setDocumentName(e.target.value)}
            placeholder="Enter document name"
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="documentContent" style={{ display: 'block', marginBottom: '5px' }}>
            Document Content:
          </label>
          <textarea
            id="documentContent"
            value={documentInput}
            onChange={(e) => setDocumentInput(e.target.value)}
            placeholder="Paste your document content here or upload a markdown file"
            rows={10}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ddd',
              resize: 'vertical'
            }}
          />
        </div>

        <div style={{ marginBottom: '15px', display: 'flex', gap: '10px' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
          />
          <button
            type="button"
            onClick={triggerFileUpload}
            style={{
              padding: '10px 15px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Upload Markdown File
          </button>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="category" style={{ display: 'block', marginBottom: '5px' }}>
            Category:
          </label>
          <select
            id="category"
            value={documentMetadata.category}
            onChange={(e) => setDocumentMetadata({ category: e.target.value })}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
          >
            <option value="general">General</option>
            <option value="documentation">Documentation</option>
            <option value="technical">Technical</option>
            <option value="business">Business</option>
          </select>
        </div>

                  <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="submit"
              disabled={!documentInput || ingestMutation.isPending}
              style={{
                padding: '10px 15px',
                backgroundColor: !documentInput || ingestMutation.isPending ? '#cccccc' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: !documentInput || ingestMutation.isPending ? 'not-allowed' : 'pointer'
              }}
            >
              {ingestMutation.isPending ? 'Ingesting...' : 'Ingest Document'}
            </button>

            <button
              type="button"
              onClick={handleReset}
              disabled={resetMutation.isPending}
              style={{
                padding: '10px 15px',
                backgroundColor: resetMutation.isPending ? '#cccccc' : '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: resetMutation.isPending ? 'not-allowed' : 'pointer'
              }}
            >
              {resetMutation.isPending ? 'Resetting...' : 'Reset Database'}
            </button>
          </div>

        {ingestMutation.isError && (
          <div style={{ color: 'red', marginTop: '10px' }}>
            Error: {ingestMutation.error.message}
          </div>
        )}

        {ingestMutation.isSuccess && (
          <div style={{ color: 'green', marginTop: '10px' }}>
            Document successfully ingested! Chunks processed: {ingestMutation.data.chunks_ingested}
          </div>
        )}

        {resetError && (
          <div style={{ color: 'red', marginTop: '10px' }}>
            Reset Error: {resetError}
          </div>
        )}

        {resetSuccess && (
          <div style={{ color: 'green', marginTop: '10px' }}>
            Vector database successfully reset!
          </div>
        )}
      </form>
    </div>
  );
}

export default DocumentIngest;