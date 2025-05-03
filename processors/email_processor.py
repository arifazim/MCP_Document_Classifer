from typing import Dict, Any, List, Pattern
import re
import logging
from datetime import datetime
from .base_processor import BaseProcessor
from mcp.context import MCPContext
from models.entity_extractor import BERTEntityExtractor

logger = logging.getLogger(__name__)

class EmailProcessor(BaseProcessor):
    """Processor for handling email documents."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entity_extractor = BERTEntityExtractor(
            model_name=config["models"]["entity_extractor"]["model_name"],
            confidence_threshold=config["models"]["entity_extractor"]["confidence_threshold"]
        )
        
        # Regular expressions for common email fields
        self.patterns = {
            "from": re.compile(r"(?i)From:\s*([^<\n]+)(?:<([^>]+)>)?"),
            "to": re.compile(r"(?i)To:\s*([^<\n]+)(?:<([^>]+)>)?"),
            "subject": re.compile(r"(?i)Subject:\s*(.+)(?:\n|$)"),
            "date": re.compile(r"(?i)Date:\s*(.+)(?:\n|$)"),
            "cc": re.compile(r"(?i)Cc:\s*(.+)(?:\n|$)")
        }
    
    def can_handle(self, context: MCPContext) -> bool:
        """Check if the document is an email."""
        if not context.raw_text:
            if context.compressed:
                context.decompress()
            if not context.raw_text:
                return False
        
        # Check if document is already classified
        if context.metadata.get("document_type") == "email":
            return True
            
        # Look for email indicators in the text
        email_indicators = [
            "from:", "to:", "subject:", "sent:", "cc:", "bcc:",
            "forwarded message", "original message", "reply"
        ]
        
        text_lower = context.raw_text.lower()
        indicator_count = sum(1 for indicator in email_indicators if indicator in text_lower)
        
        # If at least 3 indicators are found, consider it an email
        return indicator_count >= 3
    
    def process(self, context: MCPContext) -> MCPContext:
        """Process an email document."""
        if not self.validate_context(context):
            context.add_to_history(
                processor_name=self.__class__.__name__,
                status="skipped",
                details={"reason": "Invalid context"}
            )
            return context
            
        if context.compressed:
            context.decompress()
            
        # Mark document as email
        context.update_metadata({"document_type": "email"})
        
        # Extract basic fields using regex
        extracted_fields = self._extract_basic_fields(context.raw_text)
        for field, value in extracted_fields.items():
            context.add_extracted_data(field, value, confidence=0.9)  # High confidence for regex matches
            
        # Use ML-based entity extraction for more complex fields
        entities = self.entity_extractor.extract_entities(context.raw_text)
        
        # Extract email body (simplified approach)
        body = self._extract_body(context.raw_text)
        if body:
            context.add_extracted_data("body", body, confidence=0.85)
            
        # Extract people mentioned in the email
        if "person" in entities:
            people = entities["person"]
            if people:
                context.add_extracted_data("people_mentioned", 
                                        [person["text"] for person in people], 
                                        confidence=self.entity_extractor.get_confidence())
                
        # Extract organizations mentioned
        if "organization" in entities:
            orgs = entities["organization"]
            if orgs:
                context.add_extracted_data("organizations_mentioned", 
                                        [org["text"] for org in orgs], 
                                        confidence=self.entity_extractor.get_confidence())
        
        return context
    
    def _extract_basic_fields(self, text: str) -> Dict[str, Any]:
        """Extract basic email fields using regex patterns."""
        results = {}
        
        for field, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                if field in ["from", "to"] and match.group(2):
                    # If email address is captured in second group
                    results[field] = {
                        "name": match.group(1).strip(),
                        "email": match.group(2).strip()
                    }
                else:
                    results[field] = match.group(1).strip()
                
        return results
    
    def _extract_body(self, text: str) -> str:
        """Extract the body of the email."""
        # Simple heuristic: look for common email header patterns and extract everything after
        header_patterns = [
            r"(?i)Subject:.+\n\s*\n",
            r"(?i)Date:.+\n\s*\n",
            r"(?i)To:.+\n\s*\n"
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, text)
            if match:
                start_idx = match.end()
                # Look for signature or footer
                signature_patterns = [
                    r"\n--\s*\n",  # Common signature delimiter
                    r"\n\s*Regards,",
                    r"\n\s*Sincerely,"
                ]
                
                end_idx = len(text)
                for sig_pattern in signature_patterns:
                    sig_match = re.search(sig_pattern, text[start_idx:])
                    if sig_match:
                        end_idx = start_idx + sig_match.start()
                        break
                        
                return text[start_idx:end_idx].strip()
        
        # Fallback: if we can't identify headers, just return the text
        return text