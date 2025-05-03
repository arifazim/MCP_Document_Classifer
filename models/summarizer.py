from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

class T5Summarizer:
    """Document summarizer using T5 model."""
    
    def __init__(self, model_name: str, max_length: int = 150):
        self.model_name = model_name
        self.max_length = max_length
        self.last_confidence = 0.0
        
        logger.info(f"Initialized mock T5Summarizer with model: {model_name}")
        
    def predict(self, text: str) -> str:
        """Generate a prediction (summary)."""
        return self.summarize(text)
        
    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """Generate a summary of the text using mock implementation."""
        if max_length is None:
            max_length = self.max_length
            
        try:
            # Mock implementation - extract key sentences
            
            # Split text into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            if not sentences:
                return ""
                
            # Simple extractive summarization
            # 1. Take the first sentence (often contains the main point)
            summary_sentences = [sentences[0]]
            
            # 2. Look for sentences with important keywords
            important_keywords = ["important", "significant", "key", "main", "critical", "essential", 
                                 "conclusion", "therefore", "result", "summary", "finally"]
            
            for sentence in sentences[1:]:
                # Add sentences with important keywords
                if any(keyword in sentence.lower() for keyword in important_keywords):
                    summary_sentences.append(sentence)
                    
                # Stop if we've reached a reasonable length
                if len(" ".join(summary_sentences)) >= max_length:
                    break
            
            # 3. If summary is still too short, add more sentences from the beginning
            if len(summary_sentences) < 3 and len(sentences) > 3:
                for sentence in sentences[1:4]:  # Add 2nd and 3rd sentences if needed
                    if sentence not in summary_sentences:
                        summary_sentences.append(sentence)
                        
                        if len(" ".join(summary_sentences)) >= max_length:
                            break
            
            # Combine sentences and truncate to max_length
            summary = " ".join(summary_sentences)
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            # Set a fixed confidence for summarization
            self.last_confidence = 0.8
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            self.last_confidence = 0.0
            return ""
    
    def get_confidence(self) -> float:
        """Get the confidence score of the last prediction."""
        return self.last_confidence