# RAG Embeddings Frontend

A simple React application that interacts with the RAG API.

## Features

- Document ingestion: Upload documents to the knowledge base
- Knowledge queries: Ask questions and get AI-generated answers based on the knowledge base
- API health checking

## Technology Stack

- React with Vite for fast development
- React Query for data fetching
- Zustand for state management
- Inline CSS for styling (no external dependencies)

## Setup

### Prerequisites

- Node.js 16+
- npm or yarn
- Running RAG API backend (on port 8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. The application will be available at http://localhost:5173

## Usage

1. First start the backend server:
```bash
cd .. # Go to the root directory
python run.py
```

2. Then start the frontend in a separate terminal:
```bash
cd frontend
npm run dev
```

3. The application will open in your browser. You can:
   - Switch between "Document Ingest" and "Query Knowledge" tabs
   - Upload documents to the knowledge base
   - Ask questions about the uploaded documents

## Development

The application is structured as follows:

- `src/api/ragApi.js` - API client for interacting with the backend
- `src/stores/ragStore.js` - Zustand store for state management
- `src/components/` - React components
  - `DocumentIngest.jsx` - Document upload interface
  - `QueryInterface.jsx` - Question-answering interface
- `App.jsx` - Main application component
- `main.jsx` - Application entry point

## Building for Production

To build the application for production:

```bash
npm run build
```

The built files will be in the `dist` directory and can be served by any static file server.