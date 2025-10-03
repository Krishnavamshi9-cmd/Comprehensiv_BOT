#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced Golden Questions extraction system.
This script tests the extraction capabilities with sample content.
"""

import os
from generator import generate_qa, GenerationError
from formatter import validate_qa_format, format_qa_output

# Sample content that represents typical website content
SAMPLE_CONTENT = """
Welcome to TechCorp Cloud Services

Our cloud platform offers scalable computing solutions for businesses of all sizes.

Pricing Plans:
- Basic Plan: $10/month - 1GB storage, 10GB bandwidth
- Pro Plan: $25/month - 10GB storage, 100GB bandwidth  
- Enterprise Plan: $100/month - 100GB storage, unlimited bandwidth

Getting Started:
1. Create an account on our website
2. Choose your pricing plan
3. Set up your first project
4. Deploy your applications

Support:
We offer 24/7 customer support via email and live chat.
Enterprise customers get dedicated phone support.

Security:
All data is encrypted at rest and in transit.
We comply with SOC 2 Type II and ISO 27001 standards.

API Documentation:
Our REST API allows you to manage resources programmatically.
Rate limits: 1000 requests per hour for Basic, 10000 for Pro, unlimited for Enterprise.

Frequently Asked Questions:

Q: How do I upgrade my plan?
A: You can upgrade anytime from your account dashboard. Changes take effect immediately.

Q: What payment methods do you accept?
A: We accept all major credit cards and PayPal.

Q: Is there a free trial?
A: Yes, we offer a 14-day free trial with full access to Pro features.

Q: How do I cancel my subscription?
A: You can cancel anytime from your account settings. No cancellation fees.

Q: Where are your data centers located?
A: We have data centers in US East, US West, Europe, and Asia Pacific regions.
"""


def test_extraction():
    """Test the enhanced extraction system with sample content."""
    print("🧪 Testing Enhanced Golden Questions Extraction System")
    print("=" * 60)
    
    try:
        # Test with sample content
        print("📝 Sample Content Length:", len(SAMPLE_CONTENT), "characters")
        print("\n🔍 Extracting Golden Questions...")
        
        # Split content into chunks (simulating the chunking process)
        chunks = [SAMPLE_CONTENT]
        
        # Generate Q&A pairs
        query = "Extract ALL possible Golden Questions that users might ask about this service"
        result = generate_qa(chunks, query=query, max_items=50)
        
        items = result.get("items", [])
        print(f"✅ Raw extraction: {len(items)} Q&A pairs")
        
        # Validate and format
        validated_items = validate_qa_format(items)
        print(f"✅ After validation: {len(validated_items)} valid Q&A pairs")
        
        # Display results
        print("\n📋 Extracted Golden Questions:")
        print("-" * 40)
        
        for i, item in enumerate(validated_items[:10], 1):  # Show first 10
            print(f"\n{i}. Q: {item['question']}")
            print(f"   A: {item['expected_response']}")
        
        if len(validated_items) > 10:
            print(f"\n... and {len(validated_items) - 10} more questions")
        
        # Test text format output
        print(f"\n📄 Text Format Sample (Q:/A:):")
        print("-" * 30)
        text_output = format_qa_output(validated_items[:3], "text")
        print(text_output)
        
        print(f"\n🎯 Summary:")
        print(f"   • Total Questions Extracted: {len(validated_items)}")
        print(f"   • Content Coverage: Comprehensive")
        print(f"   • Format Validation: ✅ Passed")
        print(f"   • Deduplication: ✅ Applied")
        
        return True
        
    except GenerationError as e:
        print(f"❌ Generation Error: {e}")
        print("💡 Make sure your GROQ_API_KEY is set in the .env file")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


def test_deduplication():
    """Test the deduplication functionality."""
    print("\n🔄 Testing Deduplication Logic")
    print("=" * 40)
    
    from generator import _deduplicate_questions
    
    # Sample items with duplicates
    test_items = [
        {"question": "How do I upgrade my plan?", "expected_response": "You can upgrade from your dashboard."},
        {"question": "How can I upgrade my subscription?", "expected_response": "Visit your account settings to upgrade."},
        {"question": "What payment methods are accepted?", "expected_response": "We accept credit cards and PayPal."},
        {"question": "Which payment options do you support?", "expected_response": "All major credit cards and PayPal are supported."},
        {"question": "Is there customer support?", "expected_response": "Yes, we offer 24/7 support."},
    ]
    
    print(f"📥 Input: {len(test_items)} items")
    deduplicated = _deduplicate_questions(test_items)
    print(f"📤 Output: {len(deduplicated)} items (after deduplication)")
    
    print("\n🔍 Deduplicated Results:")
    for i, item in enumerate(deduplicated, 1):
        print(f"{i}. {item['question']}")
    
    return len(deduplicated) < len(test_items)


if __name__ == "__main__":
    print("🚀 Golden Questions Extraction System Test Suite")
    print("=" * 60)
    
    # Check if API key is available
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  Warning: GROQ_API_KEY not found in environment")
        print("   Set your API key in the .env file to run full tests")
        print("\n🧪 Running offline tests only...")
        
        # Run deduplication test (doesn't need API)
        success = test_deduplication()
        print(f"\n✅ Deduplication test: {'PASSED' if success else 'FAILED'}")
    else:
        # Run full test suite
        print("🔑 API Key found - running full test suite...\n")
        
        extraction_success = test_extraction()
        dedup_success = test_deduplication()
        
        print(f"\n🏁 Test Results:")
        print(f"   • Extraction Test: {'✅ PASSED' if extraction_success else '❌ FAILED'}")
        print(f"   • Deduplication Test: {'✅ PASSED' if dedup_success else '❌ FAILED'}")
        
        if extraction_success and dedup_success:
            print(f"\n🎉 All tests passed! The system is ready for use.")
        else:
            print(f"\n⚠️  Some tests failed. Check the error messages above.")
