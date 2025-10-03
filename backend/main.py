import argparse
import sys
import os
from typing import List

from dotenv import load_dotenv

from enhanced_scraper import enhanced_scrape_url as scrape_url, ScraperError
from enhanced_preprocess import aggressive_clean_text as clean_text, enhanced_chunk_text as chunk_text
from vector_store import VectorStore
from generator import generate_qa, GenerationError
from exporter import export_to_excel, export_to_excel_with_testcases
from testcases import generate_test_cases_rule_based, generate_test_cases_llm
from formatter import save_qa_as_text, validate_qa_format


def run_pipeline(
    url: str,
    query: str,
    output: str,
    k: int = 20,
    scroll_pages: int = 5,
    output_format: str = "excel",
    validate_content: bool = True,
    *,
    crawl: bool = False,
    max_depth: int = 1,
    max_pages: int = 20,
    same_domain_only: bool = True,
    with_test_cases: bool = False,
    test_cases_llm: bool = False,
    tc_variations: int = 20,
    tc_negatives: int = 12,
) -> str:
    print(f"[1/7] Scraping: {url} (scrolling {scroll_pages} pages)")
    raw = scrape_url(
        url,
        scroll_pages=scroll_pages,
        crawl=crawl,
        max_depth=max_depth,
        max_pages=max_pages,
        same_domain_only=same_domain_only,
    )
    print(f"Scraped content length: {len(raw)} characters")
    
    # Content quality validation
    if validate_content:
        try:
            from enhanced_preprocess import ContentQualityAnalyzer
            analyzer = ContentQualityAnalyzer()
            quality = analyzer.analyze_content_quality(raw)
            print(f"Raw content quality score: {quality['quality_score']}/100")
            
            if quality['quality_score'] < 30:
                print("⚠ Warning: Low quality content detected. Results may be limited.")
                if quality['issues']:
                    print(f"Issues: {', '.join(quality['issues'])}")
        except ImportError:
            pass

    print("[2/7] Preprocessing text")
    cleaned = clean_text(raw)
    print(f"Cleaned content length: {len(cleaned)} characters")
    
    # Validate preprocessing improvement
    if validate_content:
        try:
            from enhanced_preprocess import ContentQualityAnalyzer
            analyzer = ContentQualityAnalyzer()
            cleaned_quality = analyzer.analyze_content_quality(cleaned)
            improvement = cleaned_quality['quality_score'] - quality['quality_score']
            print(f"Cleaned content quality score: {cleaned_quality['quality_score']}/100 ({improvement:+d})")
        except (ImportError, NameError):
            pass
    
    # Use larger chunks and more overlap for better coverage
    chunks = chunk_text(cleaned, chunk_size=800, chunk_overlap=100)
    if not chunks:
        raise RuntimeError("No chunks produced from the page content.")

    print(f"[3/7] Building vector index over {len(chunks)} chunks")
    vs = VectorStore()
    vs.build_index(chunks)

    # Retrieve more chunks to get comprehensive coverage
    print(f"[4/7] Retrieving top-{k} chunks for query: {query}")
    scored = vs.query(query, k=k)
    if not scored:
        raise RuntimeError("Retriever returned no results.")
    top_chunks = [t for t, _ in scored]
    
    # Log the total context being sent to LLM
    total_context_length = sum(len(chunk) for chunk in top_chunks)
    print(f"Total context length for LLM: {total_context_length} characters")
    
    # Validate chunk quality
    if validate_content:
        try:
            from enhanced_preprocess import ContentQualityAnalyzer
            analyzer = ContentQualityAnalyzer()
            chunk_qualities = [analyzer.analyze_content_quality(chunk)['quality_score'] for chunk in top_chunks]
            avg_chunk_quality = sum(chunk_qualities) / len(chunk_qualities)
            print(f"Average chunk quality: {avg_chunk_quality:.1f}/100")
            
            if avg_chunk_quality < 40:
                print("⚠ Warning: Low chunk quality may affect Q&A generation")
        except ImportError:
            pass

    print("[5/7] Generating Q&A via LLM")
    # Generate maximum questions without artificial limits
    data = generate_qa(top_chunks, query=query, max_items=200)
    items = data.get("items", [])
    
    # Validate and clean the Q&A format
    print(f"[6/7] Validating and cleaning {len(items)} Q&A pairs")
    validated_items = validate_qa_format(items)
    print(f"After validation: {len(validated_items)} valid Q&A pairs")

    # Optional: generate structured test cases (Option A - separate sheet)
    testcases = None
    if with_test_cases:
        print("[6b] Generating structured test cases for each question")
        if test_cases_llm:
            try:
                testcases = generate_test_cases_llm(validated_items, variations_n=tc_variations, negatives_n=tc_negatives)
            except Exception as e:
                print(f"⚠ LLM test case generation failed, falling back to rule-based: {e}")
                testcases = generate_test_cases_rule_based(validated_items, variations_n=tc_variations, negatives_n=tc_negatives)
        else:
            testcases = generate_test_cases_rule_based(validated_items, variations_n=tc_variations, negatives_n=tc_negatives)

    print(f"[7/7] Exporting to {output_format.upper()} format: {output}")
    if output_format.lower() == "text":
        path = save_qa_as_text(validated_items, output)
    else:
        if testcases is not None:
            path = export_to_excel_with_testcases(validated_items, testcases, output, url)
        else:
            path = export_to_excel(validated_items, output, url)
    return path


def main(argv: List[str]) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Web Page Intelligence for Bot Testing (RAG)")
    parser.add_argument("url", type=str, help="Webpage URL containing bot FAQ or documentation")
    parser.add_argument("--query", type=str, default="Extract Golden Questions and Expected Responses that users commonly ask about this product/service for comprehensive bot testing", help="Retrieval/generation query")
    parser.add_argument("--output", type=str, default=os.path.join("output", "golden_qna.xlsx"), help="Output Excel filename (defaults to output/golden_qna.xlsx)")
    parser.add_argument("--k", type=int, default=30, help="Top-k chunks to retrieve (more chunks = more comprehensive coverage)")
    parser.add_argument("--scroll-pages", type=int, default=5, help="Number of page scrolls to load dynamic content (more scrolls = more content)")
    parser.add_argument("--format", type=str, choices=["excel", "text"], default="excel", help="Output format: 'excel' for .xlsx or 'text' for Q:/A: format")
    parser.add_argument("--validate", action="store_true", help="Enable content quality validation and debugging")
    parser.add_argument("--debug", action="store_true", help="Run full pipeline validation and save debug files")
    # Test case generation options (Option A)
    parser.add_argument("--with-test-cases", action="store_true", help="Also generate structured test cases and add a 'TestCases' sheet to the Excel output")
    parser.add_argument("--test-cases-llm", action="store_true", help="Use LLM to generate variations/negative cases instead of rule-based templates")
    parser.add_argument("--tc-variations", type=int, default=20, help="Number of paraphrase variations per question (default: 20)")
    parser.add_argument("--tc-negatives", type=int, default=12, help="Number of negative/edge-case variants per question (default: 12)")
    # Crawling options
    parser.add_argument("--crawl", action="store_true", help="Follow hyperlinks and aggregate content from linked pages")
    parser.add_argument("--max-depth", type=int, default=1, help="Maximum hyperlink depth to crawl when --crawl is set (default: 1)")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum number of pages to crawl including the seed (default: 20)")
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow crawling to external domains (by default, restrict to same domain)",
    )
    args = parser.parse_args(argv)

    try:
        # Debug mode - run full validation
        if args.debug:
            try:
                from content_validator import PipelineValidator
                validator = PipelineValidator()
                results = validator.validate_full_pipeline(args.url)
                
                assessment = results.get("assessment", {})
                if assessment.get("readiness") != "ready":
                    print("⚠ Pipeline validation suggests issues. Proceeding anyway...")
                else:
                    print("✅ Pipeline validation passed!")
            except ImportError:
                print("⚠ Debug mode requires content_validator.py")
        
        # If user passed a bare filename without directory, prefix with output/
        output_path = args.output
        if not os.path.dirname(output_path):
            output_path = os.path.join("output", output_path)
        
        out = run_pipeline(
            url=args.url, 
            query=args.query, 
            output=output_path, 
            k=args.k, 
            scroll_pages=args.scroll_pages, 
            output_format=args.format,
            validate_content=args.validate or args.debug,
            crawl=args.crawl,
            max_depth=args.max_depth,
            max_pages=args.max_pages,
            same_domain_only=not args.allow_external,
            with_test_cases=args.with_test_cases,
            test_cases_llm=args.test_cases_llm,
            tc_variations=max(1, args.tc_variations),
            tc_negatives=max(1, args.tc_negatives),
        )
        print(f"Done. File saved at: {out}")
        return 0
    except ScraperError as e:
        print(f"Scraper error: {e}")
    except GenerationError as e:
        print(f"Generation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
