from typing import Dict, Any, List
import logging
import re
from datetime import datetime
from .base_processor import BaseProcessor
from mcp.context import MCPContext
from models.entity_extractor import BERTEntityExtractor
from models.document_classifier import BERTDocumentClassifier
from models.summarizer import T5Summarizer

logger = logging.getLogger(__name__)

class DefaultProcessor(BaseProcessor):
    """Default processor for handling any document type."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entity_extractor = BERTEntityExtractor(
            model_name=config["models"]["entity_extractor"]["model_name"],
            confidence_threshold=config["models"]["entity_extractor"]["confidence_threshold"]
        )
        self.document_classifier = BERTDocumentClassifier(
            model_name=config["models"]["document_classifier"]["model_name"],
            threshold=config["models"]["document_classifier"]["threshold"]
        )
        self.summarizer = T5Summarizer(
            model_name=config["models"]["summarizer"]["model_name"]
        )
    
    def can_handle(self, context: MCPContext) -> bool:
        """This processor can handle any document type."""
        # Always return True as this is the fallback processor
        return True
    
    def process(self, context: MCPContext) -> MCPContext:
        """Process any document type."""
        if not self.validate_context(context):
            context.add_to_history(
                processor_name=self.__class__.__name__,
                status="skipped",
                details={"reason": "Invalid context"}
            )
            return context
            
        if context.compressed:
            context.decompress()
        
        # Classify the document if not already classified
        if not context.metadata.get("document_type"):
            document_type = self.document_classifier.predict(context.raw_text)
            context.update_metadata({"document_type": document_type})
            logger.info(f"Classified document {context.document_id} as {document_type}")
            
            # Add classification confidence
            classification_scores = self.document_classifier.classify(context.raw_text)
            context.add_extracted_data(
                "classification_scores", 
                classification_scores,
                confidence=self.document_classifier.get_confidence()
            )
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(context.raw_text)
        for entity_type, entity_list in entities.items():
            if entity_list:
                context.add_extracted_data(
                    f"extracted_{entity_type}s", 
                    [entity["text"] for entity in entity_list],
                    confidence=self.entity_extractor.get_confidence()
                )
        
        # Generate summary
        try:
            summary = self.summarizer.summarize(context.raw_text, max_length=150)
            context.add_extracted_data("summary", summary, confidence=0.8)
        except Exception as e:
            logger.error(f"Error generating summary for document {context.document_id}: {str(e)}")
        
        # Extract dates
        date_pattern = re.compile(r"(?i)(?:Date|Dated)[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})")
        date_matches = date_pattern.findall(context.raw_text)
        if date_matches:
            dates = []
            for date_str in date_matches:
                try:
                    # Try different date formats
                    for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"]:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            dates.append(date_obj.isoformat()[:10])  # YYYY-MM-DD
                            break
                        except ValueError:
                            continue
                except Exception:
                    # Keep original if parsing fails
                    dates.append(date_str)
            
            if dates:
                context.add_extracted_data("dates", dates, confidence=0.85)
        
        # Extract basic metadata
        metadata = self.extract_common_metadata(context)
        if metadata:
            context.update_metadata(metadata)
        
        return context
    
    def extract_common_metadata(self, context: MCPContext) -> Dict[str, Any]:
        """Extract common metadata fields across document types."""
        metadata = {}
        
        # Extract document language (simplified)
        english_indicators = ["the", "and", "for", "with", "this", "that"]
        spanish_indicators = ["el", "la", "los", "las", "y", "con"]
        french_indicators = ["le", "la", "les", "et", "avec", "ce", "cette"]
        
        text_lower = context.raw_text.lower()
        english_count = sum(1 for word in english_indicators if f" {word} " in text_lower)
        spanish_count = sum(1 for word in spanish_indicators if f" {word} " in text_lower)
        french_count = sum(1 for word in french_indicators if f" {word} " in text_lower)
        
        if english_count > spanish_count and english_count > french_count:
            metadata["language"] = "english"
        elif spanish_count > english_count and spanish_count > french_count:
            metadata["language"] = "spanish"
        elif french_count > english_count and french_count > spanish_count:
            metadata["language"] = "french"
        else:
            metadata["language"] = "unknown"
        
        # Extract word count
        words = re.findall(r'\b\w+\b', context.raw_text)
        metadata["word_count"] = len(words)
        
        # Extract page count (simplified estimate)
        # Assuming average of 500 words per page
        metadata["estimated_pages"] = max(1, len(words) // 500)
        
        return metadata
