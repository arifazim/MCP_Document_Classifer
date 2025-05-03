from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from mcp.context import MCPContext

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Base class for all document processors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    def process(self, context: MCPContext) -> MCPContext:
        """Process the document and update the context."""
        pass
    
    @abstractmethod
    def can_handle(self, context: MCPContext) -> bool:
        """Determine if this processor can handle the given document."""
        pass
    
    def extract_common_metadata(self, context: MCPContext) -> Dict[str, Any]:
        """Extract common metadata fields across document types."""
        metadata = {}
        # Implementation would depend on the specific business requirements
        return metadata
    
    def validate_context(self, context: MCPContext) -> bool:
        """Validate that the context has the necessary data for processing."""
        if not context.document_id:
            logger.error("Missing document ID in context")
            return False
        
        if not context.raw_text and not context.extracted_data:
            logger.error(f"No content to process for document {context.document_id}")
            return False
            
        return True