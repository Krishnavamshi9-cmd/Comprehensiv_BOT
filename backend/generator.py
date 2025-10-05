import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from groq import Groq
from loguru import logger

load_dotenv()

# Model configurations
DEFAULT_MODEL = "openai/gpt-oss-120b"  # High intelligence model, 8k token limit
FALLBACK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # Higher token capacity (30k), instruct-tuned
TOKEN_LIMIT_PRIMARY = 3500  # Conservative limit for primary model (actual: 8k, leaving room for response)
TOKEN_LIMIT_FALLBACK = 12000  # Conservative limit for fallback model (actual: 30k, leaving room for response)


class GenerationError(Exception):
    pass


def _normalize_question(question: str) -> str:
    """Normalize question for similarity comparison."""
    # Convert to lowercase and remove punctuation
    normalized = re.sub(r'[^\w\s]', '', question.lower())
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    return normalized


def _questions_similar(q1: str, q2: str, threshold: float = 0.8) -> bool:
    """Check if two questions are semantically similar using simple string similarity."""
    norm_q1 = _normalize_question(q1)
    norm_q2 = _normalize_question(q2)
    
    # Simple word overlap similarity
    words1 = set(norm_q1.split())
    words2 = set(norm_q2.split())
    
    if not words1 or not words2:
        return False
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    similarity = intersection / union if union > 0 else 0
    return similarity >= threshold


def _deduplicate_questions(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate and very similar questions, keeping the one with the longer answer."""
    if not items:
        return items
    
    deduplicated = []
    
    for item in items:
        question = item.get("question", "").strip()
        answer = item.get("expected_response", "").strip()
        
        if not question or not answer:
            continue
        
        # Check if this question is similar to any existing one
        is_duplicate = False
        for i, existing in enumerate(deduplicated):
            if _questions_similar(question, existing["question"]):
                # Keep the one with the longer/better answer
                if len(answer) > len(existing["expected_response"]):
                    deduplicated[i] = item
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduplicated.append(item)
    
    return deduplicated


def _count_tokens(text: str) -> int:
    """Estimate the number of tokens in the text.
    Uses an extremely conservative estimate to avoid exceeding limits.
    Assumes 1 token ≈ 2 characters (very conservative, typical is 3-4 chars/token).
    Better to overestimate and truncate than underestimate and fail.
    """
    if not text:
        return 0
    # VERY conservative estimate: 1 token ≈ 2 chars
    # This aggressive estimation prevents token limit errors
    return int(len(text) / 2)


def _build_prompt_standard(context: str, query: str) -> str:
    """Standard prompt for high-intelligence models like gpt-oss-120b."""
    return (
        "You are an exhaustive Golden Question extraction assistant for chatbot testing.\n"
        "Your task is to extract ALL POSSIBLE distinct questions that real users might ask from the provided context.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. Extract the MAXIMUM number of questions possible - DO NOT limit yourself\n"
        "2. NEVER hallucinate answers - use ONLY what is explicitly stated in the context\n"
        "3. Extract questions for ALL website types: e-commerce, banking, education, healthcare, etc.\n"
        "4. Cover every possible user scenario and information need\n\n"
        "GOLDEN QUESTIONS include:\n"
        "- Basic product/service information questions\n"
        "- Feature and functionality questions\n"
        "- Pricing, costs, and billing questions\n"
        "- How-to and step-by-step process questions\n"
        "- Troubleshooting and problem-solving questions\n"
        "- Account and profile management questions\n"
        "- Policy and terms questions\n"
        "- Support and contact questions\n"
        "- Availability and accessibility questions\n"
        "- Comparison and alternative questions\n"
        "- Technical specification questions\n"
        "- Usage limits and restrictions questions\n\n"
        "ANSWER REQUIREMENTS:\n"
        "- Extract answers DIRECTLY from the provided context only\n"
        "- If context doesn't contain a complete answer, extract what's available\n"
        "- Maintain natural, conversational language\n"
        "- Keep answers concise but informative\n"
        "- Never add information not present in the context\n\n"
        f"User Query: {query}\n\n"
        "Return STRICT JSON with a top-level key `items` that is an array of objects.\n"
        "Each object must have the keys:\n"
        "- `\"question\"` → the extracted question in natural language\n"
        "- `\"expected_response\"` → the answer extracted directly from context\n\n"
        "EXTRACTION STRATEGY:\n"
        "- Be EXHAUSTIVE: Extract every possible question from the content\n"
        "- Look for explicit Q&A pairs, FAQ sections, help content\n"
        "- Infer questions from informational statements\n"
        "- Create questions for every feature, process, and detail mentioned\n"
        "- Extract questions at different complexity levels\n"
        "- Do NOT merge similar questions - extract all variations\n\n"
        f"Context:\n{context}"
    )


def _build_prompt_instruct(context: str, query: str) -> str:
    """Optimized instruct-tuned prompt for llama-4-scout-17b-16e-instruct.
    More directive and step-by-step for better performance with smaller models.
    """
    return (
        "TASK: Extract golden question-answer pairs for chatbot testing.\n\n"
        "STEP 1 - READ THE CONTEXT:\n"
        f"Context:\n{context}\n\n"
        "STEP 2 - UNDERSTAND THE REQUIREMENT:\n"
        f"User Query: {query}\n\n"
        "STEP 3 - EXTRACT QUESTIONS:\n"
        "Extract EVERY possible question users might ask. Include:\n"
        "• Product/service info questions\n"
        "• Feature and how-to questions\n"
        "• Pricing and cost questions\n"
        "• Policy and terms questions\n"
        "• Support and contact questions\n"
        "• Technical specification questions\n"
        "• Troubleshooting questions\n\n"
        "STEP 4 - EXTRACT ANSWERS:\n"
        "For each question, extract the answer DIRECTLY from the context.\n"
        "NEVER invent information. Use ONLY what is explicitly stated.\n\n"
        "STEP 5 - FORMAT OUTPUT:\n"
        "Return ONLY valid JSON in this exact format:\n"
        "{\n"
        '  "items": [\n'
        '    {"question": "...", "expected_response": "..."},\n'
        '    {"question": "...", "expected_response": "..."}\n'
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "1. Extract the MAXIMUM number of Q&A pairs\n"
        "2. Each question must be in natural language\n"
        "3. Each answer must come from the context\n"
        "4. Return ONLY the JSON object, no other text\n"
        "5. Ensure valid JSON syntax\n\n"
        "BEGIN EXTRACTION NOW:"
    )


def _safe_json_parse(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Try to locate JSON substring if model wrapped output
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, dict) or "items" not in data or not isinstance(data["items"], list):
        raise GenerationError("Model output missing 'items' list.")
    # Normalize items
    norm_items = []
    for it in data["items"]:
        if not isinstance(it, dict):
            continue
        q = str(it.get("question", "")).strip()
        a = str(it.get("expected_response", "")).strip()
        if q and a:
            norm_items.append({"question": q, "expected_response": a})
    if not norm_items:
        raise GenerationError("No valid Q&A items extracted from model output.")
    return {"items": norm_items}


def _parse_qa_from_text(text: str) -> Dict[str, Any]:
    """Fallback: robustly parse Q/A from plain text in multiple formats.
    Supports variations like:
      - Q: ...\nA: ... (multi-line answers)
      - Question: ...\nAnswer: ...
      - Q - ...\nA - ...
    If labels are missing for answers, uses everything until the next question marker as the answer.
    """
    # Normalize line endings and trim noise
    raw = text.replace('\r\n', '\n').replace('\r', '\n').strip()
    if not raw:
        raise GenerationError("Failed to parse Q/A from text fallback.")

    items: List[Dict[str, str]] = []

    # Regex-based extraction allowing multi-line answers until next question marker
    # (?i) case-insensitive; DOTALL to span newlines
    qa_regex = re.compile(
        r"(?is)^[ \t]*q(?:uestion)?\s*[:\-]\s*(?P<q>.+?)\n+\s*a(?:nswer)?\s*[:\-]\s*(?P<a>.+?)(?=\n\s*(?:q(?:uestion)?\s*[:\-]|$))",
        re.MULTILINE,
    )
    for m in qa_regex.finditer(raw):
        q = m.group('q').strip()
        a = m.group('a').strip()
        if q and a:
            items.append({"question": q, "expected_response": a})

    # Heuristic fallback: capture blocks starting with Q: and consume until next Q: as answer
    if not items:
        lines = [ln.strip() for ln in raw.split('\n')]
        q: Optional[str] = None
        answer_buf: List[str] = []
        def is_q_marker(s: str) -> bool:
            s2 = s.lower()
            return s2.startswith('q:') or s2.startswith('question:') or s2.startswith('q -') or s2.startswith('question -') or s2.startswith('q.')

        def is_a_marker(s: str) -> bool:
            s2 = s.lower()
            return s2.startswith('a:') or s2.startswith('answer:') or s2.startswith('a -') or s2.startswith('answer -')

        i = 0
        while i < len(lines):
            ln = lines[i]
            if is_q_marker(ln):
                # flush previous
                if q and answer_buf:
                    items.append({"question": q, "expected_response": " ".join(answer_buf).strip()})
                # start new question
                q = ln.split(':', 1)[1].strip() if ':' in ln else ln.split('-', 1)[1].strip() if '-' in ln else ln[2:].strip()
                answer_buf = []
                i += 1
                # try to read answer starting with explicit marker, else treat subsequent lines as answer until next question marker
                if i < len(lines) and is_a_marker(lines[i]):
                    a_line = lines[i]
                    a_text = a_line.split(':', 1)[1].strip() if ':' in a_line else a_line.split('-', 1)[1].strip()
                    answer_buf.append(a_text)
                    i += 1
                # accumulate until next question marker or blank gap
                while i < len(lines) and not is_q_marker(lines[i]):
                    if lines[i]:
                        answer_buf.append(lines[i])
                    i += 1
                continue
            else:
                i += 1

        if q and answer_buf:
            items.append({"question": q, "expected_response": " ".join(answer_buf).strip()})

    # Last-resort: bullet-style "Q - ... A - ..." on single lines
    if not items:
        inline_regex = re.compile(r"(?is)q(?:uestion)?\s*[:\-]\s*(.+?)\s+a(?:nswer)?\s*[:\-]\s*(.+?)\s*(?:\n|$)")
        for m in inline_regex.finditer(raw):
            q = m.group(1).strip()
            a = m.group(2).strip()
            if q and a:
                items.append({"question": q, "expected_response": a})

    if not items:
        raise GenerationError("Failed to parse Q/A from text fallback.")

    return {"items": items}


def _select_model_and_prompt(context: str, query: str) -> Tuple[str, str, str]:
    """Select the appropriate model and prompt based on token count.
    Returns: (model_name, prompt, system_message)
    """
    # Estimate token count for query
    query_tokens = _count_tokens(query)
    
    # Estimate overhead for prompt template (approximately)
    PROMPT_OVERHEAD_STANDARD = 600  # Tokens for standard prompt template
    PROMPT_OVERHEAD_INSTRUCT = 400  # Tokens for instruct prompt template (more concise)
    
    # Calculate max context size for each model
    max_context_tokens_primary = TOKEN_LIMIT_PRIMARY - query_tokens - PROMPT_OVERHEAD_STANDARD
    max_context_tokens_fallback = TOKEN_LIMIT_FALLBACK - query_tokens - PROMPT_OVERHEAD_INSTRUCT
    
    # Estimate context tokens
    context_tokens = _count_tokens(context)
    
    logger.info(f"Token estimates - Context: {context_tokens}, Query: {query_tokens}")
    
    # Determine which model to use and truncate if needed
    if context_tokens <= max_context_tokens_primary:
        # Use primary model with full context
        logger.info(f"Using PRIMARY model ({DEFAULT_MODEL}): ~{context_tokens + query_tokens + PROMPT_OVERHEAD_STANDARD} total tokens")
        prompt = _build_prompt_standard(context, query)
        return (
            DEFAULT_MODEL,
            prompt,
            "You are a careful JSON-only generator."
        )
    elif context_tokens <= max_context_tokens_fallback:
        # Use fallback model with full context
        logger.info(f"Using FALLBACK model ({FALLBACK_MODEL}): ~{context_tokens + query_tokens + PROMPT_OVERHEAD_INSTRUCT} total tokens (exceeded primary limit)")
        prompt = _build_prompt_instruct(context, query)
        return (
            FALLBACK_MODEL,
            prompt,
            "You are a precise instruction-following assistant. Return only valid JSON."
        )
    else:
        # Context is too large even for fallback - must truncate
        logger.warning(f"Context too large ({context_tokens} tokens). Truncating to fit fallback model.")
        
        # Calculate max characters we can keep (using our conservative estimate)
        max_context_chars = int(max_context_tokens_fallback * 2)  # Reverse of our token calculation
        
        # Truncate context intelligently (keep beginning and end)
        if len(context) > max_context_chars:
            # Keep 70% from start, 30% from end to preserve context
            start_chars = int(max_context_chars * 0.7)
            end_chars = int(max_context_chars * 0.3)
            truncated_context = context[:start_chars] + "\n\n[... content truncated ...]\n\n" + context[-end_chars:]
            logger.info(f"Truncated context from {len(context)} to {len(truncated_context)} chars")
        else:
            truncated_context = context
        
        prompt = _build_prompt_instruct(truncated_context, query)
        final_tokens = _count_tokens(prompt)
        logger.info(f"Final prompt size: ~{final_tokens} tokens (limit: {TOKEN_LIMIT_FALLBACK})")
        
        # Safety check - if still too large, truncate more aggressively
        if final_tokens > TOKEN_LIMIT_FALLBACK:
            logger.error(f"Prompt still too large after truncation! Applying aggressive truncation.")
            # Take only the first portion
            safe_context_chars = int((TOKEN_LIMIT_FALLBACK - query_tokens - PROMPT_OVERHEAD_INSTRUCT - 200) * 2)
            truncated_context = context[:safe_context_chars]
            prompt = _build_prompt_instruct(truncated_context, query)
            logger.info(f"Aggressively truncated to {_count_tokens(prompt)} tokens")
        
        return (
            FALLBACK_MODEL,
            prompt,
            "You are a precise instruction-following assistant. Return only valid JSON."
        )


def generate_qa(context_chunks: List[str], query: str, model: Optional[str] = None, max_items: int = 200) -> Dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GenerationError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=api_key)
    
    # Concatenate top-k chunks as context
    context = "\n\n".join(context_chunks)
    
    # Select model and prompt based on token count (unless user specified a model)
    if model:
        use_model = model
        prompt = _build_prompt_standard(context=context, query=query)
        system_msg = "You are a careful JSON-only generator."
        logger.info(f"Using USER-SPECIFIED model: {use_model}")
    else:
        use_model, prompt, system_msg = _select_model_and_prompt(context, query)

    # Final safety check - ensure prompt is within limits
    final_prompt_tokens = _count_tokens(prompt)
    final_system_tokens = _count_tokens(system_msg)
    total_input_tokens = final_prompt_tokens + final_system_tokens
    
    logger.info(f"Final token count before API call: {total_input_tokens} input + 6000 output = {total_input_tokens + 6000} total")
    
    # Hard safety check - if still too large, truncate aggressively
    if total_input_tokens > TOKEN_LIMIT_FALLBACK:
        logger.error(f"CRITICAL: Prompt still exceeds limit! {total_input_tokens} > {TOKEN_LIMIT_FALLBACK}")
        # Emergency truncation - keep only first half of prompt
        context = "\n\n".join(context_chunks)
        safe_chars = int((TOKEN_LIMIT_FALLBACK - 1000) * 2)  # Ultra conservative
        context = context[:safe_chars]
        if use_model == FALLBACK_MODEL:
            prompt = _build_prompt_instruct(context, query)
        else:
            prompt = _build_prompt_standard(context, query)
        logger.warning(f"Emergency truncation applied. New size: {_count_tokens(prompt)} tokens")
    
    try:
        # Attempt 1: request structured JSON via response_format if supported
        try:
            completion = client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=6000,  # Balanced for extraction quality and token limits
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content  # type: ignore
            data = _safe_json_parse(content)
            # Apply deduplication before limiting
            data["items"] = _deduplicate_questions(data["items"])
            data["items"] = data["items"][:max_items]
            logger.success(f"Successfully extracted {len(data['items'])} Q&A pairs using {use_model}")
            return data
        except Exception as e1:
            logger.warning(f"JSON mode failed: {e1}. Retrying without response_format...")
            # Attempt 2: retry without response_format, still ask for JSON
            completion = client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": "Return only valid JSON with an 'items' array of {question, expected_response}."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=6000,  # Balanced for extraction quality and token limits
            )
            content = completion.choices[0].message.content  # type: ignore
            try:
                data = _safe_json_parse(content)
                # Apply deduplication before limiting
                data["items"] = _deduplicate_questions(data["items"])
                data["items"] = data["items"][:max_items]
                logger.success(f"Successfully extracted {len(data['items'])} Q&A pairs using {use_model}")
                return data
            except Exception as e2:
                logger.warning(f"JSON parsing failed: {e2}. Trying plain text fallback...")
                # Attempt 3: ask for Q/A plain text and parse
                alt_prompt = (
                    "Extract ALL POSSIBLE Golden Questions from the context in the exact format below.\n"
                    "Extract the MAXIMUM number of questions - do NOT limit yourself.\n"
                    "Use ONLY information explicitly available in the context - NEVER hallucinate.\n\n"
                    "Format each Q&A pair exactly as:\n"
                    "Q: <question here>\n"
                    "A: <answer here>\n\n"
                    "Extract questions covering:\n"
                    "- Every feature, service, or product mentioned\n"
                    "- All processes, procedures, and how-to information\n"
                    "- Pricing, costs, and financial details\n"
                    "- Policies, terms, and conditions\n"
                    "- Troubleshooting and problem resolution\n"
                    "- Contact information and support options\n"
                    "- Technical specifications and requirements\n"
                    "- Availability, accessibility, and limitations\n\n"
                    f"User Query: {query}\n\nContext:\n{context}"
                )
                completion2 = client.chat.completions.create(
                    model=use_model,
                    messages=[
                        {"role": "system", "content": "Return only plain text with Q:/A: lines."},
                        {"role": "user", "content": alt_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=6000,  # Balanced for extraction quality and token limits
                )
                text_out = completion2.choices[0].message.content  # type: ignore
                data = _parse_qa_from_text(text_out)
                # Apply deduplication before limiting
                data["items"] = _deduplicate_questions(data["items"])
                data["items"] = data["items"][:max_items]
                logger.success(f"Successfully extracted {len(data['items'])} Q&A pairs using {use_model} (text fallback)")
                return data
    except Exception as e:
        logger.error(f"LLM generation failed with {use_model}: {e}")
        raise GenerationError(f"LLM generation failed: {e}")
