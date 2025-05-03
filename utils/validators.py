from typing import Dict, Any, List, Optional
from datetime import datetime
import re

class DataValidator:
    """Utilities for validating extracted data."""
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate if the string is a valid date."""
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%d %B %Y"
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
                
        return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate if the string is a valid email address."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate if the string is a valid phone number."""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if we have a reasonable number of digits
        return 7 <= len(digits_only) <= 15
    
    @staticmethod
    def validate_amount(amount: str) -> bool:
        """Validate if the string is a valid monetary amount."""
        # Remove currency symbols and commas
        clean_amount = re.sub(r'[$€£,]', '', amount)
        
        # Check if it's a valid number
        try:
            float(clean_amount)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def confidence_check(data: Dict[str, Any], confidence_scores: Dict[str, float], 
                        threshold: float = 0.7) -> List[str]:
        """Check which fields have confidence scores below threshold."""
        low_confidence_fields = []
        
        for field, value in data.items():
            if field in confidence_scores and confidence_scores[field] < threshold:
                low_confidence_fields.append(field)
                
        return low_confidence_fields