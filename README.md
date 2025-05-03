# MCP Document Processor

An intelligent document processing system that uses the Model Context Protocol (MCP) to extract, analyze, and route business documents automatically.


## Project Overview
This project demonstrates how to use MCP to solve a real business challenge: automating document processing workflows. The system can:

- Classify incoming documents (invoices, contracts, emails)
- Extract relevant information using ML models
- Process documents according to their type
Maintain context throughout the processing pipeline
Expose functionality through a REST API

## Key MCP Components

- **Context Objects**: Central to MCP, these objects (implemented in `MCPContext`) carry information between processing steps and maintain the document's state.
- **Memory System**: Stores context objects between processing steps, with pluggable backends.
- **Protocols**: Defines clear interfaces for processors and models, ensuring modularity.
- **Router**: Intelligently routes documents to specialized processors based on content.

## Business Value
This solution addresses several business challenges:

- Reduced Manual Processing: Automates extraction of data from documents
- Consistency: Ensures consistent processing across document types
- Auditability: Maintains processing history and confidence scores
- Scalability: Modular design allows adding new document types easily

## Technical Highlights

- Uses BERT-based models for classification and entity extraction
- T5 model for document summarization
- FastAPI for REST interface
- Pluggable architecture for easy extension
- Comprehensive logging and error handling
- React based UI for better user experience

## Overview

The MCP Document Processor is designed to solve the common business challenge of processing various types of documents (invoices, contracts, emails, etc.) in a consistent and automated way. It utilizes the Model Context Protocol framework to manage information flow between different components of the system.

## Key Features

- **Document Classification**: Automatically identifies document types
- **Information Extraction**: Extracts key information from documents
- **Document Routing**: Routes documents to the appropriate processors
- **Context Management**: Maintains context throughout the processing pipeline
- **API Interface**: Provides a RESTful API for integration with other systems

## Architecture

The system is built around the Model Context Protocol (MCP), which provides:

1. **Context Objects**: Carry information across processing steps
   ```python
   # Example of MCPContext usage
   context = MCPContext(
       document_id=document_id,
       raw_text=text,
       metadata=metadata
   )
   
   # Adding extracted data with confidence scores
   context.add_extracted_data("invoice_number", "INV-12345", confidence=0.95)
   
   # Tracking processing history
   context.add_to_history(
       processor_name="InvoiceProcessor",
       status="completed",
       details={"processing_time": "0.5s"}
   )
   ```

2. **Memory System**: Stores context objects between API calls
   ```python
   # Storing context in memory
   memory.store(document_id, context)
   
   # Retrieving context from memory
   context = memory.retrieve(document_id)
   ```

3. **Protocols**: Define interfaces for processors and models
   ```python
   # Processor protocol example
   class Processor(Protocol):
       @abstractmethod
       def process(self, context: MCPContext) -> MCPContext:
           """Process the document and update the context."""
           pass
       
       @abstractmethod
       def can_handle(self, context: MCPContext) -> bool:
           """Determine if this processor can handle the given document."""
           pass
   ```

4. **Router**: Routes documents to appropriate specialized processors
   ```python
   # Router usage example
   processor = processor_router.route(context)
   if processor:
       processed_context = processor.process(context)
   ```

### MCP Flow Diagram

```
Document Upload → MCPContext Creation → Memory Storage → 
Document Processing → Router Selection → Specialized Processor → 
Entity Extraction → Context Update → Memory Storage → API Response
```

## MCP Implementation Details

The Model Context Protocol implementation in this project offers several key advantages:

### 1. Stateful Processing with Context Persistence

The `MCPContext` class maintains state throughout the document processing lifecycle:

```python
# Context is created during document upload
@router.post("/documents/upload")
async def upload_document(file: UploadFile, memory: MemoryInterface):
    # Create a context
    context = MCPContext(
        document_id=document_id,
        raw_text=text,
        metadata=metadata
    )
    
    # Store in memory for later retrieval
    memory.store(document_id, context)
```

### 2. Pluggable Memory System

The memory system is designed to be pluggable, allowing different storage backends:

```python
# Factory function in memory.py
def get_memory_store(memory_type: str = "in_memory", **kwargs) -> MemoryInterface:
    if memory_type == "in_memory":
        return InMemoryStorage(default_ttl=kwargs.get("ttl", 3600))
    # Additional implementations can be added here
```

### 3. Confidence Tracking

MCP tracks confidence scores for all extracted data, enabling better decision-making:

```python
# In entity_extractor.py
entity_data = {
    "text": text[current_entity["start"]:current_entity["end"]],
    "start": current_entity["start"],
    "end": current_entity["end"],
    "confidence": avg_confidence
}
```

### 4. Processing History

Each processing step is recorded in the context's history, providing auditability:

```python
# In router.py
context.add_to_history(
    processor_name=processor.__class__.__name__,
    status="completed"
)
```

### 5. Intelligent Document Routing

The `ProcessorRouter` determines the appropriate processor for each document:

```python
# In router.py
def route(self, context: MCPContext) -> Optional[Processor]:
    for processor in self.processors:
        if processor.can_handle(context):
            return processor
    return None
```

### 6. Extensibility

Adding new document types is straightforward by implementing the `Processor` protocol:

```python
# Example of adding a new processor
class NewDocumentProcessor(BaseProcessor):
    def can_handle(self, context: MCPContext) -> bool:
        # Logic to determine if this processor can handle the document
        pass
        
    def process(self, context: MCPContext) -> MCPContext:
        # Document processing logic
        pass
```

## Document Processors

The system includes specialized processors for different document types:

- **Invoice Processor**: Extracts vendor, customer, line items, totals, etc.
- **Contract Processor**: Extracts parties, key dates, terms, etc.
- **Email Processor**: Extracts sender, recipients, subject, body, etc.

## Machine Learning Models

Several ML models are used for different tasks:

- **Document Classifier**: BERT-based model for document type classification
- **Entity Extractor**: Named Entity Recognition model for extracting key information
- **Summarizer**: T5-based model for generating document summaries

## User Interface

The MCP Document Processor includes a modern React-based user interface that provides an intuitive way to interact with the document processing system. The UI is built with Material-UI and offers the following features:

### UI Features

- **Dashboard**: Overview of processed documents with statistics and quick access to document details
- **Document Upload**: Drag-and-drop interface for uploading new documents
- **Document Processing**: Step-by-step workflow for processing documents
- **Document Viewer**: Detailed view of processed documents with extracted information
- **Processing History**: Timeline view of all processing steps for auditability

### UI Architecture

The frontend is built with:

- **React**: For building the user interface components
- **Material-UI**: For consistent, responsive design
- **React Router**: For navigation between different views
- **Axios**: For API communication with the backend
- **Chart.js**: For data visualization of document statistics

### UI-Backend Integration

The frontend communicates with the backend through a RESTful API, with the following main endpoints:

- `GET /api/documents`: Retrieve all documents
- `POST /api/documents/upload`: Upload a new document
- `POST /api/documents/{document_id}/process`: Process a document
- `GET /api/documents/{document_id}`: Get document details
- `DELETE /api/documents/{document_id}`: Delete a document

## Complete System Architecture

The MCP Document Processor follows a layered architecture that integrates the frontend, API layer, processing components, and machine learning models:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             Frontend Layer                              │
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐  │
│  │  Dashboard  │      │   Upload    │      │    Document Viewer      │  │
│  └─────────────┘      └─────────────┘      └─────────────────────────┘  │
│          │                   │                         │                │
└──────────┼───────────────────┼─────────────────────────┼────────────────┘
           │                   │                         │
           │                   │                         │
           ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API Layer                                  │
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐  │
│  │ Document    │      │ Document    │      │    Document             │  │
│  │ Upload API  │      │ Process API │      │    Retrieval API        │  │
│  └─────────────┘      └─────────────┘      └─────────────────────────┘  │
│          │                   │                         │                │
└──────────┼───────────────────┼─────────────────────────┼────────────────┘
           │                   │                         │
           │                   │                         │
           ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MCP Core Components                             │
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐  │
│  │ MCPContext  │◄────►│ Memory      │◄────►│    Processor Router     │  │
│  └─────────────┘      └─────────────┘      └─────────────────────────┘  │
│          │                                            │                 │
└──────────┼────────────────────────────────────────────┼─────────────────┘
           │                                            │
           │                                            │
           ▼                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Document Processors                             │
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐  │
│  │ Invoice     │      │ Contract    │      │    Email                │  │
│  │ Processor   │      │ Processor   │      │    Processor            │  │
│  └─────────────┘      └─────────────┘      └─────────────────────────┘  │
│          │                   │                         │                │
└──────────┼───────────────────┼─────────────────────────┼────────────────┘
           │                   │                         │
           │                   │                         │
           ▼                   ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ML Models Layer                                 │
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────────┐  │
│  │ Document    │      │ Entity      │      │    Summarizer           │  │
│  │ Classifier  │      │ Extractor   │      │                         │  │
│  └─────────────┘      └─────────────┘      └─────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Complete Workflow

The document processing workflow involves multiple steps across the system components:

1. **Document Upload**:
   - User uploads a document through the UI
   - Frontend sends the document to the backend API
   - Backend creates an MCPContext object with document metadata
   - Context is stored in the Memory system

2. **Document Classification**:
   - User initiates processing through the UI
   - Backend retrieves the document context from Memory
   - Document Classifier model determines document type
   - Context is updated with document type information

3. **Document Processing**:
   - Processor Router selects the appropriate processor based on document type
   - Selected processor (Invoice, Contract, or Email) processes the document
   - Processor uses Entity Extractor to identify key information
   - Extracted data is added to the context with confidence scores

4. **Result Retrieval**:
   - Updated context is stored back in Memory
   - UI retrieves and displays the processed document information
   - User can view extracted data, confidence scores, and processing history

5. **Audit and Review**:
   - All processing steps are recorded in the context's processing history
   - UI provides visualization of confidence scores for extracted data
   - User can review the document text alongside extracted information

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ and npm (for the frontend)
- Dependencies listed in requirements.txt

### Installation and Setup

#### Backend Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/mcp_document_processor.git
   cd mcp_document_processor
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create a data directory for document storage (if it doesn't exist)
   ```bash
   mkdir -p data
   ```

#### Frontend Setup

1. Navigate to the frontend directory
   ```bash
   cd frontend
   ```

2. Install frontend dependencies
   ```bash
   npm install
   ```

### Running the Application

#### Start the Backend Server

1. From the root directory of the project (with virtual environment activated):
   ```bash
   python app.py
   ```
   This will start the FastAPI server on http://localhost:8000.

2. You can access the API documentation at http://localhost:8000/docs

#### Start the Frontend Development Server

1. Open a new terminal window/tab
2. Navigate to the frontend directory:
   ```bash
   cd /path/to/mcp_document_processor/frontend
   ```

3. Start the React development server:
   ```bash
   npm start
   ```
   This will start the frontend on http://localhost:3000.

### Using the Application

1. Open your browser and navigate to http://localhost:3000
2. Use the sidebar navigation to:
   - View the dashboard
   - Upload new documents
   - Process and view document details

#### Example Workflow

1. **Upload a Document**:
   - Click on "Upload Document" in the sidebar
   - Drag and drop a document (PDF, image, or text file)
   - Click "Upload Document" button

2. **Process the Document**:
   - After successful upload, click "Process Document"
   - Wait for processing to complete

3. **View Results**:
   - View extracted data, confidence scores, and processing history
   - Navigate to the Dashboard to see all processed documents

### API Usage

You can also interact directly with the API:

- `GET /api/documents`: Retrieve all documents
- `POST /api/documents/upload`: Upload a new document
- `POST /api/documents/{document_id}/process`: Process a document
- `GET /api/documents/{document_id}`: Get document details
- `DELETE /api/documents/{document_id}`: Delete a document

## Extending the System

### Adding a New Document Processor

1. Create a new processor class that inherits from `BaseProcessor`
2. Implement the `can_handle` and `process` methods
3. Add the processor to the router in `api/routes.py`

### Adding a New Model

1. Create a new model class that implements the appropriate protocol
2. Add configuration in `config/config.yaml`
3. Integrate the model with the relevant processor

## License

[MIT License](LICENSE)
