import { create } from 'zustand';

// Create a Zustand store to manage the application state
const useRagStore = create((set) => ({
  // Document ingest state
  documentInput: '',
  documentName: '',
  documentMetadata: { source: 'user_upload', category: 'general', genre: 'non-fiction' },

  // Query state
  queryInput: '',
  topK: 25,
  topN: 5,

  // Set document input
  setDocumentInput: (input) => set({ documentInput: input }),

  // Set document name
  setDocumentName: (name) => set({ documentName: name }),

  // Set document metadata
  setDocumentMetadata: (metadata) => set((state) => ({
    documentMetadata: { ...state.documentMetadata, ...metadata }
  })),

  // Set query input
  setQueryInput: (input) => set({ queryInput: input }),

  // Set top K
  setTopK: (k) => set({ topK: k }),

  // Set top N
  setTopN: (n) => set({ topN: n }),

  // Reset document form
  resetDocumentForm: () => set({
    documentInput: '',
    documentName: '',
    documentMetadata: { source: 'user_upload', category: 'general', genre: 'non-fiction' }
  }),

  // Reset query form
  resetQueryForm: () => set({
    queryInput: '',
  }),
}));

export default useRagStore;