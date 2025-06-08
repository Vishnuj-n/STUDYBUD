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
    
    def extract_list_from_string(self, text: str) -> Optional[List[str]]:
        """
        Extract a Python list from a string containing code blocks or direct list notation.
        
        Args:
            text (str): The input string that may contain a Python list
        
        Returns:
            list: The extracted list of items, or None if no list is found
        """
        # First try to extract from code blocks
        extracted_list = self._extract_from_code_blocks(text)
        if extracted_list:
            return extracted_list
        
        # If not found in code blocks, try direct list pattern
        return self._extract_from_direct_list(text)
    
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
        direct_matches = re.findall(self._direct_list_pattern, text)
        
        if direct_matches:
            items = re.findall(self._item_pattern, direct_matches[0])
            return items
        
        return None


