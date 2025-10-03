"""
Enhanced preprocessing with aggressive content recovery and quality improvement.
Handles edge cases, poor quality content, and maximizes information extraction.
"""

import re
import unicodedata
from typing import List, Tuple, Dict
from collections import Counter

from transformers import AutoTokenizer

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

try:
    tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL_NAME)
    tokenizer.model_max_length = 512
except Exception as e:
    print(f"Warning: Could not load tokenizer: {e}")
    tokenizer = None


class ContentQualityAnalyzer:
    """Analyzes and improves content quality."""
    
    def __init__(self):
        self.noise_patterns = [
            # Navigation and UI elements
            r'(?i)home\s*>\s*products?\s*>\s*',
            r'(?i)breadcrumb|navigation|menu|navbar',
            r'(?i)skip\s+to\s+(?:main\s+)?content',
            r'(?i)back\s+to\s+top',
            
            # Social and sharing
            r'(?i)share\s+(?:on\s+)?(?:facebook|twitter|linkedin|instagram)',
            r'(?i)follow\s+us\s+on',
            r'(?i)like\s+us\s+on\s+facebook',
            
            # Legal and footer content
            r'(?i)copyright\s+©?\s*\d{4}',
            r'(?i)all\s+rights\s+reserved',
            r'(?i)terms\s+(?:of\s+(?:use|service)|and\s+conditions)',
            r'(?i)privacy\s+policy',
            
            # Cookie and consent
            r'(?i)this\s+(?:website|site)\s+uses\s+cookies',
            r'(?i)accept\s+(?:all\s+)?cookies',
            r'(?i)cookie\s+(?:policy|settings|preferences)',
            
            # Subscription and marketing
            r'(?i)subscribe\s+to\s+(?:our\s+)?newsletter',
            r'(?i)sign\s+up\s+for\s+(?:our\s+)?(?:newsletter|updates)',
            r'(?i)get\s+(?:the\s+)?latest\s+(?:news|updates)',
            
            # Timestamps and metadata
            r'(?i)(?:last\s+)?updated?\s*:?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'(?i)published\s*:?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'(?i)\d+\s+(?:minute|hour|day|week|month|year)s?\s+ago',
            
            # Print and sharing actions
            r'(?i)print\s+(?:this\s+)?page',
            r'(?i)email\s+(?:this\s+)?(?:page|article)',
            r'(?i)share\s+(?:this\s+)?(?:page|article)',
        ]
        
        self.compiled_patterns = [re.compile(pattern) for pattern in self.noise_patterns]
    
    def remove_noise(self, text: str) -> str:
        """Remove common noise patterns from text."""
        for pattern in self.compiled_patterns:
            text = pattern.sub('', text)
        return text
    
    def analyze_content_quality(self, text: str) -> Dict[str, any]:
        """Analyze content quality metrics."""
        if not text:
            return {"quality_score": 0, "issues": ["Empty content"]}
        
        lines = text.strip().split('\n')
        words = text.split()
        
        # Basic metrics
        char_count = len(text)
        word_count = len(words)
        line_count = len([l for l in lines if l.strip()])
        
        # Quality indicators
        unique_words = len(set(word.lower() for word in words if word.isalpha()))
        avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
        
        # Repetition analysis
        word_freq = Counter(word.lower() for word in words if word.isalpha())
        most_common_freq = word_freq.most_common(1)[0][1] if word_freq else 0
        repetition_ratio = most_common_freq / max(word_count, 1)
        
        # Calculate quality score (0-100)
        quality_score = 0
        issues = []
        
        # Length checks
        if char_count < 100:
            issues.append("Content too short")
        elif char_count > 500:
            quality_score += 20
        
        # Word diversity
        if word_count > 0:
            diversity_ratio = unique_words / word_count
            if diversity_ratio > 0.5:
                quality_score += 30
            elif diversity_ratio < 0.3:
                issues.append("Low word diversity")
        
        # Repetition check
        if repetition_ratio > 0.3:
            issues.append("High repetition detected")
        else:
            quality_score += 25
        
        # Structure check
        if line_count > 5:
            quality_score += 15
        
        # Average word length (indicates meaningful content)
        if 3 < avg_word_length < 8:
            quality_score += 10
        
        return {
            "quality_score": min(quality_score, 100),
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "unique_words": unique_words,
            "repetition_ratio": repetition_ratio,
            "issues": issues
        }


def aggressive_clean_text(text: str) -> str:
    """Aggressively clean and normalize text while preserving structure."""
    if not text:
        return ""
    
    analyzer = ContentQualityAnalyzer()
    
    # Step 1: Unicode normalization
    text = unicodedata.normalize('NFKD', text)
    
    # Step 2: Remove noise patterns
    text = analyzer.remove_noise(text)
    
    # Step 3: Normalize whitespace and line breaks
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 consecutive newlines
    text = re.sub(r'[ \t]{3,}', '  ', text)   # Max 2 consecutive spaces
    
    # Step 4: Clean up common formatting issues
    # Fix broken words (e.g., "hel lo" -> "hello")
    text = re.sub(r'\b(\w)\s+(\w)\b', r'\1\2', text)
    
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.!?,:;])', r'\1', text)
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
    
    # Step 5: Process lines individually
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            cleaned_lines.append('')
            continue
        
        # Skip lines that are likely noise
        if _is_noise_line(line):
            continue
        
        # Clean individual line
        line = _clean_line(line)
        
        if line and len(line) > 2:  # Keep non-empty, meaningful lines
            cleaned_lines.append(line)
    
    # Step 6: Remove excessive empty lines and duplicates
    final_lines = []
    prev_line = None
    empty_count = 0
    
    for line in cleaned_lines:
        if not line.strip():
            empty_count += 1
            if empty_count <= 2:  # Allow max 2 consecutive empty lines
                final_lines.append(line)
        else:
            empty_count = 0
            # Skip exact duplicates
            if line != prev_line:
                final_lines.append(line)
                prev_line = line
    
    result = '\n'.join(final_lines).strip()
    
    # Step 7: Final quality check and enhancement
    quality = analyzer.analyze_content_quality(result)
    if quality["quality_score"] < 30:
        print(f"⚠ Low quality content detected (score: {quality['quality_score']})")
        print(f"  Issues: {', '.join(quality['issues'])}")
        # Try to salvage what we can
        result = _salvage_low_quality_content(result)
    
    return result


def _is_noise_line(line: str) -> bool:
    """Check if a line is likely noise."""
    line_lower = line.lower().strip()
    
    # Empty or very short lines
    if len(line_lower) < 3:
        return True
    
    # Lines with only symbols/numbers
    if re.match(r'^[\W\d\s]*$', line_lower):
        return True
    
    # Common noise patterns
    noise_indicators = [
        'javascript', 'cookie', 'gdpr', 'accept all',
        'skip to', 'back to top', 'print page',
        'share on', 'follow us', 'subscribe',
        'copyright', 'all rights reserved',
        'terms of use', 'privacy policy'
    ]
    
    for indicator in noise_indicators:
        if indicator in line_lower:
            return True
    
    # Lines with excessive repetition of characters
    if len(set(line_lower)) / len(line_lower) < 0.3 and len(line_lower) > 10:
        return True
    
    return False


def _clean_line(line: str) -> str:
    """Clean individual line."""
    # Remove excessive punctuation
    line = re.sub(r'[.]{3,}', '...', line)
    line = re.sub(r'[!]{2,}', '!', line)
    line = re.sub(r'[?]{2,}', '?', line)
    
    # Fix spacing
    line = re.sub(r'\s+', ' ', line)
    
    # Remove leading/trailing punctuation noise
    line = re.sub(r'^[^\w\s]*', '', line)
    line = re.sub(r'[^\w\s.!?]*$', '', line)
    
    return line.strip()


def _salvage_low_quality_content(text: str) -> str:
    """Try to salvage useful information from low quality content."""
    lines = text.split('\n')
    
    # Look for lines that might contain useful information
    useful_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Keep lines that look like questions or answers
        if (re.search(r'\b(?:what|how|why|when|where|who|can|is|are|do|does|will)\b', line, re.I) or
            re.search(r'\?', line) or
            len(line.split()) > 5):  # Lines with more than 5 words
            useful_lines.append(line)
    
    return '\n'.join(useful_lines)


def enhanced_chunk_text(text: str, 
                       chunk_size: int = 800, 
                       chunk_overlap: int = 100,
                       min_chunk_size: int = 50,
                       preserve_structure: bool = True) -> List[str]:
    """
    Enhanced chunking with structure preservation and quality optimization.
    """
    if not text:
        return []
    
    # Analyze content quality first
    analyzer = ContentQualityAnalyzer()
    quality = analyzer.analyze_content_quality(text)
    
    print(f"📊 Content quality score: {quality['quality_score']}/100")
    if quality['issues']:
        print(f"⚠ Quality issues: {', '.join(quality['issues'])}")
    
    # Adjust chunking strategy based on content quality
    if quality['quality_score'] < 50:
        # For low quality content, use smaller chunks to avoid noise
        chunk_size = min(chunk_size, 500)
        chunk_overlap = min(chunk_overlap, 50)
    
    # Try structure-aware chunking first
    if preserve_structure:
        structured_chunks = _structure_aware_chunking(text, chunk_size, chunk_overlap)
        if structured_chunks:
            return _validate_and_filter_chunks(structured_chunks, min_chunk_size)
    
    # Fallback to token-based chunking
    if tokenizer:
        try:
            return _enhanced_token_chunking(text, chunk_size, chunk_overlap, min_chunk_size)
        except Exception as e:
            print(f"⚠ Token chunking failed: {e}")
    
    # Final fallback to character-based chunking
    return _character_based_chunking(text, chunk_size * 4, min_chunk_size)


def _structure_aware_chunking(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Chunk text while preserving logical structure."""
    
    # Split by major structural elements
    sections = []
    current_section = []
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Check if this line starts a new section
        if _is_section_boundary(line):
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
        
        if line:  # Only add non-empty lines
            current_section.append(line)
    
    # Add the last section
    if current_section:
        sections.append('\n'.join(current_section))
    
    # Now chunk each section appropriately
    chunks = []
    for section in sections:
        if len(section) <= chunk_size * 4:  # Small section, keep as is
            chunks.append(section)
        else:
            # Large section, need to split further
            section_chunks = _split_large_section(section, chunk_size, chunk_overlap)
            chunks.extend(section_chunks)
    
    return chunks


def _is_section_boundary(line: str) -> bool:
    """Check if a line indicates a section boundary."""
    if not line:
        return False
    
    # Headings
    if re.match(r'^HEADING:', line):
        return True
    
    # Q&A patterns
    if re.match(r'^Q&A:', line):
        return True
    
    # Lines that look like headings (all caps, short, etc.)
    if (len(line) < 100 and 
        (line.isupper() or 
         re.match(r'^\d+\.', line) or
         line.endswith(':'))):
        return True
    
    return False


def _split_large_section(section: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split a large section into smaller chunks."""
    if tokenizer:
        try:
            return _token_chunk_section(section, chunk_size, chunk_overlap)
        except:
            pass
    
    # Fallback to sentence-based splitting
    sentences = re.split(r'[.!?]+', section)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_length = len(sentence)
        
        if current_length + sentence_length > chunk_size * 4 and current_chunk:
            # Start new chunk
            chunks.append('. '.join(current_chunk) + '.')
            
            # Add overlap
            overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
            current_chunk = overlap_sentences + [sentence]
            current_length = sum(len(s) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks


def _enhanced_token_chunking(text: str, chunk_size: int, chunk_overlap: int, min_chunk_size: int) -> List[str]:
    """Enhanced token-based chunking with better handling."""
    
    # Handle very long texts by processing in pieces
    max_chars_per_piece = 3000
    if len(text) > max_chars_per_piece:
        pieces = []
        for i in range(0, len(text), max_chars_per_piece):
            piece = text[i:i + max_chars_per_piece]
            pieces.append(piece)
        
        all_chunks = []
        for piece in pieces:
            try:
                piece_chunks = _token_chunk_piece(piece, chunk_size, chunk_overlap)
                all_chunks.extend(piece_chunks)
            except Exception as e:
                print(f"⚠ Failed to chunk piece: {e}")
                # Fallback for this piece
                fallback_chunks = _character_based_chunking(piece, chunk_size * 4, min_chunk_size)
                all_chunks.extend(fallback_chunks)
        
        return _validate_and_filter_chunks(all_chunks, min_chunk_size)
    else:
        return _token_chunk_piece(text, chunk_size, chunk_overlap)


def _token_chunk_piece(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Chunk a single piece using tokenizer."""
    try:
        tokens = tokenizer.encode(text, add_special_tokens=False, truncation=True)
    except Exception as e:
        print(f"⚠ Tokenization failed: {e}")
        return _character_based_chunking(text, chunk_size * 4, 50)
    
    if not tokens:
        return []
    
    chunks = []
    start = 0
    n = len(tokens)
    
    while start < n:
        end = min(start + chunk_size, n)
        chunk_tokens = tokens[start:end]
        
        try:
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunk_text = chunk_text.strip()
            if chunk_text and len(chunk_text) > 10:
                chunks.append(chunk_text)
        except Exception as e:
            print(f"⚠ Failed to decode chunk: {e}")
        
        if end == n:
            break
        
        start = end - chunk_overlap
        if start < 0:
            start = 0
    
    return chunks


def _character_based_chunking(text: str, chunk_size: int, min_chunk_size: int) -> List[str]:
    """Fallback character-based chunking."""
    chunks = []
    
    # Try to split on sentence boundaries first
    sentences = re.split(r'[.!?]+', text)
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_length = len(sentence)
        
        if current_length + sentence_length > chunk_size and current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            if len(chunk_text) >= min_chunk_size:
                chunks.append(chunk_text)
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
    
    if current_chunk:
        chunk_text = '. '.join(current_chunk) + '.'
        if len(chunk_text) >= min_chunk_size:
            chunks.append(chunk_text)
    
    return chunks


def _validate_and_filter_chunks(chunks: List[str], min_chunk_size: int) -> List[str]:
    """Validate and filter chunks for quality."""
    analyzer = ContentQualityAnalyzer()
    valid_chunks = []
    
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or len(chunk) < min_chunk_size:
            continue
        
        # Basic quality check
        quality = analyzer.analyze_content_quality(chunk)
        if quality['quality_score'] > 20:  # Keep chunks with reasonable quality
            valid_chunks.append(chunk)
        else:
            print(f"⚠ Filtered low quality chunk: {chunk[:100]}...")
    
    return valid_chunks


# Backward compatibility functions
def clean_text(text: str) -> str:
    """Backward compatible clean_text function."""
    return aggressive_clean_text(text)


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[str]:
    """Backward compatible chunk_text function."""
    return enhanced_chunk_text(text, chunk_size, chunk_overlap)


if __name__ == "__main__":
    # Test the enhanced preprocessing
    test_text = """
    Cookie Policy Accept All Cookies
    
    HEADING: Welcome to Our Service
    
    Q&A: How do I get started?
    You can get started by creating an account and following our setup guide.
    
    Q&A: What are the pricing plans?
    We offer three plans: Basic ($10/month), Pro ($25/month), and Enterprise ($100/month).
    
    Some additional information about our service...
    
    Follow us on Facebook Twitter LinkedIn
    Copyright 2024 All Rights Reserved
    """
    
    print("🧪 Testing Enhanced Preprocessing")
    print("=" * 50)
    
    print("📝 Original text:")
    print(repr(test_text))
    
    print("\n🧹 Cleaned text:")
    cleaned = aggressive_clean_text(test_text)
    print(repr(cleaned))
    
    print("\n📦 Chunks:")
    chunks = enhanced_chunk_text(cleaned, chunk_size=200, chunk_overlap=50)
    for i, chunk in enumerate(chunks, 1):
        print(f"{i}. {chunk}")
