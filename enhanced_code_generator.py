"""
Enhanced Code Generator with Quality Control and Validation
Fixes code generation issues found in drone agents
"""
import re
import ast
import tempfile
import subprocess
import os
from typing import Dict, List, Optional, Tuple
import logging

class CodeQualityValidator:
    """Validates generated code for syntax and common issues"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def validate_python_code(self, code: str) -> Tuple[bool, List[str], str]:
        """
        Validate Python code for syntax errors and common issues
        
        Returns:
            (is_valid, issues_found, corrected_code)
        """
        issues = []
        corrected_code = code
        
        try:
            # Fix common typos and issues first
            corrected_code = self._fix_common_issues(code)
            
            # Check syntax
            ast.parse(corrected_code)
            self.logger.info("✅ Code syntax validation passed")
            
            # Check for common problems
            additional_issues = self._check_code_quality(corrected_code)
            issues.extend(additional_issues)
            
            return True, issues, corrected_code
            
        except SyntaxError as e:
            issues.append(f"Syntax Error: {e.msg} at line {e.lineno}")
            self.logger.error(f"❌ Syntax error in generated code: {e}")
            
            # Try to fix syntax errors
            fixed_code = self._attempt_syntax_fix(corrected_code, e)
            if fixed_code != corrected_code:
                try:
                    ast.parse(fixed_code)
                    self.logger.info("✅ Syntax error fixed automatically")
                    return True, issues, fixed_code
                except SyntaxError:
                    pass
            
            return False, issues, corrected_code
            
        except Exception as e:
            issues.append(f"Validation Error: {str(e)}")
            self.logger.error(f"❌ Code validation failed: {e}")
            return False, issues, corrected_code
    
    def _fix_common_issues(self, code: str) -> str:
        """Fix common code generation issues"""
        fixed_code = code
        
        # Fix 1: cv20 -> cv2 (common OCR/generation error)
        fixed_code = re.sub(r'\bcv20\b', 'cv2', fixed_code)
        
        # Fix 2: Remove bash commands mixed in Python code
        fixed_code = re.sub(r'echo\s+"[^"]*"\s*>>\s*[^\n]*\.txt', '# Removed bash echo command', fixed_code)
        
        # Fix 3: Fix Windows paths in Python strings
        fixed_code = re.sub(r"'([A-Z]):\\([^']*)'", r"r'\1:\\\2'", fixed_code)
        fixed_code = re.sub(r'"([A-Z]):\\([^"]*)"', r'r"\1:\\\2"', fixed_code)
        
        # Fix 4: Add missing imports for common libraries
        if 'cv2.' in fixed_code and 'import cv2' not in fixed_code:
            fixed_code = 'import cv2\n' + fixed_code
        
        if 'np.' in fixed_code and 'import numpy' not in fixed_code:
            fixed_code = 'import numpy as np\n' + fixed_code
        
        if 'plt.' in fixed_code and 'import matplotlib' not in fixed_code:
            fixed_code = 'import matplotlib.pyplot as plt\n' + fixed_code
        
        # Fix 5: Remove invalid function calls
        fixed_code = re.sub(r'touch\s+[^\n]*\n', '', fixed_code)
        fixed_code = re.sub(r'cat\s+<<.*?EOT[^;]*;', '', fixed_code, flags=re.DOTALL)
        
        # Fix 6: Ensure proper indentation
        fixed_code = self._fix_indentation(fixed_code)
        
        return fixed_code
    
    def _fix_indentation(self, code: str) -> str:
        """Fix basic indentation issues"""
        lines = code.split('\n')
        fixed_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                fixed_lines.append('')
                continue
            
            # Adjust indent level based on keywords
            if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except', 'with ')):
                fixed_lines.append('    ' * indent_level + stripped)
                if stripped.endswith(':'):
                    indent_level += 1
            elif stripped.startswith(('else:', 'elif ', 'except:', 'finally:')):
                if indent_level > 0:
                    indent_level -= 1
                fixed_lines.append('    ' * indent_level + stripped)
                indent_level += 1
            elif stripped in ['pass', 'break', 'continue'] or not stripped.endswith(':'):
                if stripped.startswith(('return ', 'yield ', 'raise ')):
                    fixed_lines.append('    ' * indent_level + stripped)
                    if indent_level > 0:
                        indent_level -= 1
                else:
                    fixed_lines.append('    ' * indent_level + stripped)
            else:
                fixed_lines.append('    ' * indent_level + stripped)
        
        return '\n'.join(fixed_lines)
    
    def _attempt_syntax_fix(self, code: str, error: SyntaxError) -> str:
        """Attempt to fix specific syntax errors"""
        lines = code.split('\n')
        
        if error.lineno and error.lineno <= len(lines):
            line_idx = error.lineno - 1
            problematic_line = lines[line_idx]
            
            # Common fixes
            fixed_line = problematic_line
            
            # Fix missing colons
            if 'expected \':\'' in str(error):
                if re.match(r'^\s*(if|for|while|def|class|try|except|with|else|elif)', problematic_line):
                    if not problematic_line.rstrip().endswith(':'):
                        fixed_line = problematic_line.rstrip() + ':'
            
            # Fix unmatched parentheses
            elif 'unmatched' in str(error) or 'unexpected EOF' in str(error):
                open_parens = problematic_line.count('(') - problematic_line.count(')')
                if open_parens > 0:
                    fixed_line = problematic_line + ')' * open_parens
            
            if fixed_line != problematic_line:
                lines[line_idx] = fixed_line
                return '\n'.join(lines)
        
        return code
    
    def _check_code_quality(self, code: str) -> List[str]:
        """Check for code quality issues"""
        issues = []
        
        # Check for undefined variables (basic check)
        imports = set()
        defined_vars = set()
        
        for line in code.split('\n'):
            line = line.strip()
            
            # Track imports
            if line.startswith(('import ', 'from ')):
                match = re.search(r'import\s+(\w+)', line)
                if match:
                    imports.add(match.group(1))
            
            # Track variable definitions
            if '=' in line and not line.startswith('#'):
                var_match = re.match(r'^(\w+)\s*=', line)
                if var_match:
                    defined_vars.add(var_match.group(1))
        
        # Check for common undefined variables
        common_undefined = []
        if 'cv2' in code and 'cv2' not in imports:
            common_undefined.append('cv2')
        if 'np.' in code and 'np' not in imports:
            common_undefined.append('numpy as np')
        
        if common_undefined:
            issues.append(f"Missing imports: {', '.join(common_undefined)}")
        
        return issues

class EnhancedCodeGenerator:
    """Enhanced code generator with quality control"""
    
    def __init__(self):
        self.validator = CodeQualityValidator()
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def extract_and_validate_code(self, llm_response: str, task_context: str = "") -> Dict[str, any]:
        """
        Extract code from LLM response and validate it
        
        Returns:
            {
                'code': str,
                'is_valid': bool,
                'issues': List[str],
                'filename': str,
                'language': str
            }
        """
        # Extract code blocks
        code_blocks = self._extract_code_blocks(llm_response)
        
        if not code_blocks:
            self.logger.warning("⚠️ No code blocks found in response")
            return {
                'code': '',
                'is_valid': False,
                'issues': ['No code blocks found'],
                'filename': 'unknown.txt',
                'language': 'unknown'
            }
        
        # Select best code block
        best_block = self._select_best_code_block(code_blocks, task_context)
        
        # Validate and fix code
        if best_block['language'] == 'python':
            is_valid, issues, corrected_code = self.validator.validate_python_code(best_block['code'])
            best_block['code'] = corrected_code
            best_block['is_valid'] = is_valid
            best_block['issues'] = issues
        else:
            best_block['is_valid'] = True
            best_block['issues'] = []
        
        # Determine filename
        best_block['filename'] = self._determine_filename(task_context, best_block['language'])
        
        return best_block
    
    def _extract_code_blocks(self, response: str) -> List[Dict[str, str]]:
        """Extract code blocks from LLM response"""
        code_blocks = []
        
        # Pattern 1: ```language blocks
        language_pattern = r'```(\w+)?\s*\n(.*?)\n```'
        matches = re.findall(language_pattern, response, re.DOTALL | re.IGNORECASE)
        
        for language, code in matches:
            language = language.lower() if language else 'unknown'
            if language in ['', 'text', 'txt']:
                language = 'unknown'
            
            code_blocks.append({
                'language': language,
                'code': code.strip(),
                'extraction_method': 'markdown_block'
            })
        
        # Pattern 2: Python code detection (if no markdown blocks found)
        if not code_blocks:
            python_indicators = ['import ', 'def ', 'class ', 'if __name__', 'from ']
            lines = response.split('\n')
            
            code_lines = []
            in_code = False
            
            for line in lines:
                stripped = line.strip()
                if any(line.startswith(indicator) for indicator in python_indicators):
                    in_code = True
                
                if in_code:
                    code_lines.append(line)
                    
                    # Stop if we hit obvious non-code
                    if stripped and not any(c in stripped for c in '()[]{}#=') and len(stripped.split()) > 5:
                        if not any(keyword in stripped.lower() for keyword in ['def', 'class', 'import', 'if', 'for', 'while', 'try', 'print', 'return']):
                            break
            
            if code_lines:
                code_blocks.append({
                    'language': 'python',
                    'code': '\n'.join(code_lines).strip(),
                    'extraction_method': 'pattern_detection'
                })
        
        return code_blocks
    
    def _select_best_code_block(self, code_blocks: List[Dict[str, str]], task_context: str) -> Dict[str, str]:
        """Select the best code block based on context and quality"""
        if not code_blocks:
            return {
                'language': 'unknown',
                'code': '',
                'extraction_method': 'none'
            }
        
        # Score each block
        scored_blocks = []
        task_lower = task_context.lower()
        
        for block in code_blocks:
            score = 0
            code = block['code']
            language = block['language']
            
            # Language preference based on task
            if 'python' in task_lower or 'opencv' in task_lower or 'cv2' in task_lower:
                if language == 'python':
                    score += 50
            
            # Code quality indicators
            if 'import' in code:
                score += 10
            if 'def ' in code:
                score += 10
            if 'class ' in code:
                score += 5
            
            # Length preference (not too short, not too long)
            code_length = len(code.strip())
            if 50 < code_length < 2000:
                score += 20
            elif code_length > 2000:
                score -= 10
            
            # Specific task indicators
            if 'opencv' in task_lower and 'cv2' in code:
                score += 30
            if 'image' in task_lower and any(term in code for term in ['imread', 'imshow', 'imwrite']):
                score += 20
            
            scored_blocks.append((score, block))
        
        # Return highest scoring block
        best_block = max(scored_blocks, key=lambda x: x[0])[1]
        self.logger.info(f"✅ Selected {best_block['language']} code block using {best_block['extraction_method']}")
        
        return best_block
    
    def _determine_filename(self, task_context: str, language: str) -> str:
        """Determine appropriate filename based on task and language"""
        task_lower = task_context.lower()
        
        # Language-specific extensions
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'html': '.html',
            'css': '.css',
            'bash': '.sh',
            'shell': '.sh',
            'sql': '.sql'
        }
        
        ext = extensions.get(language, '.txt')
        
        # Task-specific filenames
        if 'opencv' in task_lower or 'bilderkennungs' in task_lower:
            if 'detect' in task_lower and 'people' in task_lower:
                return f'detect_people{ext}'
            elif 'image' in task_lower or 'recognition' in task_lower:
                return f'image_recognition{ext}'
        
        if 'flask' in task_lower or 'web' in task_lower:
            return f'app{ext}'
        
        if 'test' in task_lower:
            return f'test_script{ext}'
        
        if 'analysis' in task_lower or 'analyze' in task_lower:
            return f'data_analysis{ext}'
        
        # Default naming
        return f'generated_code{ext}'
    
    def generate_complete_opencv_example(self, dataset_path: str = "/mnt/d/Datasets/Rescue/kaggle/PART_1/PART_1/") -> str:
        """Generate a complete, working OpenCV example for the specific use case"""
        code = f'''#!/usr/bin/env python3
"""
OpenCV Human Detection System for Drone Imagery
Detects people in water from drone perspective images
"""

import cv2
import numpy as np
import os
import glob
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DroneImageProcessor:
    """Process drone images to detect people in water"""
    
    def __init__(self, dataset_path="{dataset_path}"):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path("detection_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize HOG descriptor for human detection
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Create background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        logger.info(f"Initialized processor with dataset: {{self.dataset_path}}")
    
    def load_images(self):
        """Load all images from dataset directory"""
        if not self.dataset_path.exists():
            logger.error(f"Dataset path does not exist: {{self.dataset_path}}")
            return []
        
        # Support multiple image formats
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
        images = []
        
        for ext in image_extensions:
            pattern = str(self.dataset_path / "**" / ext)
            found_images = glob.glob(pattern, recursive=True)
            images.extend(found_images)
        
        logger.info(f"Found {{len(images)}} images in dataset")
        return images
    
    def preprocess_image(self, image):
        """Preprocess image for better detection in water environment"""
        # Apply Gaussian blur to reduce noise from water reflections
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        
        # Enhance contrast for better detection underwater
        lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels and convert back to BGR
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def detect_humans(self, image):
        """Detect humans in the image using HOG descriptor"""
        # Preprocess image
        processed = self.preprocess_image(image)
        
        # Detect people using HOG
        boxes, weights = self.hog.detectMultiScale(
            processed,
            winStride=(8, 8),
            padding=(32, 32),
            scale=1.05,
            useMeanshiftGrouping=False
        )
        
        # Filter detections by confidence
        detections = []
        for i, (x, y, w, h) in enumerate(boxes):
            if weights[i] > 0.5:  # Confidence threshold
                detections.append({{
                    'bbox': (x, y, w, h),
                    'confidence': weights[i]
                }})
        
        return detections
    
    def draw_detections(self, image, detections):
        """Draw bounding boxes around detected humans"""
        result = image.copy()
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            confidence = detection['confidence']
            
            # Draw bounding box
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Add confidence label
            label = f"Person: {{confidence:.2f}}"
            cv2.putText(result, label, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return result
    
    def process_single_image(self, image_path):
        """Process a single image and return results"""
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                logger.warning(f"Could not load image: {{image_path}}")
                return None
            
            # Detect humans
            detections = self.detect_humans(image)
            
            # Create result image with annotations
            result_image = self.draw_detections(image, detections)
            
            return {{
                'image_path': image_path,
                'detections': detections,
                'result_image': result_image,
                'human_count': len(detections)
            }}
            
        except Exception as e:
            logger.error(f"Error processing {{image_path}}: {{e}}")
            return None
    
    def process_dataset(self):
        """Process entire dataset and save results"""
        images = self.load_images()
        results = []
        
        logger.info("Starting batch processing...")
        
        for i, image_path in enumerate(images):
            logger.info(f"Processing {{i+1}}/{{len(images)}}: {{Path(image_path).name}}")
            
            result = self.process_single_image(image_path)
            if result:
                results.append(result)
                
                # Save result image if humans detected
                if result['human_count'] > 0:
                    output_filename = f"detected_{{Path(image_path).stem}}.jpg"
                    output_path = self.output_dir / output_filename
                    cv2.imwrite(str(output_path), result['result_image'])
                    logger.info(f"✅ Detected {{result['human_count']}} people - saved to {{output_path}}")
        
        # Generate summary report
        self.generate_report(results)
        
        return results
    
    def generate_report(self, results):
        """Generate summary report of detection results"""
        total_images = len(results)
        images_with_humans = sum(1 for r in results if r['human_count'] > 0)
        total_detections = sum(r['human_count'] for r in results)
        
        report = f"""
=== DRONE IMAGE HUMAN DETECTION REPORT ===
Total Images Processed: {{total_images}}
Images with Human Detections: {{images_with_humans}}
Total Human Detections: {{total_detections}}
Detection Rate: {{images_with_humans/total_images*100:.1f}}%

Top Detections:
"""
        
        # Sort by detection count
        sorted_results = sorted(results, key=lambda x: x['human_count'], reverse=True)
        
        for result in sorted_results[:10]:  # Top 10
            if result['human_count'] > 0:
                report += f"- {{Path(result['image_path']).name}}: {{result['human_count']}} people\\n"
        
        # Save report
        report_path = self.output_dir / "detection_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"📊 Report saved to {{report_path}}")
        print(report)

def main():
    """Main execution function"""
    logger.info("🚁 Starting Drone Image Human Detection System")
    
    # Initialize processor
    processor = DroneImageProcessor()
    
    # Process dataset
    results = processor.process_dataset()
    
    logger.info(f"✅ Processing complete. {{len(results)}} images processed.")
    logger.info(f"Results saved to {{processor.output_dir}}")

if __name__ == "__main__":
    main()
'''
        
        return code

def create_code_generator() -> EnhancedCodeGenerator:
    """Create enhanced code generator instance"""
    return EnhancedCodeGenerator()

if __name__ == '__main__':
    # Test the enhanced code generator
    print("🧪 Testing Enhanced Code Generator...")
    
    generator = EnhancedCodeGenerator()
    
    # Test with problematic code from the log
    test_response = '''Here's a Python script for image recognition:

```python
import cv2
from os import listdir
from os import chdir
chdir('D:/Datasets/Rescue/kaggle/PART_1')
for img in listdir():
    if not img.startswith('.'):
        image = cv2.imread(img)
        processed_image = cv20.GaussianBlur(image, (5, 5), 0)  # Typo here
        # More code...
        echo "Processing complete" >> log.txt
```
'''
    
    result = generator.extract_and_validate_code(test_response, "opencv image recognition task")
    
    print(f"✅ Code extracted and validated:")
    print(f"Language: {result['language']}")
    print(f"Valid: {result['is_valid']}")
    print(f"Issues: {result['issues']}")
    print(f"Filename: {result['filename']}")
    print(f"Code length: {len(result['code'])} characters")
    
    # Generate complete OpenCV example
    complete_example = generator.generate_complete_opencv_example()
    print(f"\\n📝 Generated complete OpenCV example ({len(complete_example)} characters)")
    
    print("\\n✅ Code generator test completed")