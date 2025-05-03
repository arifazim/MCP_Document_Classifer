# MCP Document Processor

An intelligent document processing system that uses the Model Context Protocol (MCP) to extract, analyze, and route business documents automatically.

## Overview

The MCP Document Processor is a full-stack application (FastAPI backend + React frontend) that automates document processing workflows. The system classifies documents, extracts relevant information, and provides a user-friendly interface for document management.

## How MCP Works

The Model Context Protocol (MCP) is the core framework that powers this document processor. Here's how it works in simple terms:

1. **Document Context**: When a document is uploaded, MCP creates a "context" object that acts as a container for:
   - The original document text
   - Document metadata (filename, upload time, etc.)
   - Processing history log
   - Extracted information with confidence scores

2. **Memory System**: These context objects are stored in a persistent memory system (file-based storage), allowing them to survive between API calls and server restarts.

3. **Smart Routing**: The system examines each document and routes it to the appropriate specialized processor:
   ```
   Document → Router → Invoice/Contract/Email/Default Processor
   ```

4. **Processing Pipeline**: Each document follows this workflow:
   ```
   Upload → Classification → Information Extraction → Storage → Viewing
   ```

5. **History & Confidence Tracking**: Every processing step is recorded with timestamps and confidence scores, providing full transparency into how information was extracted.

### Key Features

- **Document Classification**: Automatically identifies document types (invoices, contracts, emails)
- **Information Extraction**: Extracts key data using ML models with confidence scoring
- **Persistent Storage**: File-based document storage that persists between server restarts
- **Processing Pipeline**: Specialized processors for different document types
- **Modern UI**: React-based dashboard for document upload, viewing, and management

## Architecture

### Backend

- **Context System**: `MCPContext` objects maintain document state throughout processing
- **Memory System**: Configurable storage (in-memory or file-based) with TTL management
- **Processor Router**: Routes documents to specialized processors based on content
- **Document Processors**: Type-specific processors with a default fallback processor
- **ML Models**: Mock implementations of entity extraction, classification, and summarization

### Frontend

- **Dashboard**: Document statistics and listing with filtering options
- **Document View**: Detailed view of processed documents and extracted data
- **Upload Interface**: Simple drag-and-drop document upload

## Setup

### Backend

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python app.py  # Runs on http://localhost:8000
```

### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start  # Runs on http://localhost:3000
```

## API Endpoints

- `POST /api/documents/upload`: Upload a new document
- `POST /api/documents/{document_id}/process`: Process a document
- `GET /api/documents/{document_id}`: Get document details
- `GET /api/documents`: List all documents
- `DELETE /api/documents/{document_id}`: Delete a document
- `GET /api/memory-status`: Check memory store status (debugging)

## Technical Notes

- Documents are stored in `data/documents/` with a 24-hour TTL
- The DefaultProcessor handles any document type that specialized processors cannot handle
- CORS is enabled to allow frontend-backend communication
- Proxy is configured in package.json to route API requests during development
