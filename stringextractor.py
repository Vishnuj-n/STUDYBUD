import re
from typing import List, Optional

class StringExtractor:
    """
    A class for extracting structured data from text strings.
    Currently supports extracting Python lists from code blocks or direct list notation.
    """
    
    def __init__(self):
        """Initialize the StringExtractor with regular expression patterns."""
        self._code_block_pattern = r"```python\s+([\s\S]*?)```"
        self._list_pattern = r"(\w+)\s*=\s*\[([\s\S]*?)\]"
        self._direct_list_pattern = r"\[([\s\S]*?)\]"
        self._item_pattern = r'["\'](.*?)["\']'
    
    def extract_list_from_string(self, text: str) -> List[str]:
        """
        Extract a Python list from a string containing code blocks, direct list notation,
        or natural language lists.
        
        Args:
            text (str): The input string that may contain a Python list
        
        Returns:
            list: The extracted list of items, or an empty list if no list is found.
        """
        # First try to extract from code blocks
        extracted_list = self._extract_from_code_blocks(text)
        if extracted_list is not None:
            return extracted_list
        
        # If not found in code blocks, try direct list pattern
        extracted_list = self._extract_from_direct_list(text)
        if extracted_list is not None:
            return extracted_list

        # If not found in the above, try natural language list pattern
        extracted_list = self._extract_from_natural_language_list(text)
        if extracted_list is not None:
            return extracted_list

        return []
    
    def _extract_from_code_blocks(self, text: str) -> Optional[List[str]]:
        """Extract list from Python code blocks in the text."""
        code_blocks = re.findall(self._code_block_pattern, text)
        
        for block in code_blocks:
            list_matches = re.findall(self._list_pattern, block)
            
            for _, list_content in list_matches:
                items = re.findall(self._item_pattern, list_content)
                return items
        
        return None
    
    def _extract_from_direct_list(self, text: str) -> Optional[List[str]]:
        """Extract list from direct list notation in the text."""
        match = re.search(self._direct_list_pattern, text)
        
        if match:
            list_content = match.group(1)
            if not list_content.strip():
                return []
            
            # Split by comma, then clean up each item
            items = list_content.split(',')
            
            cleaned_items = []
            for item in items:
                # Remove leading/trailing whitespace
                item = item.strip()
                # Remove potential list markers like "1.", "-", "*"
                item = re.sub(r'^\s*(\d+\.|\*|-)\s*', '', item)
                # Remove surrounding quotes
                item = re.sub(r'^["\']|["\']$', '', item)
                # Add to list if not empty
                if item:
                    cleaned_items.append(item)
            return cleaned_items
        
        return None

    def _extract_from_natural_language_list(self, text: str) -> Optional[List[str]]:
        """Extract list from natural language text (numbered or bulleted)."""
        # This regex splits the string by list markers (e.g., "1. ", "- ", "* ").
        splitter = re.compile(r'\s*(?:\d+\.|\*|-)\s*')
        
        # Don't process if no markers are found
        if not splitter.search(text):
            return None

        potential_items = splitter.split(text)
        
        # Filter out empty strings that result from splitting, and strip whitespace.
        items = [item.strip() for item in potential_items if item.strip()]
        
        # Clean up items by removing trailing punctuation that might be part of the sentence structure.
        cleaned_items = []
        for item in items:
            # Remove trailing dots or ellipses, but not other punctuation like '!'
            cleaned_item = re.sub(r'\.{1,3}\s*$', '', item).strip()
            if cleaned_item:
                cleaned_items.append(cleaned_item)
                
        return cleaned_items if cleaned_items else None


