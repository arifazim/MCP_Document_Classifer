from typing import Dict, Any, Optional, List
import json
import zlib
from dataclasses import dataclass, field

@dataclass
class MCPContext:
    """Context object for storing and managing context across MCP components."""
    
    document_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    processing_history: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    raw_text: Optional[str] = None
    compressed: bool = False
    
    def add_to_history(self, processor_name: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Add a processing step to the history."""
        from datetime import datetime
        
        self.processing_history.append({
            "processor": processor_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })
    
    def update_metadata(self, new_metadata: Dict[str, Any]):
        """Update the metadata dictionary."""
        self.metadata.update(new_metadata)
        
    def add_extracted_data(self, key: str, data: Any, confidence: float = 1.0):
        """Add extracted data with confidence score."""
        self.extracted_data[key] = data
        self.confidence_scores[key] = confidence
        
    def compress(self):
        """Compress the raw text to save memory."""
        if not self.compressed and self.raw_text:
            self.raw_text = zlib.compress(self.raw_text.encode()).hex()
            self.compressed = True
            
    def decompress(self):
        """Decompress the raw text."""
        if self.compressed and self.raw_text:
            self.raw_text = zlib.decompress(bytes.fromhex(self.raw_text)).decode()
            self.compressed = False
    
    def to_json(self) -> str:
        """Convert context to JSON string."""
        if not self.compressed and self.raw_text:
            self.compress()
        return json.dumps({
            "document_id": self.document_id,
            "metadata": self.metadata,
            "extracted_data": self.extracted_data,
            "processing_history": self.processing_history,
            "confidence_scores": self.confidence_scores,
            "raw_text": self.raw_text,
            "compressed": self.compressed
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPContext':
        """Create context from JSON string."""
        data = json.loads(json_str)
        context = cls(
            document_id=data["document_id"],
            metadata=data.get("metadata", {}),
            extracted_data=data.get("extracted_data", {}),
            processing_history=data.get("processing_history", []),
            confidence_scores=data.get("confidence_scores", {}),
            raw_text=data.get("raw_text"),
            compressed=data.get("compressed", False)
        )
        return context