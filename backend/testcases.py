from typing import Dict, List
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Columns for the TestCases sheet
TESTCASE_COLUMNS = [
    "ID",
    "Question",
    "Expected Response",
    "Test Steps",
    "Variations",
    "Negative Case",
    "Entities/Slots",
    "Notes",
]


def _default_steps(question: str) -> str:
    return (
        "1) Open the chat interface\n"
        f"2) Ask: '{question}'\n"
        "3) Wait for the bot response\n"
        "4) Verify response matches 'Expected Response' without missing facts or hallucinations\n"
        "5) If the bot asks for clarification, provide minimal clarifying info and re-validate"
    )


def _default_variations(question: str, max_items: int = 10) -> str:
    """Generate multiple paraphrases for a question using simple heuristics."""
    base = question.strip()
    stem = base.rstrip('?')
    lower_cap = stem.lower().capitalize()
    tokens = stem.split()
    keyword = " ".join(t for t in tokens if len(t) > 2)
    polite = [
        f"Could you please tell me: {stem}?",
        f"Please provide: {stem}?",
        f"I want to know: {stem}?",
    ]
    wh_forms = [
        f"What is the detail about {stem}?" if not base.lower().startswith("what") else f"Can you explain {stem}?",
        f"Share information on: {stem}?",
    ]
    style_changes = [
        f"{lower_cap}?",
        f"{stem} please?",
        f"Help with: {stem}?",
        f"Looking for details on {stem}.",
    ]
    keyword_form = [f"{keyword}?"] if keyword and keyword != stem else []
    variations = [
        f"- {base}",
        *[f"- {v}" for v in polite],
        *[f"- {v}" for v in wh_forms],
        *[f"- {v}" for v in style_changes],
        *[f"- {v}" for v in keyword_form],
    ]
    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for v in variations:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return "\n".join(uniq[:max_items])


def _default_negative(question: str, max_items: int = 10) -> str:
    """Generate multiple negative/edge-case variants for a question."""
    stem = question.strip().rstrip('?')
    words = stem.split()
    first = words[0] if words else ""
    ambiguous = f"- {first} ???"
    missing_entity = f"- {stem.replace(words[-1], '___') if words else stem} ?" if words else f"- {stem} ?"
    noisy = f"- {stem} [random context added unrelated to topic]?"
    conflicting = f"- {stem} but also for a different product at the same time?"
    long_run = f"- {stem}??????"  # excessive punctuation
    non_ascii = f"- {stem} — please??"  # unicode dash
    empty = "- ?"
    negatives = [ambiguous, missing_entity, noisy, conflicting, long_run, non_ascii, empty]
    return "\n".join(negatives[:max_items])


def generate_test_cases_rule_based(items: List[Dict[str, str]], variations_n: int = 10, negatives_n: int = 10) -> List[Dict[str, str]]:
    testcases: List[Dict[str, str]] = []
    for i, it in enumerate(items, start=1):
        q = it.get("question", "").strip()
        a = it.get("expected_response", "").strip()
        if not q or not a:
            continue
        testcases.append(
            {
                "ID": i,
                "Question": q,
                "Expected Response": a,
                "Test Steps": _default_steps(q),
                "Variations": _default_variations(q, variations_n),
                "Negative Case": _default_negative(q, negatives_n),
                "Entities/Slots": "",
                "Notes": "",
            }
        )
    return testcases


def _llm_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set for LLM-based test case generation")
    return Groq(api_key=api_key)


def _llm_prompt_for_testcases(question: str, expected: str) -> str:
    return (
        "You are a QA test case generator for chatbot question/answer validation.\n"
        "Given a Question and its Expected Response (ground truth), create structured test artifacts.\n"
        "Return JSON with keys: steps, variations, negative, entities, notes.\n"
        "Constraints: Steps should be 4-6 concise steps. Provide 3-5 rephrase variations.\n"
        f"Question: {question}\n"
        f"Expected: {expected}"
    )


def generate_test_cases_llm(items: List[Dict[str, str]], model: str | None = None, variations_n: int = 10, negatives_n: int = 10) -> List[Dict[str, str]]:
    client = _llm_client()
    use_model = model or os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    out: List[Dict[str, str]] = []
    for i, it in enumerate(items, start=1):
        q = it.get("question", "").strip()
        a = it.get("expected_response", "").strip()
        if not q or not a:
            continue
        prompt = _llm_prompt_for_testcases(q, a)
        try:
            completion = client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": "Return only JSON with keys: steps, variations, negative, entities, notes."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content  # type: ignore
        except Exception:
            # Fallback without response_format
            completion = client.chat.completions.create(
                model=use_model,
                messages=[
                    {"role": "system", "content": "Return only JSON with keys: steps, variations, negative, entities, notes."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1200,
            )
            content = completion.choices[0].message.content  # type: ignore
        # Parse JSON leniently
        import json
        try:
            start = content.find('{')
            end = content.rfind('}')
            data = json.loads(content[start:end+1]) if start != -1 and end != -1 else {}
        except Exception:
            data = {}
        steps = data.get("steps") or _default_steps(q)
        variations = data.get("variations") or _default_variations(q, variations_n)
        negative = data.get("negative") or _default_negative(q, negatives_n)
        entities = data.get("entities") or ""
        notes = data.get("notes") or ""
        out.append(
            {
                "ID": i,
                "Question": q,
                "Expected Response": a,
                "Test Steps": steps if isinstance(steps, str) else "\n".join(steps),
                "Variations": variations if isinstance(variations, str) else "\n".join(variations),
                "Negative Case": negative if isinstance(negative, str) else "\n".join(negative),
                "Entities/Slots": entities if isinstance(entities, str) else ", ".join(entities),
                "Notes": notes if isinstance(notes, str) else "\n".join(notes),
            }
        )
    return out
