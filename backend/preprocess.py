from typing import List, Tuple
import re

from transformers import AutoTokenizer

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL_NAME)
# Set a reasonable max length to avoid warnings
tokenizer.model_max_length = 512


def clean_text(text: str) -> str:
    """Basic cleaning to normalize whitespace and remove duplicates/noise."""
    if not text:
        return ""
    # Normalize newlines and spaces
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove boilerplate-like lines (very short nav crumbs, etc.)
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not re.fullmatch(r"[\-|•›»←→/]{1,3}", ln)]
    # Deduplicate consecutive identical lines
    deduped = []
    for ln in lines:
        if not deduped or deduped[-1] != ln:
            deduped.append(ln)
    return "\n".join(deduped).strip()


def _count_tokens(text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks of approximately `chunk_size` tokens with overlap.
    """
    if not text:
        return []
    
    # For very long texts, split into smaller pieces first to avoid tokenization warnings
    max_chars_per_piece = 2000  # Approximately 500 tokens worth of characters
    if len(text) > max_chars_per_piece:
        # Split text into manageable pieces and process each
        pieces = []
        for i in range(0, len(text), max_chars_per_piece):
            piece = text[i:i + max_chars_per_piece]
            pieces.append(piece)
        
        all_chunks = []
        for piece in pieces:
            piece_chunks = _chunk_text_piece(piece, chunk_size, chunk_overlap)
            all_chunks.extend(piece_chunks)
        return all_chunks
    else:
        return _chunk_text_piece(text, chunk_size, chunk_overlap)


def _chunk_text_piece(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Chunk a single piece of text that fits within tokenizer limits."""
    try:
        tokens = tokenizer.encode(text, add_special_tokens=False, truncation=True)
    except Exception as e:
        print(f"Warning: Tokenization failed, falling back to character-based chunking: {e}")
        # Fallback to character-based chunking
        return _fallback_chunk_text(text, chunk_size * 4)  # Rough approximation: 4 chars per token
    
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
            if chunk_text:
                chunks.append(chunk_text)
        except Exception as e:
            print(f"Warning: Failed to decode tokens, skipping chunk: {e}")
            
        if end == n:
            break
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks


def _fallback_chunk_text(text: str, chunk_size: int) -> List[str]:
    """Fallback character-based chunking when tokenization fails."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks
