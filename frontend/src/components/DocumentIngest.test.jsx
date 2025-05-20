import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DocumentIngest from './DocumentIngest';
import * as ragApi from '../api/ragApi';

// Mock the API module
vi.mock('../api/ragApi', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ingestDocument: vi.fn(),
    resetVectors: vi.fn(), // Assuming resetVectors is also used and needs mocking
  };
});

// Mock the store
const mockSetDocumentInput = vi.fn();
const mockSetDocumentName = vi.fn();
const mockSetDocumentMetadata = vi.fn();
const mockResetDocumentForm = vi.fn();

const mockInitialStoreState = {
  documentInput: 'Initial document content for testing.',
  documentName: 'InitialTestDoc.md',
  documentMetadata: { category: 'general', genre: 'non-fiction' },
};

vi.mock('../stores/ragStore', () => ({
  __esModule: true,
  default: vi.fn(() => ({
    ...mockInitialStoreState,
    setDocumentInput: mockSetDocumentInput,
    setDocumentName: mockSetDocumentName,
    setDocumentMetadata: mockSetDocumentMetadata,
    resetDocumentForm: mockResetDocumentForm,
  })),
}));


const queryClient = new QueryClient();

describe('DocumentIngest', () => {
  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <DocumentIngest />
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.mocked(ragApi.ingestDocument).mockClear();
    vi.mocked(ragApi.resetVectors).mockClear(); // Clear if used in other tests not shown
    mockSetDocumentInput.mockClear();
    mockSetDocumentName.mockClear();
    mockSetDocumentMetadata.mockClear();
    mockResetDocumentForm.mockClear();

    // Reset store mock to initial state for each test if needed, or specific values
    vi.mocked(useRagStore).mockReturnValue({
        ...mockInitialStoreState,
        setDocumentInput: mockSetDocumentInput,
        setDocumentName: mockSetDocumentName,
        setDocumentMetadata: mockSetDocumentMetadata,
        resetDocumentForm: mockResetDocumentForm,
    });
  });

  it('should render the main heading', () => {
    renderComponent();
    expect(screen.getByRole('heading', { name: /Document Ingest/i })).toBeInTheDocument();
  });

  it('should render document name input', () => {
    renderComponent();
    expect(screen.getByLabelText(/Document Name/i)).toBeInTheDocument();
  });

  it('should render document content textarea', () => {
    renderComponent();
    expect(screen.getByLabelText(/Document Content/i)).toBeInTheDocument();
  });

  it('should render file input button', () => {
    renderComponent();
    expect(screen.getByText(/Upload Markdown File/i)).toBeInTheDocument();
  });

  it('should render category select dropdown', () => {
    renderComponent();
    expect(screen.getByLabelText(/Category/i)).toBeInTheDocument();
  });

  it('should render genre select dropdown', () => {
    renderComponent();
    expect(screen.getByLabelText(/Genre/i)).toBeInTheDocument();
  });

  it('should render ingest document button', () => {
    renderComponent();
    expect(screen.getByRole('button', { name: /Ingest Document/i })).toBeInTheDocument();
  });

  it('should render reset database button', () => {
    renderComponent();
    expect(screen.getByRole('button', { name: /Reset Database/i })).toBeInTheDocument();
  });

  it('should update document name on input', async () => {
    renderComponent();
    const nameInput = screen.getByLabelText(/Document Name/i);
    await userEvent.type(nameInput, 'My Test Document');
    expect(mockSetDocumentName).toHaveBeenCalledWith('My Test Document');
  });

  it('should update document content on paste', async () => {
    renderComponent();
    const contentArea = screen.getByLabelText(/Document Content/i);
    await userEvent.paste(contentArea, 'This is the document content.');
    expect(mockSetDocumentInput).toHaveBeenCalledWith('This is the document content.');
  });

  it('should update category on select change', async () => {
    renderComponent();
    const categorySelect = screen.getByLabelText(/Category/i);
    await userEvent.selectOptions(categorySelect, 'technical');
    expect(mockSetDocumentMetadata).toHaveBeenCalledWith({ category: 'technical', genre: 'non-fiction' });
  });

  it('should update genre on select change', async () => {
    renderComponent();
    const genreSelect = screen.getByLabelText(/Genre/i);
    await userEvent.selectOptions(genreSelect, 'fiction');
    expect(mockSetDocumentMetadata).toHaveBeenCalledWith({ category: 'general', genre: 'fiction' });
  });

  it('should handle successful markdown file upload', async () => {
    renderComponent();
    const fileInputElement = screen.getByTestId('file-upload-input');

    const fileContent = '# Test Markdown Content';
    const fileName = 'test.md';
    const file = new File([fileContent], fileName, { type: 'text/markdown' });

    await userEvent.upload(fileInputElement, file);

    expect(mockSetDocumentName).toHaveBeenCalledWith(fileName);
    // FileReader is asynchronous, so we need to wait for the content to be read
    // However, the mock store setters are called synchronously after FileReader's onload.
    // For real file reading, we might need a waitFor, but here the mocks should capture the calls.
    // Let's verify the call was made, assuming the FileReader mock works as expected or is not deeply mocked.
    // The actual implementation uses a real FileReader.
    // The key is that setDocumentInput is called within the onload callback.
    // Testing this perfectly might require mocking FileReader if direct calls aren't captured.
    // For now, we assume the event loop processes the onload and calls the setter.
    // Vitest and JSDOM's event loop handling should be sufficient.
    expect(mockSetDocumentInput).toHaveBeenCalledWith(fileContent);
  });

  it('should handle non-markdown file upload and show alert', async () => {
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    renderComponent();
    const fileInputElement = screen.getByTestId('file-upload-input');

    const fileContent = 'This is a plain text file.';
    const fileName = 'test.txt';
    const file = new File([fileContent], fileName, { type: 'text/plain' });

    // Ensure store is reset for this specific scenario if needed
    vi.mocked(useRagStore).mockReturnValueOnce({
        documentInput: '', // Start with empty for this test if it makes sense
        documentName: '',
        documentMetadata: { category: 'general', genre: 'non-fiction' },
        setDocumentInput: mockSetDocumentInput,
        setDocumentName: mockSetDocumentName,
        setDocumentMetadata: mockSetDocumentMetadata,
        resetDocumentForm: mockResetDocumentForm,
    });
    
    await userEvent.upload(fileInputElement, file);

    expect(alertSpy).toHaveBeenCalledWith('Only markdown (.md) files are supported');
    expect(mockSetDocumentName).not.toHaveBeenCalled();
    expect(mockSetDocumentInput).not.toHaveBeenCalled();

    alertSpy.mockRestore();
  });

  describe('API Interactions (Ingestion)', () => {
    it('should handle successful document ingestion', async () => {
      const mockIngestData = { chunks_ingested: 5 };
      vi.mocked(ragApi.ingestDocument).mockResolvedValue(mockIngestData);

      renderComponent();

      const ingestButton = screen.getByRole('button', { name: /Ingest Document/i });
      await userEvent.click(ingestButton);

      expect(ragApi.ingestDocument).toHaveBeenCalledWith({
        content: mockInitialStoreState.documentInput,
        filename: mockInitialStoreState.documentName,
        metadata: mockInitialStoreState.documentMetadata,
      });

      expect(mockResetDocumentForm).toHaveBeenCalled();
      expect(await screen.findByText(/Document successfully ingested! Chunks processed: 5/i)).toBeInTheDocument();
    });

    it('should handle failed document ingestion', async () => {
      const errorMessage = 'Ingestion failed';
      vi.mocked(ragApi.ingestDocument).mockRejectedValue({ message: errorMessage });

      renderComponent();

      const ingestButton = screen.getByRole('button', { name: /Ingest Document/i });
      await userEvent.click(ingestButton);

      expect(ragApi.ingestDocument).toHaveBeenCalledWith({
        content: mockInitialStoreState.documentInput,
        filename: mockInitialStoreState.documentName,
        metadata: mockInitialStoreState.documentMetadata,
      });

      expect(await screen.findByText(`Error: ${errorMessage}`)).toBeInTheDocument();
      expect(mockResetDocumentForm).not.toHaveBeenCalled();
    });
  });

  describe('API Interactions (Reset Database)', () => {
    let confirmSpy;

    beforeEach(() => {
      vi.useFakeTimers();
      confirmSpy = vi.spyOn(window, 'confirm');
    });

    afterEach(() => {
      vi.runOnlyPendingTimers();
      vi.useRealTimers();
      confirmSpy.mockRestore();
    });

    it('should handle successful database reset and message timeout', async () => {
      confirmSpy.mockReturnValue(true);
      vi.mocked(ragApi.resetVectors).mockResolvedValue({});

      renderComponent();
      const resetButton = screen.getByRole('button', { name: /Reset Database/i });
      await userEvent.click(resetButton);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete ALL vectors from the database? This action cannot be undone.');
      expect(ragApi.resetVectors).toHaveBeenCalled();

      const successMessage = await screen.findByText('Vector database successfully reset!');
      expect(successMessage).toBeInTheDocument();

      // Advance timers by 3 seconds (as in component logic)
      vi.advanceTimersByTime(3000);
      await waitFor(() => {
        expect(screen.queryByText('Vector database successfully reset!')).not.toBeInTheDocument();
      });
    });

    it('should handle failed database reset', async () => {
      confirmSpy.mockReturnValue(true);
      const resetErrorMessage = 'Reset failed';
      vi.mocked(ragApi.resetVectors).mockRejectedValue({ message: resetErrorMessage });

      renderComponent();
      const resetButton = screen.getByRole('button', { name: /Reset Database/i });
      await userEvent.click(resetButton);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete ALL vectors from the database? This action cannot be undone.');
      expect(ragApi.resetVectors).toHaveBeenCalled();

      expect(await screen.findByText(`Reset Error: ${resetErrorMessage}`)).toBeInTheDocument();
      expect(screen.queryByText('Vector database successfully reset!')).not.toBeInTheDocument();
    });

    it('should handle cancelled database reset', async () => {
      confirmSpy.mockReturnValue(false);
      renderComponent();

      const resetButton = screen.getByRole('button', { name: /Reset Database/i });
      await userEvent.click(resetButton);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete ALL vectors from the database? This action cannot be undone.');
      expect(ragApi.resetVectors).not.toHaveBeenCalled();
      expect(screen.queryByText('Vector database successfully reset!')).not.toBeInTheDocument();
      expect(screen.queryByText(/Reset Error:/i)).not.toBeInTheDocument();
    });
  });
});
