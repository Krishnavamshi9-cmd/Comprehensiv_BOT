# Model Switching Implementation Guide

## Overview
This implementation automatically switches between two LLM models based on token count to prevent "Request too large" errors.

## Models Configuration

### Primary Model: `openai/gpt-oss-120b`
- **Token Limit**: 8,000 TPM
- **Characteristics**: High intelligence, better quality responses
- **Use Case**: Standard requests with smaller context

### Fallback Model: `meta-llama/llama-4-scout-17b-16e-instruct`
- **Token Limit**: 30,000 TPM
- **Characteristics**: Instruction-tuned, 17B parameters
- **Use Case**: Large context requests exceeding 8k tokens
- **Note**: Less intelligent than gpt-oss-120b, but optimized for following instructions

## How It Works

### 1. Token Estimation
```python
def _count_tokens(text: str) -> int:
    """Conservative estimate: 1 token ≈ 3.5 characters"""
    return len(text) // 3
```

### 2. Model Selection Logic
- **Threshold for Primary**: 6,000 tokens (conservative limit)
- **Threshold for Fallback**: 25,000 tokens (conservative limit)
- If context exceeds both limits, it gets automatically truncated

### 3. Prompt Optimization

#### Standard Prompt (for gpt-oss-120b)
- Comprehensive instructions
- Open-ended extraction strategy
- Relies on model intelligence

#### Instruct-Tuned Prompt (for llama-4-scout-17b-16e-instruct)
- **Step-by-step instructions**
- **Clear task breakdown** (STEP 1, STEP 2, etc.)
- **Explicit formatting examples**
- **Bullet-point rules**
- More directive language for better instruction-following

Example:
```
TASK: Extract golden question-answer pairs for chatbot testing.

STEP 1 - READ THE CONTEXT:
[context here]

STEP 2 - UNDERSTAND THE REQUIREMENT:
[query here]

STEP 3 - EXTRACT QUESTIONS:
• Product/service info questions
• Feature and how-to questions
...
```

## Benefits

1. **No More Token Limit Errors**: Automatic fallback prevents 413 errors
2. **Cost Optimization**: Uses smarter model when possible
3. **Better UX**: Users don't see errors, just results
4. **Quality Optimization**: Each model gets optimized prompts
5. **Transparent Logging**: Clear logs showing which model is used

## Logging

The system logs the following:
- Which model is being used
- Estimated token count
- Success/failure messages
- Reason for model selection

Example logs:
```
INFO: Using PRIMARY model (openai/gpt-oss-120b): ~4523 tokens
INFO: Using FALLBACK model (meta-llama/llama-4-scout-17b-16e-instruct): ~18432 tokens (exceeded primary limit)
SUCCESS: Successfully extracted 145 Q&A pairs using meta-llama/llama-4-scout-17b-16e-instruct
```

## Testing

### Test Case 1: Small Context (should use primary model)
```python
from generator import generate_qa

context_chunks = ["Short content about a product."]
query = "Extract Q&A pairs"
result = generate_qa(context_chunks, query)
# Should use: openai/gpt-oss-120b
```

### Test Case 2: Large Context (should use fallback model)
```python
from generator import generate_qa

# Large scraped content from stealth_scraper
context_chunks = [very_large_content]  # >8k tokens
query = "Extract Q&A pairs"
result = generate_qa(context_chunks, query)
# Should use: meta-llama/llama-4-scout-17b-16e-instruct
```

### Test Case 3: Manual Model Override
```python
result = generate_qa(context_chunks, query, model="llama-3.1-70b-versatile")
# Will use specified model regardless of token count
```

## Configuration

You can adjust the token limits in `generator.py`:

```python
TOKEN_LIMIT_PRIMARY = 6000   # Adjust for primary model
TOKEN_LIMIT_FALLBACK = 25000 # Adjust for fallback model
```

## Error Handling

1. **Token Limit Exceeded**: Automatically switches to fallback model
2. **Fallback Limit Exceeded**: Truncates context to fit
3. **JSON Parsing Fails**: Falls back to plain text extraction
4. **All Strategies Fail**: Raises `GenerationError` with details

## Integration with Stealth Scraper

When using stealth scraper, large scraped content is automatically handled:

```python
from stealth_scraper import StealthScraper
from generator import generate_qa

scraper = StealthScraper()
content = scraper.scrape_url("https://example.com")  # Large content
result = generate_qa([content], query)
# Automatically uses appropriate model based on content size
```

## Monitoring

Check the logs to see:
- Model usage patterns
- Token count trends
- Success rates per model
- Performance metrics

## Future Improvements

1. Add tiktoken for accurate token counting
2. Implement caching for repeated contexts
3. Add metrics tracking for model performance
4. Consider chunking strategy for very large contexts
5. Add rate limiting awareness
