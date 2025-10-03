from typing import Dict, List


def format_qa_output(items: List[Dict[str, str]], output_format: str = "excel") -> str:
    """
    Format Q&A items into the specified output format.
    
    Args:
        items: List of Q&A dictionaries with 'question' and 'expected_response' keys
        output_format: Either 'excel' (default) or 'text' for Q:/A: format
    
    Returns:
        Formatted string output
    """
    if output_format == "text":
        formatted_lines = []
        for item in items:
            question = item.get("question", "").strip()
            answer = item.get("expected_response", "").strip()
            
            if question and answer:
                formatted_lines.append(f"Q: {question}")
                formatted_lines.append(f"A: {answer}")
                formatted_lines.append("")  # Empty line between Q&A pairs
        
        return "\n".join(formatted_lines)
    
    # Default to returning items as-is for Excel format
    return items


def validate_qa_format(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Validate and clean Q&A items to ensure proper format.
    
    Args:
        items: List of Q&A dictionaries
    
    Returns:
        Cleaned and validated list of Q&A items
    """
    validated_items = []
    
    for item in items:
        question = item.get("question", "").strip()
        answer = item.get("expected_response", "").strip()
        
        # Skip items with missing question or answer
        if not question or not answer:
            continue
        
        # Clean up question format
        if not question.endswith("?"):
            question += "?"
        
        # Ensure question starts with capital letter
        if question and question[0].islower():
            question = question[0].upper() + question[1:]
        
        # Clean up answer format
        if answer and answer[0].islower():
            answer = answer[0].upper() + answer[1:]
        
        validated_items.append({
            "question": question,
            "expected_response": answer
        })
    
    return validated_items


def save_qa_as_text(items: List[Dict[str, str]], output_path: str) -> str:
    """
    Save Q&A items in Q:/A: text format.
    
    Args:
        items: List of Q&A dictionaries
        output_path: Path to save the text file
    
    Returns:
        Path to the saved file
    """
    import os
    
    # Validate items first
    validated_items = validate_qa_format(items)
    
    # Format as Q:/A: text
    formatted_text = format_qa_output(validated_items, "text")
    
    # Ensure directory exists
    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted_text)
    
    return output_path
