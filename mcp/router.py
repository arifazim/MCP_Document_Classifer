from typing import List, Dict, Any, Type, Optional
import logging
from .context import MCPContext
from .protocols import Processor

logger = logging.getLogger(__name__)

class ProcessorRouter:
    """Routes documents to appropriate processors based on document type and content."""
    
    def __init__(self, processors: List[Processor]):
        self.processors = processors
        
    def route(self, context: MCPContext) -> Optional[Processor]:
        """Find the appropriate processor for the document."""
        for processor in self.processors:
            if processor.can_handle(context):
                logger.info(f"Selected processor: {processor.__class__.__name__} for document {context.document_id}")
                return processor
        
        logger.warning(f"No suitable processor found for document {context.document_id}")
        return None
    
    def process_document(self, context: MCPContext) -> MCPContext:
        """Process a document using the appropriate processor."""
        processor = self.route(context)
        
        if processor:
            context.add_to_history(
                processor_name=processor.__class__.__name__,
                status="started"
            )
            
            try:
                processed_context = processor.process(context)
                processed_context.add_to_history(
                    processor_name=processor.__class__.__name__,
                    status="completed"
                )
                return processed_context
            except Exception as e:
                context.add_to_history(
                    processor_name=processor.__class__.__name__,
                    status="failed",
                    details={"error": str(e)}
                )
                logger.error(f"Error processing document {context.document_id}: {str(e)}")
                raise
        else:
            context.add_to_history(
                processor_name="router",
                status="failed",
                details={"error": "No suitable processor found"}
            )
            return context