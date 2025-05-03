from typing import Protocol, Dict, Any, List, Optional
from abc import abstractmethod
from .context import MCPContext

class Processor(Protocol):
    """Protocol defining the interface for document processors."""
    
    @abstractmethod
    def process(self, context: MCPContext) -> MCPContext:
        """Process the document and update the context."""
        pass
    
    @abstractmethod
    def can_handle(self, context: MCPContext) -> bool:
        """Determine if this processor can handle the given document."""
        pass

class Model(Protocol):
    """Protocol defining the interface for ML models."""
    
    @abstractmethod
    def predict(self, input_data: Any) -> Any:
        """Make a prediction based on input data."""
        pass
    
    @abstractmethod
    def get_confidence(self) -> float:
        """Get the confidence score of the last prediction."""
        pass

class DocumentClassifier(Model):
    """Protocol for document classification models."""
    
    @abstractmethod
    def classify(self, text: str) -> Dict[str, float]:
        """Classify a document into different categories."""
        pass

class EntityExtractor(Model):
    """Protocol for entity extraction models."""
    
    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities from text."""
        pass

class Summarizer(Model):
    """Protocol for document summarization models."""
    
    @abstractmethod
    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """Generate a summary of the text."""
        pass

class DocumentParser(Protocol):
    """Protocol for document parsing utilities."""
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse a document and return the text content."""
        pass
    
    @abstractmethod
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from the document."""
        pass