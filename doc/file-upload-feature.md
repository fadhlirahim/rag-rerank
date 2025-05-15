# Markdown File Upload Feature

## Overview

A new feature has been added to the RAG embeddings demo: the ability to upload markdown (.md) files directly into the system. This feature allows users to ingest existing markdown documentation into the knowledge base for querying later.

## Implementation Details

The file upload feature has been implemented in the following components:

1. **DocumentIngest Component**:
   - Added a file input field (hidden) with a reference
   - Added a button to trigger the file input
   - Added a handler for file uploads that:
     - Validates that only `.md` files are accepted
     - Reads the file content using FileReader
     - Updates the document name and content in the store

2. **Data Flow**:
   - When a file is selected, its name is used as the document name
   - The file content is read as text and placed in the document content textarea
   - The user can still edit the content before ingestion
   - The same ingestion process is used, sending the content to the backend API

## Usage

1. Navigate to the "Document Ingest" tab in the application
2. Click the "Upload Markdown File" button
3. Select a markdown (.md) file from your computer
4. The file name and content will be populated in the form
5. Review and modify the content if needed
6. Click "Ingest Document" to process the document

## Limitations

- Only accepts markdown (.md) files
- File size is limited by browser memory constraints
- The content is read as plain text, not as a binary file

## Future Improvements

- Support for additional file formats (PDF, DOCX, etc.)
- Direct binary file upload to the server
- Progress indicator for large file uploads
- Batch file upload capability