from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
from uuid import uuid4
import os
import json
import logging
import yaml
import time

from mcp.context import MCPContext
from mcp.memory import get_memory_store, MemoryInterface
from utils.document_parser import DocumentParser
from processors.invoice_processor import InvoiceProcessor
from processors.contract_processor import ContractProcessor
from processors.email_processor import EmailProcessor
from processors.default_processor import DefaultProcessor
from mcp.router import ProcessorRouter

router = APIRouter()
logger = logging.getLogger(__name__)

# Load configuration
with open("config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Dependency to get memory store
def get_memory():
    return get_memory_store(
        memory_type="file",
        storage_dir="data/documents",
        ttl=86400  # 24 hours
    )

# Dependency to get document parser
def get_parser():
    return DocumentParser(ocr_enabled=True)

# Dependency to get processor router
def get_router():
    processors = [
        InvoiceProcessor(config),
        ContractProcessor(config),
        EmailProcessor(config),
        DefaultProcessor(config)  # Add the DefaultProcessor as a fallback
    ]
    return ProcessorRouter(processors)

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    memory: MemoryInterface = Depends(get_memory),
    parser: DocumentParser = Depends(get_parser)
):
    """Upload a document for processing."""
    # Generate a unique document ID
    document_id = str(uuid4())
    logger.info(f"Uploading document with ID: {document_id}, filename: {file.filename}")
    
    # Save the file temporarily
    temp_file_path = f"/tmp/{document_id}_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        # Extract text and metadata
        text = parser.parse(temp_file_path)
        metadata = parser.get_metadata(temp_file_path)
        
        # Add additional metadata
        metadata["filename"] = file.filename
        metadata["upload_time"] = str(time.time())
        
        logger.info(f"Extracted text length: {len(text)}, metadata: {metadata}")
        
        # Create a context
        context = MCPContext(
            document_id=document_id,
            raw_text=text,
            metadata=metadata
        )
        
        # Store in memory
        logger.info(f"Storing document {document_id} in memory")
        success = memory.store(document_id, context)
        
        if not success:
            logger.error(f"Failed to store document {document_id} in memory")
            raise HTTPException(status_code=500, detail="Failed to store document in memory")
        
        # Verify document was stored
        if hasattr(memory, 'exists') and not memory.exists(document_id):
            logger.error(f"Document {document_id} not found in memory after storing")
            raise HTTPException(status_code=500, detail="Document not found in memory after storing")
        
        # Clean up
        os.remove(temp_file_path)
        
        # Log available documents
        if hasattr(memory, 'storage') and hasattr(memory.storage, 'keys'):
            logger.info(f"Available documents after upload: {list(memory.storage.keys())}")
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "metadata": metadata,
            "status": "uploaded"
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        # Clean up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: str,
    body: Dict[str, Any] = Body(default=None),
    memory: MemoryInterface = Depends(get_memory),
    processor_router: ProcessorRouter = Depends(get_router)
):
    """Process a previously uploaded document."""
    logger.info(f"Processing document with ID: {document_id}")
    
    # Check if memory store has the document
    if hasattr(memory, 'storage') and hasattr(memory.storage, 'keys'):
        logger.info(f"Available documents in memory: {list(memory.storage.keys())}")
    
    # Retrieve context from memory
    context = memory.retrieve(document_id)
    if not context:
        logger.error(f"Document not found in memory: {document_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Process the document
        processed_context = processor_router.process_document(context)
        
        # Update in memory
        memory.store(document_id, processed_context)
        
        return {
            "document_id": document_id,
            "status": "processed",
            "document_type": processed_context.metadata.get("document_type", "unknown"),
            "extracted_data": processed_context.extracted_data
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    include_text: bool = False,
    memory: MemoryInterface = Depends(get_memory)
):
    """Retrieve document information and processing results."""
    # Retrieve context from memory
    context = memory.retrieve(document_id)
    if not context:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Prepare response
    response = {
        "document_id": document_id,
        "metadata": context.metadata,
        "extracted_data": context.extracted_data,
        "processing_history": context.processing_history
    }
    
    # Include text if requested
    if include_text and context.raw_text:
        if context.compressed:
            context.decompress()
        response["text"] = context.raw_text
    
    return response

@router.get("/memory-status")
async def memory_status(
    memory: MemoryInterface = Depends(get_memory)
):
    """Check the status of the memory store."""
    try:
        result = {
            "status": "operational",
            "type": memory.__class__.__name__
        }
        
        # If it's an in-memory store with our enhanced methods
        if hasattr(memory, 'get_all_documents'):
            document_ids = memory.get_all_documents()
            result["document_count"] = len(document_ids)
            result["document_ids"] = document_ids
            
            # Get detailed info about each document
            documents = []
            for doc_id in document_ids:
                if hasattr(memory, 'get_document_info'):
                    doc_info = memory.get_document_info(doc_id)
                    if doc_info:
                        documents.append(doc_info)
                else:
                    try:
                        context = memory.retrieve(doc_id)
                        if context:
                            doc_info = {
                                "document_id": doc_id,
                                "document_type": context.metadata.get("document_type", "unknown"),
                                "has_extracted_data": bool(context.extracted_data)
                            }
                            documents.append(doc_info)
                    except Exception as e:
                        logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            
            result["documents"] = documents
        # Fallback for older memory implementations
        elif hasattr(memory, 'storage') and hasattr(memory.storage, 'keys'):
            document_ids = list(memory.storage.keys())
            result["document_count"] = len(document_ids)
            result["document_ids"] = document_ids
            
            # Get basic info about each document
            documents = []
            for doc_id in document_ids:
                try:
                    context = memory.retrieve(doc_id)
                    if context:
                        doc_info = {
                            "document_id": doc_id,
                            "document_type": context.metadata.get("document_type", "unknown"),
                            "has_extracted_data": bool(context.extracted_data)
                        }
                        documents.append(doc_info)
                except Exception as e:
                    logger.error(f"Error retrieving document {doc_id}: {str(e)}")
            
            result["documents"] = documents
        
        return result
    except Exception as e:
        logger.error(f"Error checking memory status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/documents")
async def get_all_documents(
    memory: MemoryInterface = Depends(get_memory)
):
    """Get a list of all documents."""
    try:
        # Use the new get_all_documents method if available
        if hasattr(memory, 'get_all_documents'):
            document_ids = memory.get_all_documents()
        # Fallback for older memory implementations
        elif hasattr(memory, 'storage'):
            document_ids = list(memory.storage.keys())
        else:
            return {"documents": []}
        
        documents = []
        for doc_id in document_ids:
            try:
                context = memory.retrieve(doc_id)
                if context:
                    doc_info = {
                        "document_id": doc_id,
                        "document_type": context.metadata.get("document_type", "unknown"),
                        "filename": context.metadata.get("filename", "unknown"),
                        "upload_time": context.metadata.get("upload_time", "unknown"),
                        "processed": bool(context.extracted_data),
                        "extracted_fields": list(context.extracted_data.keys()) if context.extracted_data else []
                    }
                    documents.append(doc_info)
            except Exception as e:
                logger.error(f"Error retrieving document {doc_id}: {str(e)}")
        
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error getting all documents: {str(e)}")
        return {"error": str(e), "documents": []}

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    memory: MemoryInterface = Depends(get_memory)
):
    """Delete a document and its associated data."""
    if not memory.exists(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    memory.delete(document_id)
    
    return {"status": "deleted", "document_id": document_id}

@router.get("/test-document/{document_id}")
async def test_document_exists(
    document_id: str,
    memory: MemoryInterface = Depends(get_memory)
):
    """Test if a document exists in memory."""
    logger.info(f"Testing if document {document_id} exists in memory")
    
    # Check all available documents
    available_docs = []
    if hasattr(memory, 'get_all_documents'):
        available_docs = memory.get_all_documents()
    elif hasattr(memory, 'storage'):
        available_docs = list(memory.storage.keys())
    
    logger.info(f"Available documents: {available_docs}")
    
    # Check if the specific document exists
    exists = False
    if hasattr(memory, 'exists'):
        exists = memory.exists(document_id)
    
    # Try to retrieve the document
    context = None
    try:
        context = memory.retrieve(document_id)
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
    
    return {
        "document_id": document_id,
        "exists": exists,
        "available_documents": available_docs,
        "document_found": context is not None,
        "document_metadata": context.metadata if context else None
    }