"""
Test script for model switching based on token count.
Verifies that the system correctly selects models based on context size.
"""

import os
from dotenv import load_dotenv
from generator import _count_tokens, _select_model_and_prompt, DEFAULT_MODEL, FALLBACK_MODEL

load_dotenv()

def test_token_counting():
    """Test token counting function."""
    print("\n" + "="*60)
    print("TEST 1: Token Counting")
    print("="*60)
    
    test_cases = [
        ("", 0),
        ("Hello world", 3),  # ~11 chars / 3 ≈ 3 tokens
        ("A" * 1000, 333),   # 1000 chars / 3 ≈ 333 tokens
    ]
    
    for text, expected_approx in test_cases:
        count = _count_tokens(text)
        print(f"Text length: {len(text):>4} chars → {count:>4} tokens (expected ~{expected_approx})")
        assert abs(count - expected_approx) <= 1, f"Token count mismatch: {count} vs {expected_approx}"
    
    print("✅ Token counting test PASSED\n")


def test_small_context_uses_primary_model():
    """Test that small context uses the primary model."""
    print("="*60)
    print("TEST 2: Small Context (Should Use Primary Model)")
    print("="*60)
    
    small_context = "This is a small product description with basic information."
    query = "Extract Q&A pairs"
    
    model, prompt, system_msg = _select_model_and_prompt(small_context, query)
    
    print(f"Context size: {len(small_context)} chars")
    print(f"Token estimate: {_count_tokens(small_context + prompt)} tokens")
    print(f"Selected model: {model}")
    print(f"System message: {system_msg}")
    
    assert model == DEFAULT_MODEL, f"Expected {DEFAULT_MODEL}, got {model}"
    print(f"✅ Correctly selected PRIMARY model: {model}\n")


def test_large_context_uses_fallback_model():
    """Test that large context uses the fallback model."""
    print("="*60)
    print("TEST 3: Large Context (Should Use Fallback Model)")
    print("="*60)
    
    # Create a large context that exceeds 6000 tokens (>18000 chars)
    large_context = """
    This is a comprehensive product catalog with detailed information about
    various products, services, features, pricing, policies, and technical specifications.
    """ * 500  # Repeat to make it large
    
    query = "Extract Q&A pairs"
    
    model, prompt, system_msg = _select_model_and_prompt(large_context, query)
    
    print(f"Context size: {len(large_context)} chars")
    print(f"Token estimate: {_count_tokens(large_context + prompt)} tokens")
    print(f"Selected model: {model}")
    print(f"System message: {system_msg}")
    
    assert model == FALLBACK_MODEL, f"Expected {FALLBACK_MODEL}, got {model}"
    print(f"✅ Correctly selected FALLBACK model: {model}\n")


def test_instruct_prompt_format():
    """Test that the instruct prompt has the correct format."""
    print("="*60)
    print("TEST 4: Instruct Prompt Format")
    print("="*60)
    
    large_context = "Context" * 3000
    query = "Extract Q&A"
    
    model, prompt, system_msg = _select_model_and_prompt(large_context, query)
    
    # Check that the prompt contains step-by-step instructions
    required_elements = [
        "TASK:",
        "STEP 1",
        "STEP 2",
        "STEP 3",
        "STEP 4",
        "STEP 5",
        "BEGIN EXTRACTION NOW"
    ]
    
    print("Checking for required prompt elements:")
    for element in required_elements:
        assert element in prompt, f"Missing required element: {element}"
        print(f"  ✓ Found: {element}")
    
    print("✅ Instruct prompt format is correct\n")


def test_very_large_context_truncation():
    """Test that extremely large context gets truncated."""
    print("="*60)
    print("TEST 5: Very Large Context (Should Truncate)")
    print("="*60)
    
    # Create context that exceeds even the fallback limit (>75000 chars)
    very_large_context = "X" * 100000
    query = "Extract Q&A pairs"
    
    model, prompt, system_msg = _select_model_and_prompt(very_large_context, query)
    
    print(f"Original context size: {len(very_large_context)} chars")
    print(f"Prompt size after processing: {len(prompt)} chars")
    print(f"Selected model: {model}")
    
    # Should still use fallback model with truncated context
    assert model == FALLBACK_MODEL, f"Expected {FALLBACK_MODEL}, got {model}"
    assert len(prompt) < len(very_large_context), "Context should be truncated"
    print(f"✅ Context was truncated and uses FALLBACK model\n")


def run_all_tests():
    """Run all tests."""
    print("\n" + "🚀 STARTING MODEL SWITCHING TESTS 🚀".center(60, "="))
    
    try:
        test_token_counting()
        test_small_context_uses_primary_model()
        test_large_context_uses_fallback_model()
        test_instruct_prompt_format()
        test_very_large_context_truncation()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED! ✅".center(60))
        print("="*60)
        print("\nModel switching implementation is working correctly!")
        print(f"Primary model: {DEFAULT_MODEL}")
        print(f"Fallback model: {FALLBACK_MODEL}")
        
    except AssertionError as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED! ❌".center(60))
        print("="*60)
        print(f"Error: {e}")
        raise
    except Exception as e:
        print("\n" + "="*60)
        print("❌ UNEXPECTED ERROR! ❌".center(60))
        print("="*60)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
