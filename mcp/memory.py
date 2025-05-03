from typing import Dict, Optional, List
import time
import json
import logging
import os
import pickle
from pathlib import Path
from .context import MCPContext

logger = logging.getLogger(__name__)

class MemoryInterface:
    """Interface for MCP memory systems."""
    
    def store(self, context_id: str, context: MCPContext, ttl: Optional[int] = None) -> bool:
        """Store a context object."""
        raise NotImplementedError
    
    def retrieve(self, context_id: str) -> Optional[MCPContext]:
        """Retrieve a context object."""
        raise NotImplementedError
    
    def delete(self, context_id: str) -> bool:
        """Delete a context object."""
        raise NotImplementedError
    
    def exists(self, context_id: str) -> bool:
        """Check if a context exists."""
        raise NotImplementedError

class InMemoryStorage(MemoryInterface):
    """In-memory implementation of the MCP memory system."""
    
    def __init__(self, default_ttl: int = 86400):  # Increased to 24 hours
        self.storage: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        logger.info(f"Initialized InMemoryStorage with default TTL of {default_ttl} seconds")
    
    def store(self, context_id: str, context: MCPContext, ttl: Optional[int] = None) -> bool:
        """Store a context object with an optional time-to-live."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        try:
            # Store the context as a JSON string
            context_json = context.to_json()
            
            self.storage[context_id] = {
                "context": context_json,
                "expiry": expiry,
                "stored_at": time.time(),
                "document_type": context.metadata.get("document_type", "unknown")
            }
            
            logger.info(f"Stored document {context_id} with expiry in {ttl} seconds. " +
                       f"Document type: {context.metadata.get('document_type', 'unknown')}. " +
                       f"Total documents in storage: {len(self.storage)}")
            
            # Verify the document was stored correctly
            if not self.exists(context_id):
                logger.error(f"Document {context_id} not found in storage after storing")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error storing document {context_id}: {str(e)}")
            return False
    
    def retrieve(self, context_id: str) -> Optional[MCPContext]:
        """Retrieve a context object if it exists and hasn't expired."""
        if not self.exists(context_id):
            logger.warning(f"Document {context_id} not found or expired. Available documents: {list(self.storage.keys())}")
            return None
        
        try:
            # Get the stored context JSON
            context_json = self.storage[context_id]["context"]
            
            # Create a MCPContext from the JSON
            context = MCPContext.from_json(context_json)
            
            logger.info(f"Retrieved document {context_id}")
            return context
        except Exception as e:
            logger.error(f"Error retrieving document {context_id}: {str(e)}")
            return None
    
    def delete(self, context_id: str) -> bool:
        """Delete a context object."""
        if context_id in self.storage:
            del self.storage[context_id]
            logger.info(f"Deleted document {context_id}")
            return True
        logger.warning(f"Attempted to delete non-existent document {context_id}")
        return False
    
    def exists(self, context_id: str) -> bool:
        """Check if a context exists and hasn't expired."""
        if context_id not in self.storage:
            return False
        
        if time.time() > self.storage[context_id]["expiry"]:
            logger.info(f"Document {context_id} has expired and will be deleted")
            self.delete(context_id)
            return False
        
        return True
    
    def cleanup(self):
        """Remove expired contexts."""
        current_time = time.time()
        expired_keys = [
            context_id for context_id, data in self.storage.items()
            if current_time > data["expiry"]
        ]
        
        if expired_keys:
            logger.info(f"Cleaning up {len(expired_keys)} expired documents")
        
        for key in expired_keys:
            self.delete(key)
    
    def get_all_documents(self) -> List[str]:
        """Get a list of all document IDs in storage."""
        self.cleanup()  # Clean up expired documents first
        return list(self.storage.keys())
    
    def get_document_info(self, context_id: str) -> Optional[Dict]:
        """Get metadata about a stored document."""
        if not self.exists(context_id):
            return None
        
        doc_data = self.storage[context_id]
        return {
            "document_id": context_id,
            "document_type": doc_data.get("document_type", "unknown"),
            "stored_at": doc_data.get("stored_at", 0),
            "expires_at": doc_data.get("expiry", 0),
            "ttl_remaining": max(0, doc_data.get("expiry", 0) - time.time())
        }

class FileStorage(MemoryInterface):
    """File-based implementation of the MCP memory system that persists between server restarts."""
    
    def __init__(self, storage_dir: str = "data/documents", default_ttl: int = 86400):
        self.storage_dir = Path(storage_dir)
        self.default_ttl = default_ttl
        
        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a metadata file to track document expiry
        self.metadata_file = self.storage_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"Initialized FileStorage with storage directory: {storage_dir}")
        logger.info(f"Default TTL: {default_ttl} seconds")
        logger.info(f"Found {len(self.metadata)} existing documents")
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Load metadata from file."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
    
    def _get_document_path(self, context_id: str) -> Path:
        """Get the path to a document file."""
        return self.storage_dir / f"{context_id}.json"
    
    def store(self, context_id: str, context: MCPContext, ttl: Optional[int] = None) -> bool:
        """Store a context object with an optional time-to-live."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        try:
            # Store the context as a JSON string
            context_json = context.to_json()
            
            # Save the context to a file
            document_path = self._get_document_path(context_id)
            with open(document_path, "w") as f:
                f.write(context_json)
            
            # Update metadata
            self.metadata[context_id] = {
                "expiry": expiry,
                "stored_at": time.time(),
                "document_type": context.metadata.get("document_type", "unknown"),
                "filename": context.metadata.get("filename", "unknown")
            }
            
            # Save metadata
            self._save_metadata()
            
            logger.info(f"Stored document {context_id} to file {document_path}")
            return True
        except Exception as e:
            logger.error(f"Error storing document {context_id}: {str(e)}")
            return False
    
    def retrieve(self, context_id: str) -> Optional[MCPContext]:
        """Retrieve a context object if it exists and hasn't expired."""
        if not self.exists(context_id):
            return None
        
        try:
            # Get the document path
            document_path = self._get_document_path(context_id)
            
            # Read the context from the file
            with open(document_path, "r") as f:
                context_json = f.read()
            
            # Create a MCPContext from the JSON
            context = MCPContext.from_json(context_json)
            
            logger.info(f"Retrieved document {context_id} from file {document_path}")
            return context
        except Exception as e:
            logger.error(f"Error retrieving document {context_id}: {str(e)}")
            return None
    
    def delete(self, context_id: str) -> bool:
        """Delete a context object."""
        if context_id not in self.metadata:
            return False
        
        try:
            # Delete the document file
            document_path = self._get_document_path(context_id)
            if document_path.exists():
                document_path.unlink()
            
            # Remove from metadata
            del self.metadata[context_id]
            
            # Save metadata
            self._save_metadata()
            
            logger.info(f"Deleted document {context_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {context_id}: {str(e)}")
            return False
    
    def exists(self, context_id: str) -> bool:
        """Check if a context exists and hasn't expired."""
        # Check if the document is in metadata
        if context_id not in self.metadata:
            return False
        
        # Check if the document has expired
        if time.time() > self.metadata[context_id]["expiry"]:
            logger.info(f"Document {context_id} has expired and will be deleted")
            self.delete(context_id)
            return False
        
        # Check if the document file exists
        document_path = self._get_document_path(context_id)
        return document_path.exists()
    
    def cleanup(self):
        """Remove expired contexts."""
        current_time = time.time()
        expired_keys = [
            context_id for context_id, data in self.metadata.items()
            if current_time > data["expiry"]
        ]
        
        if expired_keys:
            logger.info(f"Cleaning up {len(expired_keys)} expired documents")
        
        for key in expired_keys:
            self.delete(key)
    
    def get_all_documents(self) -> List[str]:
        """Get a list of all document IDs in storage."""
        self.cleanup()  # Clean up expired documents first
        return list(self.metadata.keys())
    
    def get_document_info(self, context_id: str) -> Optional[Dict]:
        """Get metadata about a stored document."""
        if not self.exists(context_id):
            return None
        
        doc_data = self.metadata[context_id]
        return {
            "document_id": context_id,
            "document_type": doc_data.get("document_type", "unknown"),
            "filename": doc_data.get("filename", "unknown"),
            "stored_at": doc_data.get("stored_at", 0),
            "expires_at": doc_data.get("expiry", 0),
            "ttl_remaining": max(0, doc_data.get("expiry", 0) - time.time())
        }

# Factory for creating different memory systems
def get_memory_store(memory_type: str = "file", **kwargs) -> MemoryInterface:
    """Factory function to create a memory store based on configuration."""
    if memory_type == "in_memory":
        return InMemoryStorage(default_ttl=kwargs.get("ttl", 86400))  # Default 24 hours
    elif memory_type == "file":
        return FileStorage(
            storage_dir=kwargs.get("storage_dir", "data/documents"),
            default_ttl=kwargs.get("ttl", 86400)
        )
    else:
        raise ValueError(f"Unsupported memory type: {memory_type}")