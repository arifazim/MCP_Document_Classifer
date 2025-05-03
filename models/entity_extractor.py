from typing import Dict, Any, List, Optional
import logging
import random  # Used for mock implementation

logger = logging.getLogger(__name__)

class BERTEntityExtractor:
    """Entity extractor using BERT for named entity recognition."""
    
    def __init__(self, model_name: str, confidence_threshold: float = 0.5):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.last_confidence = 0.0
        
        # Define entity types
        self.entities = ["person", "organization", "location", "date", "money", "percent", "time", "product"]
        self.id2label = {i: label for i, label in enumerate(self.entities)}
        self.label2id = {label: i for i, label in self.id2label.items()}
        
        logger.info(f"Initialized mock BERTEntityExtractor with model: {model_name}")
        
    def predict(self, text: str) -> List[Dict[str, Any]]:
        """Extract all entities from text."""
        entities = self.extract_entities(text)
        # Flatten the entities
        return [entity for entity_type in entities.values() for entity in entity_type]
        
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities from text using mock implementation."""
        results = {entity_type: [] for entity_type in self.entities}
        
        try:
            # Mock implementation - extract simple patterns
            # Organization detection (simple heuristic)
            for company in ["Acme Corp", "TechSolutions", "Global Industries", "ABC Company"]:
                if company.lower() in text.lower():
                    confidence = random.uniform(0.75, 0.95)
                    results["organization"].append({
                        "text": company,
                        "start": text.lower().find(company.lower()),
                        "end": text.lower().find(company.lower()) + len(company),
                        "confidence": confidence
                    })
            
            # Person detection (simple heuristic)
            for person in ["John Smith", "Jane Doe", "Robert Johnson", "Sarah Williams"]:
                if person.lower() in text.lower():
                    confidence = random.uniform(0.75, 0.95)
                    results["person"].append({
                        "text": person,
                        "start": text.lower().find(person.lower()),
                        "end": text.lower().find(person.lower()) + len(person),
                        "confidence": confidence
                    })
            
            # Date detection (simple regex-like approach)
            import re
            date_patterns = [
                r"\d{1,2}/\d{1,2}/\d{2,4}",  # MM/DD/YYYY
                r"\d{1,2}-\d{1,2}-\d{2,4}",  # MM-DD-YYYY
                r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)? \d{1,2},? \d{4}"
            ]
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    confidence = random.uniform(0.8, 0.98)
                    results["date"].append({
                        "text": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": confidence
                    })
            
            # Money detection (simple regex-like approach)
            money_matches = re.finditer(r"\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})? (?:dollars|USD)", text)
            for match in money_matches:
                confidence = random.uniform(0.85, 0.98)
                results["money"].append({
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": confidence
                })
            
            # Set overall confidence as average of all entity confidences
            all_confidences = [entity["confidence"] for entities in results.values() for entity in entities]
            self.last_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            return results
            
        except Exception as e:
            logger.error(f"Error in entity extraction: {str(e)}")
            self.last_confidence = 0.0
            return {entity_type: [] for entity_type in self.entities}
    
    def get_confidence(self) -> float:
        """Get the confidence score of the last prediction."""
        return self.last_confidence