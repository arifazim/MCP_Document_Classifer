from typing import Dict, Any, List
import re
import logging
from .base_processor import BaseProcessor
from mcp.context import MCPContext
from models.entity_extractor import BERTEntityExtractor
from models.summarizer import T5Summarizer

logger = logging.getLogger(__name__)

class ContractProcessor(BaseProcessor):
    """Processor for handling contract documents."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entity_extractor = BERTEntityExtractor(
            model_name=config["models"]["entity_extractor"]["model_name"],
            confidence_threshold=config["models"]["entity_extractor"]["confidence_threshold"]
        )
        self.summarizer = T5Summarizer(
            model_name=config["models"]["summarizer"]["model_name"],
            max_length=config["models"]["summarizer"]["max_length"]
        )
        
    def can_handle(self, context: MCPContext) -> bool:
        """Check if the document is a contract."""
        if not context.raw_text:
            if context.compressed:
                context.decompress()
            if not context.raw_text:
                return False
        
        # Check if document is already classified
        if context.metadata.get("document_type") == "contract":
            return True
            
        # Look for contract indicators in the text
        contract_indicators = [
            "agreement", "contract", "terms and conditions", "party", "parties",
            "hereby agrees", "obligations", "termination", "governing law"
        ]
        
        text_lower = context.raw_text.lower()
        indicator_count = sum(1 for indicator in contract_indicators if indicator in text_lower)
        
        # If at least 3 indicators are found, consider it a contract
        return indicator_count >= 3
    
    def process(self, context: MCPContext) -> MCPContext:
        """Process a contract document."""
        if not self.validate_context(context):
            context.add_to_history(
                processor_name=self.__class__.__name__,
                status="skipped",
                details={"reason": "Invalid context"}
            )
            return context
            
        if context.compressed:
            context.decompress()
            
        # Mark document as contract
        context.update_metadata({"document_type": "contract"})
        
        # Generate a summary of the contract
        summary = self.summarizer.summarize(context.raw_text)
        context.add_extracted_data("summary", summary, confidence=0.8)
        
        # Extract contract sections
        sections = self._extract_sections(context.raw_text)
        context.add_extracted_data("sections", sections, confidence=0.85)
        
        # Extract key dates
        dates = self._extract_dates(context.raw_text)
        for date_type, date_value in dates.items():
            context.add_extracted_data(f"date_{date_type}", date_value, confidence=0.9)
        
        # Extract parties
        entities = self.entity_extractor.extract_entities(context.raw_text)
        parties = self._extract_parties(context.raw_text, entities)
        context.add_extracted_data("parties", parties, 
                                 confidence=self.entity_extractor.get_confidence())
        
        # Extract key terms
        key_terms = self._extract_key_terms(context.raw_text, sections)
        context.add_extracted_data("key_terms", key_terms, confidence=0.75)
        
        return context
        
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract main sections from the contract."""
        sections = {}
        
        # Simple regex-based section extraction
        # This is a simplified implementation
        section_pattern = re.compile(r'(?i)^[\d\.\s]*([A-Z][A-Z\s]+)[\.\s]*$(.*?)(?=^[\d\.\s]*[A-Z][A-Z\s]+[\.\s]*$|\Z)', 
                                    re.MULTILINE | re.DOTALL)
        
        for match in section_pattern.finditer(text):
            section_title = match.group(1).strip()
            section_content = match.group(2).strip()
            sections[section_title] = section_content
            
        return sections
    
    def _extract_dates(self, text: str) -> Dict[str, str]:
        """Extract key dates from the contract."""
        dates = {}
        
        # Look for effective date
        effective_date_pattern = re.compile(r'(?i)(?:effective\s+date|commencement\s+date|start\s+date)[:\s]+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})')
        effective_match = effective_date_pattern.search(text)
        if effective_match:
            dates["effective"] = effective_match.group(1).strip()
        
        # Look for termination date
        termination_date_pattern = re.compile(r'(?i)(?:termination\s+date|end\s+date|expiry\s+date)[:\s]+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})')
        termination_match = termination_date_pattern.search(text)
        if termination_match:
            dates["termination"] = termination_match.group(1).strip()
            
        return dates
    
    def _extract_parties(self, text: str, entities: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract parties to the contract."""
        parties = []
        
        # Extract organizations
        if "organization" in entities:
            for org in entities["organization"]:
                # Look for context around the organization to determine the role
                context_window = 200  # Characters to look around entity
                start_idx = max(0, org["start"] - context_window)
                end_idx = min(len(text), org["end"] + context_window)
                context_text = text[start_idx:end_idx].lower()
                
                role = None
                if any(indicator in context_text for indicator in ["first party", "party of the first part"]):
                    role = "first_party"
                elif any(indicator in context_text for indicator in ["second party", "party of the second part"]):
                    role = "second_party"
                elif "seller" in context_text:
                    role = "seller"
                elif "buyer" in context_text:
                    role = "buyer"
                elif "lessor" in context_text:
                    role = "lessor"
                elif "lessee" in context_text:
                    role = "lessee"
                
                parties.append({
                    "name": org["text"],
                    "role": role,
                    "confidence": org["confidence"]
                })
                
        return parties
    
    def _extract_key_terms(self, text: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """Extract key contract terms."""
        key_terms = {}
        
        # Extract payment terms
        payment_section = None
        for title, content in sections.items():
            if any(term in title.lower() for term in ["payment", "consideration", "compensation", "fees"]):
                payment_section = content
                break
                
        if payment_section:
            # Look for amounts
            amount_pattern = re.compile(r'(?i)(?:amount|fee|payment|price)[:\s]+[$€£]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
            amount_match = amount_pattern.search(payment_section)
            if amount_match:
                key_terms["payment_amount"] = amount_match.group(1).strip()
                
        # Extract governing law
        law_pattern = re.compile(r'(?i)(?:governed\s+by|governing\s+law|jurisdiction)[:\s]+(?:the\s+laws\s+of\s+)?([A-Za-z\s]+)')
        law_match = law_pattern.search(text)
        if law_match:
            key_terms["governing_law"] = law_match.group(1).strip()
            
        return key_terms