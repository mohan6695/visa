import hashlib
import time
import re
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentWatermarker:
    """Utility for watermarking and verifying content"""
    
    @staticmethod
    def generate_watermark(
        content: str,
        author_id: str,
        post_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate watermark for content
        
        Args:
            content: The content to watermark
            author_id: Author ID
            post_id: Optional post ID
            
        Returns:
            Dict: Watermark data
        """
        try:
            # Generate timestamp
            timestamp = int(time.time())
            timestamp_iso = datetime.utcnow().isoformat()
            
            # Generate content hash
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Generate author hash
            author_hash = hashlib.md5(author_id.encode()).hexdigest()[:8]
            
            # Generate watermark hash
            watermark_input = f"{content}{author_id}{timestamp_iso}"
            if post_id:
                watermark_input += post_id
            
            watermark_hash = hashlib.md5(watermark_input.encode()).hexdigest()
            
            # Generate display watermark
            display_watermark = f"POST-{content_hash[:6]}-{author_hash[:6]}-{timestamp}"
            
            return {
                "watermark_hash": watermark_hash,
                "display_watermark": display_watermark,
                "content_hash": content_hash,
                "author_hash": author_hash,
                "timestamp": timestamp_iso
            }
        except Exception as e:
            logger.error(f"Error generating watermark: {e}")
            return {
                "watermark_hash": "error",
                "display_watermark": "ERROR",
                "content_hash": "error",
                "author_hash": "error",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def verify_watermark(
        content: str,
        author_id: str,
        watermark_hash: str,
        timestamp: str,
        post_id: Optional[str] = None
    ) -> bool:
        """
        Verify content watermark
        
        Args:
            content: The content to verify
            author_id: Author ID
            watermark_hash: Watermark hash to verify against
            timestamp: Timestamp of the watermark
            post_id: Optional post ID
            
        Returns:
            bool: True if watermark is valid
        """
        try:
            # Generate watermark input
            watermark_input = f"{content}{author_id}{timestamp}"
            if post_id:
                watermark_input += post_id
            
            # Generate hash
            generated_hash = hashlib.md5(watermark_input.encode()).hexdigest()
            
            # Compare hashes
            return generated_hash == watermark_hash
        except Exception as e:
            logger.error(f"Error verifying watermark: {e}")
            return False
    
    @staticmethod
    def extract_watermark(text: str) -> Optional[str]:
        """
        Extract watermark from text
        
        Args:
            text: Text to extract watermark from
            
        Returns:
            Optional[str]: Extracted watermark or None
        """
        try:
            # Look for watermark pattern
            pattern = r"POST-([a-f0-9]{6})-([a-f0-9]{6})-(\d+)"
            match = re.search(pattern, text)
            
            if match:
                return match.group(0)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting watermark: {e}")
            return None
    
    @staticmethod
    def parse_watermark(watermark: str) -> Optional[Dict[str, Any]]:
        """
        Parse watermark into components
        
        Args:
            watermark: Watermark to parse
            
        Returns:
            Optional[Dict]: Parsed watermark or None
        """
        try:
            # Parse watermark pattern
            pattern = r"POST-([a-f0-9]{6})-([a-f0-9]{6})-(\d+)"
            match = re.match(pattern, watermark)
            
            if not match:
                return None
            
            content_hash = match.group(1)
            author_hash = match.group(2)
            timestamp = int(match.group(3))
            
            return {
                "content_hash": content_hash,
                "author_hash": author_hash,
                "timestamp": timestamp,
                "timestamp_iso": datetime.fromtimestamp(timestamp).isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing watermark: {e}")
            return None
    
    @staticmethod
    def add_invisible_watermark(content: str, watermark: str) -> str:
        """
        Add invisible watermark to content using zero-width characters
        
        Args:
            content: Content to watermark
            watermark: Watermark to add
            
        Returns:
            str: Content with invisible watermark
        """
        try:
            # Convert watermark to binary
            binary_watermark = ''.join(format(ord(c), '08b') for c in watermark)
            
            # Zero-width characters
            zwc = {
                '0': '\u200b',  # Zero-width space
                '1': '\u200c'   # Zero-width non-joiner
            }
            
            # Convert binary to zero-width characters
            invisible_watermark = ''.join(zwc[bit] for bit in binary_watermark)
            
            # Add to end of content
            return content + invisible_watermark
        except Exception as e:
            logger.error(f"Error adding invisible watermark: {e}")
            return content
    
    @staticmethod
    def extract_invisible_watermark(content: str) -> Optional[str]:
        """
        Extract invisible watermark from content
        
        Args:
            content: Content with invisible watermark
            
        Returns:
            Optional[str]: Extracted watermark or None
        """
        try:
            # Find zero-width characters
            zwc_pattern = r'[\u200b\u200c]+'
            match = re.search(zwc_pattern, content)
            
            if not match:
                return None
            
            # Extract zero-width characters
            zwc_sequence = match.group(0)
            
            # Convert to binary
            binary = ''
            for char in zwc_sequence:
                if char == '\u200b':
                    binary += '0'
                elif char == '\u200c':
                    binary += '1'
            
            # Convert binary to text
            watermark = ''
            for i in range(0, len(binary), 8):
                byte = binary[i:i+8]
                if len(byte) == 8:
                    watermark += chr(int(byte, 2))
            
            return watermark
        except Exception as e:
            logger.error(f"Error extracting invisible watermark: {e}")
            return None
    
    @staticmethod
    def check_content_similarity(content1: str, content2: str) -> float:
        """
        Check similarity between two content pieces
        
        Args:
            content1: First content
            content2: Second content
            
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Simple Jaccard similarity
            words1 = set(re.findall(r'\w+', content1.lower()))
            words2 = set(re.findall(r'\w+', content2.lower()))
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            if union == 0:
                return 0.0
            
            return intersection / union
        except Exception as e:
            logger.error(f"Error checking content similarity: {e}")
            return 0.0
    
    @staticmethod
    def detect_copied_content(
        content: str,
        original_content: str,
        threshold: float = 0.8
    ) -> Tuple[bool, float]:
        """
        Detect if content is copied from original
        
        Args:
            content: Content to check
            original_content: Original content
            threshold: Similarity threshold
            
        Returns:
            Tuple[bool, float]: (is_copied, similarity_score)
        """
        try:
            # Check similarity
            similarity = ContentWatermarker.check_content_similarity(content, original_content)
            
            return similarity >= threshold, similarity
        except Exception as e:
            logger.error(f"Error detecting copied content: {e}")
            return False, 0.0