"""
Enhanced JSON Parser with robust error handling and validation
Fixes JSON parsing issues found in SubQueen agents
"""
import json
import re
import logging
from typing import List, Dict, Any, Union, Optional

class EnhancedJSONParser:
    """
    Robust JSON parser that handles common LLM response issues:
    - Invalid escape sequences
    - Windows path separators
    - Incomplete JSON structures
    - Mixed content (text + JSON)
    - Control characters
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def parse_llm_response(self, response: str, expected_type: str = "array") -> Union[List[str], Dict[str, Any], str]:
        """
        Parse LLM response with multiple fallback strategies
        
        Args:
            response: Raw LLM response text
            expected_type: "array", "object", or "auto"
            
        Returns:
            Parsed data or fallback response
        """
        if not response or not response.strip():
            self.logger.warning("⚠️ Empty response received")
            return [] if expected_type == "array" else {}
        
        # Strategy 1: Direct JSON parsing
        try:
            cleaned = self._clean_response(response)
            parsed = json.loads(cleaned)
            
            # Validate expected type
            if self._validate_type(parsed, expected_type):
                self.logger.info("✅ Direct JSON parsing successful")
                return parsed
                
        except json.JSONDecodeError as e:
            self.logger.debug(f"Direct parsing failed: {e}")
        except Exception as e:
            self.logger.debug(f"Direct parsing error: {e}")
        
        # Strategy 2: Extract JSON from mixed content
        try:
            extracted = self._extract_json_blocks(response)
            for json_block in extracted:
                try:
                    parsed = json.loads(json_block)
                    if self._validate_type(parsed, expected_type):
                        self.logger.info("✅ JSON block extraction successful")
                        return parsed
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            self.logger.debug(f"JSON extraction failed: {e}")
        
        # Strategy 3: Repair and retry
        try:
            repaired = self._repair_json(response)
            parsed = json.loads(repaired)
            if self._validate_type(parsed, expected_type):
                self.logger.info("✅ JSON repair successful")
                return parsed
        except Exception as e:
            self.logger.debug(f"JSON repair failed: {e}")
        
        # Strategy 4: Parse as structured text
        try:
            structured = self._parse_as_structured_text(response, expected_type)
            if structured:
                self.logger.info("✅ Structured text parsing successful")
                return structured
        except Exception as e:
            self.logger.debug(f"Structured text parsing failed: {e}")
        
        # Fallback: Return original response or safe default
        self.logger.warning(f"⚠️ All parsing strategies failed, using fallback")
        return self._create_fallback_response(response, expected_type)
    
    def _clean_response(self, response: str) -> str:
        """Clean response for JSON parsing"""
        # Remove markdown code blocks
        cleaned = response.strip()
        
        # Remove ```json markers
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        # Fix Windows paths in JSON strings
        cleaned = self._fix_windows_paths(cleaned)
        
        # Fix common escape sequence issues
        cleaned = self._fix_escape_sequences(cleaned)
        
        # Remove control characters
        cleaned = self._remove_control_characters(cleaned)
        
        return cleaned
    
    def _fix_windows_paths(self, text: str) -> str:
        """Fix Windows path separators in JSON strings"""
        # Pattern: D:\path\to\file -> D:/path/to/file
        text = re.sub(r'([A-Z]):\\+([^"\\]*)', lambda m: f'{m.group(1)}:/{m.group(2).replace(chr(92), "/")}', text)
        
        # Handle remaining backslashes in paths
        text = re.sub(r'([A-Z]:)/([^"]*?)\\([^"]*)', r'\1/\2/\3', text)
        
        # Fix double backslashes
        text = re.sub(r'\\\\+', r'/', text)
        
        return text
    
    def _fix_escape_sequences(self, text: str) -> str:
        """Fix invalid escape sequences"""
        # Escape unescaped backslashes (but not valid JSON escapes)
        text = re.sub(r'\\(?!["\\bfnrt/uU0-9a-fA-F])', r'\\\\', text)
        
        # Fix newlines in strings
        text = re.sub(r'(?<!\\)\n', r'\\n', text)
        text = re.sub(r'(?<!\\)\r', r'\\r', text)
        text = re.sub(r'(?<!\\)\t', r'\\t', text)
        
        return text
    
    def _remove_control_characters(self, text: str) -> str:
        """Remove problematic control characters"""
        # Remove null bytes and other control characters
        control_chars = ''.join(chr(i) for i in range(32) if i not in [9, 10, 13])  # Keep tab, newline, carriage return
        translator = str.maketrans('', '', control_chars)
        return text.translate(translator)
    
    def _extract_json_blocks(self, text: str) -> List[str]:
        """Extract JSON blocks from mixed content"""
        json_blocks = []
        
        # Pattern 1: ```json blocks
        json_pattern = r'```json\s*\n(.*?)\n```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
        json_blocks.extend(matches)
        
        # Pattern 2: Generic ``` blocks
        generic_pattern = r'```\s*\n(.*?)\n```'
        matches = re.findall(generic_pattern, text, re.DOTALL)
        json_blocks.extend(matches)
        
        # Pattern 3: Standalone arrays/objects
        array_pattern = r'\[[\s\S]*?\]'
        object_pattern = r'\{[\s\S]*?\}'
        
        array_matches = re.findall(array_pattern, text)
        object_matches = re.findall(object_pattern, text)
        
        json_blocks.extend(array_matches)
        json_blocks.extend(object_matches)
        
        return json_blocks
    
    def _repair_json(self, text: str) -> str:
        """Attempt to repair malformed JSON"""
        cleaned = self._clean_response(text)
        
        # Fix trailing commas
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        # Fix missing quotes around keys
        cleaned = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', cleaned)
        
        # Fix single quotes to double quotes
        cleaned = re.sub(r"'([^']*)'", r'"\1"', cleaned)
        
        # Fix incomplete objects/arrays
        if cleaned.startswith('[') and not cleaned.endswith(']'):
            cleaned += ']'
        elif cleaned.startswith('{') and not cleaned.endswith('}'):
            cleaned += '}'
        
        # Remove incomplete entries at the end
        if cleaned.endswith(','):
            cleaned = cleaned[:-1]
        
        return cleaned
    
    def _parse_as_structured_text(self, text: str, expected_type: str) -> Union[List[str], Dict[str, Any], None]:
        """Parse structured text when JSON parsing fails"""
        if expected_type == "array":
            return self._extract_list_items(text)
        elif expected_type == "object":
            return self._extract_key_value_pairs(text)
        return None
    
    def _extract_list_items(self, text: str) -> List[str]:
        """Extract list items from text"""
        items = []
        
        # Pattern 1: Numbered list
        numbered_pattern = r'^\s*\d+\.?\s*(.+)$'
        for line in text.split('\n'):
            match = re.match(numbered_pattern, line.strip())
            if match:
                items.append(match.group(1).strip(' "\''))
        
        if items:
            return items
        
        # Pattern 2: Bullet points
        bullet_pattern = r'^\s*[-*•]\s*(.+)$'
        for line in text.split('\n'):
            match = re.match(bullet_pattern, line.strip())
            if match:
                items.append(match.group(1).strip(' "\''))
        
        if items:
            return items
        
        # Pattern 3: Quoted items
        quoted_pattern = r'"([^"]+)"'
        quoted_items = re.findall(quoted_pattern, text)
        if quoted_items:
            return quoted_items
        
        # Pattern 4: Split by common delimiters
        for delimiter in ['\n', ',', ';']:
            potential_items = [item.strip(' "\'') for item in text.split(delimiter)]
            potential_items = [item for item in potential_items if item and len(item) > 3]
            if len(potential_items) > 1:
                return potential_items
        
        return []
    
    def _extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Extract key-value pairs from text"""
        pairs = {}
        
        # Pattern 1: key: value
        kv_pattern = r'^([^:]+):\s*(.+)$'
        for line in text.split('\n'):
            match = re.match(kv_pattern, line.strip())
            if match:
                key = match.group(1).strip(' "\'')
                value = match.group(2).strip(' "\'')
                pairs[key] = value
        
        return pairs if pairs else {}
    
    def _validate_type(self, data: Any, expected_type: str) -> bool:
        """Validate that parsed data matches expected type"""
        if expected_type == "array":
            return isinstance(data, list)
        elif expected_type == "object":
            return isinstance(data, dict)
        elif expected_type == "auto":
            return isinstance(data, (list, dict))
        return True
    
    def _create_fallback_response(self, original: str, expected_type: str) -> Union[List[str], Dict[str, Any], str]:
        """Create safe fallback response"""
        if expected_type == "array":
            # Try to extract something meaningful as a single item
            clean_text = re.sub(r'[^\w\s\-.,]', ' ', original)
            clean_text = ' '.join(clean_text.split())
            if clean_text:
                return [clean_text[:200]]  # Truncate to reasonable length
            return []
        elif expected_type == "object":
            return {"error": "Failed to parse response", "original": original[:100]}
        else:
            return original

def parse_subtasks(llm_response: str) -> List[str]:
    """
    Convenience function for parsing subtask responses
    
    Args:
        llm_response: Raw LLM response containing subtasks
        
    Returns:
        List of subtask strings
    """
    parser = EnhancedJSONParser()
    result = parser.parse_llm_response(llm_response, "array")
    
    if isinstance(result, list):
        # Ensure all items are strings and filter out empty ones
        return [str(item).strip() for item in result if str(item).strip()]
    else:
        # Fallback to single task
        return [str(result)]

def parse_task_structure(llm_response: str) -> Dict[str, Any]:
    """
    Convenience function for parsing structured task responses
    
    Args:
        llm_response: Raw LLM response containing task structure
        
    Returns:
        Dictionary with task structure
    """
    parser = EnhancedJSONParser()
    result = parser.parse_llm_response(llm_response, "object")
    
    if isinstance(result, dict):
        return result
    else:
        # Create structure from response
        return {
            "task": str(result),
            "type": "unstructured",
            "parsed_at": "fallback"
        }

if __name__ == '__main__':
    # Test the enhanced JSON parser
    print("🧪 Testing Enhanced JSON Parser...")
    
    parser = EnhancedJSONParser()
    
    # Test cases from the log
    test_cases = [
        # Case 1: Valid JSON array
        '''```json
[
  "Research and understand the capabilities and limitations of openCV for image recognition tasks.",
  "Familiarize yourself with data augmentation techniques specific to water imagery from drones"
]
```''',
        
        # Case 2: JSON with Windows paths (problematic)
        '''[{"agent": "analyst", "path": "D:\\Datasets\\Rescue\\kaggle\\PART_1\\PART_1"}]''',
        
        # Case 3: Incomplete JSON with control characters
        '''[
  {"agent": "data scientist", "subtask": "Determine the specific libraries needed"},
  {"agentdependent on your request? I can provide''',
        
        # Case 4: Plain text list
        '''1. Research OpenCV capabilities
2. Install required libraries
3. Create image processing pipeline'''
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"Input: {test_case[:100]}...")
        
        result = parser.parse_llm_response(test_case, "array")
        print(f"✅ Parsed: {result}")
        print(f"Type: {type(result)}, Count: {len(result) if isinstance(result, (list, dict)) else 'N/A'}")
    
    print("\n✅ JSON parser test completed")