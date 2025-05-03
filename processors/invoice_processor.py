from typing import Dict, Any, List, Pattern
import re
import logging
from datetime import datetime
from .base_processor import BaseProcessor
from mcp.context import MCPContext
from models.entity_extractor import BERTEntityExtractor

logger = logging.getLogger(__name__)

class InvoiceProcessor(BaseProcessor):
    """Processor for handling invoice documents."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entity_extractor = BERTEntityExtractor(
            model_name=config["models"]["entity_extractor"]["model_name"],
            confidence_threshold=config["models"]["entity_extractor"]["confidence_threshold"]
        )
        
        # Regular expressions for common invoice fields
        self.patterns = {
            "invoice_number": re.compile(r"(?i)Invoice\s*#?\s*[:]\s*([A-Za-z0-9\-]+)"),
            "date": re.compile(r"(?i)(?:Invoice\s*Date|Date)[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"),
            "due_date": re.compile(r"(?i)Due\s*Date[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"),
            "total_amount": re.compile(r"(?i)(?:Total|Amount\s*Due)[:]\s*[$€£]?\s*([\d,]+\.\d{2})")
        }
    
    def can_handle(self, context: MCPContext) -> bool:
        """Check if the document is an invoice."""
        if not context.raw_text:
            if context.compressed:
                context.decompress()
            if not context.raw_text:
                return False
        
        # Check if document is already classified
        if context.metadata.get("document_type") == "invoice":
            return True
            
        # Look for invoice indicators in the text
        invoice_indicators = [
            "invoice", "bill to", "ship to", "payment terms", 
            "due date", "invoice number", "qty", "quantity"
        ]
        
        text_lower = context.raw_text.lower()
        indicator_count = sum(1 for indicator in invoice_indicators if indicator in text_lower)
        
        # If at least 3 indicators are found, consider it an invoice
        return indicator_count >= 3
    
    def process(self, context: MCPContext) -> MCPContext:
        """Process an invoice document."""
        if not self.validate_context(context):
            context.add_to_history(
                processor_name=self.__class__.__name__,
                status="skipped",
                details={"reason": "Invalid context"}
            )
            return context
            
        if context.compressed:
            context.decompress()
            
        # Mark document as invoice
        context.update_metadata({"document_type": "invoice"})
        
        # Extract basic fields using regex
        extracted_fields = self._extract_basic_fields(context.raw_text)
        for field, value in extracted_fields.items():
            context.add_extracted_data(field, value, confidence=0.9)  # High confidence for regex matches
            
        # Use ML-based entity extraction for more complex fields
        entities = self.entity_extractor.extract_entities(context.raw_text)
        
        # Process line items
        line_items = self._extract_line_items(context.raw_text, entities)
        if line_items:
            context.add_extracted_data("line_items", line_items, 
                                    confidence=self.entity_extractor.get_confidence())
            
        # Extract vendor and customer information
        if "organization" in entities:
            organizations = entities["organization"]
            if len(organizations) >= 1:
                # Assume first organization is the vendor
                context.add_extracted_data("vendor", organizations[0]["text"], 
                                        confidence=organizations[0]["confidence"])
                
            if len(organizations) >= 2:
                # Assume second organization is the customer
                context.add_extracted_data("customer", organizations[1]["text"], 
                                        confidence=organizations[1]["confidence"])
                
        # Calculate and validate totals
        self._validate_totals(context)
        
        return context
    
    def _extract_basic_fields(self, text: str) -> Dict[str, Any]:
        """Extract basic invoice fields using regex patterns."""
        results = {}
        
        for field, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                
                # Convert dates to ISO format
                if field in ["date", "due_date"]:
                    try:
                        # Try different date formats
                        for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"]:
                            try:
                                date_obj = datetime.strptime(value, fmt)
                                value = date_obj.isoformat()[:10]  # YYYY-MM-DD
                                break
                            except ValueError:
                                continue
                    except Exception:
                        # Keep original if parsing fails
                        pass
                
                # Convert amounts to float
                if field == "total_amount":
                    value = float(value.replace(",", ""))
                
                results[field] = value
                
        return results
    
    def _extract_line_items(self, text: str, entities: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Extract line items from the invoice."""
        line_items = []
        
        # Implementation would depend on the specific invoice format
        # This is a simplified example
        
        return line_items
    
    def _validate_totals(self, context: MCPContext) -> None:
        """Validate that line item totals match the invoice total."""
        total_amount = context.extracted_data.get("total_amount")
        line_items = context.extracted_data.get("line_items", [])
        
        if total_amount and line_items:
            line_items_total = sum(item.get("amount", 0) for item in line_items)
            
            # Allow for small rounding differences
            if abs(total_amount - line_items_total) > 0.02:
                context.add_extracted_data(
                    "total_validated", 
                    False, 
                    confidence=1.0
                )
                context.add_to_history(
                    processor_name=self.__class__.__name__,
                    status="warning",
                    details={
                        "message": "Total amount doesn't match sum of line items",
                        "invoice_total": total_amount,
                        "calculated_total": line_items_total
                    }
                )
            else:
                context.add_extracted_data("total_validated", True, confidence=1.0)