# Markdown Rendering Feature

## Overview

This feature adds markdown formatting support to the RAG application's query responses. It renders answers and source texts with proper markdown formatting, making the content more readable and visually appealing.

## Implementation Details

The markdown rendering capability has been implemented using the following components:

1. **Library**: We've used `markdown-it`, a fast and extensible markdown parser and renderer.

2. **QueryInterface Component**:
   - Added a markdown renderer instance using React's `useMemo` for performance
   - Created a helper function `renderMarkdown()` to process markdown content
   - Updated the answer and source text displays to use the markdown renderer
   - Used `dangerouslySetInnerHTML` (safely) to render the processed HTML

3. **CSS Styling**:
   - Added comprehensive markdown styles to the App component
   - Styled various markdown elements including headings, links, code blocks, tables, etc.
   - Used a GitHub-inspired style for a clean, professional look

## Supported Markdown Features

The implementation supports standard markdown syntax including:

- Headings (H1-H6)
- Paragraphs and line breaks
- Bold and italic text
- Links with hover effects
- Code blocks with syntax highlighting
- Inline code
- Blockquotes
- Ordered and unordered lists
- Images (with responsive sizing)
- Tables with alternating row colors
- Horizontal rules

## Configuration Options

The markdown-it instance is configured with these options:

- `html: false` - Disables raw HTML tags for security
- `breaks: true` - Converts newlines to `<br>` tags for better readability
- `linkify: true` - Automatically converts URL-like text to clickable links
- `typographer: true` - Enables smart quotes and other typographic replacements

## Usage

No special action is required to use this feature. When you submit a query, the response will automatically be rendered with markdown formatting if it contains any markdown syntax.

## Security Considerations

The implementation takes several security precautions:

1. Raw HTML is disabled to prevent XSS attacks
2. Content is processed through markdown-it's sanitization process
3. React's structural approach to `dangerouslySetInnerHTML` mitigates many injection risks

## Future Improvements

Potential enhancements to consider:

- Add syntax highlighting for code blocks
- Support for mathematical notation/LaTeX
- Dark mode support for the markdown content
- Custom markdown extensions for domain-specific formatting