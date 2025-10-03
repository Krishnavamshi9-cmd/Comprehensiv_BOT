"""
Content validation and debugging tools for the scraping pipeline.
Helps identify and diagnose issues in the scraping → preprocessing → generation pipeline.
"""

import json
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import hashlib

from enhanced_scraper import enhanced_scrape_url, _validate_content_quality
from enhanced_preprocess import aggressive_clean_text, enhanced_chunk_text, ContentQualityAnalyzer


class PipelineValidator:
    """Validates and debugs the entire content processing pipeline."""
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.analyzer = ContentQualityAnalyzer()
        self.validation_results = {}
    
    def validate_full_pipeline(self, url: str, save_debug: bool = True) -> Dict[str, Any]:
        """Run full pipeline validation and return detailed results."""
        
        print(f"🔍 Validating pipeline for: {url}")
        print("=" * 60)
        
        results = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: Scraping
            print("📡 Stage 1: Scraping...")
            scraping_result = self._validate_scraping(url)
            results["stages"]["scraping"] = scraping_result
            
            if not scraping_result["success"]:
                print("❌ Scraping failed - cannot continue pipeline")
                return results
            
            raw_content = scraping_result["content"]
            
            # Stage 2: Preprocessing
            print("\n🧹 Stage 2: Preprocessing...")
            preprocessing_result = self._validate_preprocessing(raw_content)
            results["stages"]["preprocessing"] = preprocessing_result
            
            # Stage 3: Chunking
            print("\n📦 Stage 3: Chunking...")
            chunking_result = self._validate_chunking(preprocessing_result["cleaned_content"])
            results["stages"]["chunking"] = chunking_result
            
            # Stage 4: Overall Assessment
            print("\n📊 Stage 4: Overall Assessment...")
            assessment = self._assess_pipeline_quality(results)
            results["assessment"] = assessment
            
            # Save debug information
            if save_debug:
                self._save_debug_info(results, raw_content, preprocessing_result["cleaned_content"])
            
            self._print_summary(results)
            
        except Exception as e:
            print(f"❌ Pipeline validation failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def _validate_scraping(self, url: str) -> Dict[str, Any]:
        """Validate scraping stage."""
        result = {
            "success": False,
            "content": "",
            "content_length": 0,
            "quality_score": 0,
            "issues": []
        }
        
        try:
            # Try enhanced scraping
            content = enhanced_scrape_url(url, validate_quality=True, min_content_length=100)
            
            # Validate content quality
            is_valid, message = _validate_content_quality(content, min_length=100)
            quality_analysis = self.analyzer.analyze_content_quality(content)
            
            result.update({
                "success": True,
                "content": content,
                "content_length": len(content),
                "quality_score": quality_analysis["quality_score"],
                "word_count": quality_analysis["word_count"],
                "line_count": quality_analysis["line_count"],
                "unique_words": quality_analysis["unique_words"],
                "repetition_ratio": quality_analysis["repetition_ratio"],
                "issues": quality_analysis["issues"]
            })
            
            print(f"  ✅ Scraped {len(content)} characters")
            print(f"  📊 Quality score: {quality_analysis['quality_score']}/100")
            
            if quality_analysis["issues"]:
                print(f"  ⚠ Issues: {', '.join(quality_analysis['issues'])}")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Scraping failed: {e}")
        
        return result
    
    def _validate_preprocessing(self, raw_content: str) -> Dict[str, Any]:
        """Validate preprocessing stage."""
        result = {
            "success": False,
            "cleaned_content": "",
            "improvement_ratio": 0,
            "noise_removed": 0
        }
        
        try:
            # Analyze raw content
            raw_quality = self.analyzer.analyze_content_quality(raw_content)
            
            # Clean content
            cleaned_content = aggressive_clean_text(raw_content)
            
            # Analyze cleaned content
            cleaned_quality = self.analyzer.analyze_content_quality(cleaned_content)
            
            # Calculate improvements
            quality_improvement = cleaned_quality["quality_score"] - raw_quality["quality_score"]
            size_reduction = len(raw_content) - len(cleaned_content)
            
            result.update({
                "success": True,
                "cleaned_content": cleaned_content,
                "raw_quality": raw_quality["quality_score"],
                "cleaned_quality": cleaned_quality["quality_score"],
                "quality_improvement": quality_improvement,
                "size_reduction": size_reduction,
                "size_reduction_percent": (size_reduction / len(raw_content)) * 100 if raw_content else 0,
                "noise_removed": size_reduction > 0
            })
            
            print(f"  📊 Quality: {raw_quality['quality_score']} → {cleaned_quality['quality_score']} ({quality_improvement:+d})")
            print(f"  📉 Size: {len(raw_content)} → {len(cleaned_content)} chars ({result['size_reduction_percent']:.1f}% reduction)")
            
            if quality_improvement > 0:
                print(f"  ✅ Quality improved by {quality_improvement} points")
            elif quality_improvement < 0:
                print(f"  ⚠ Quality decreased by {abs(quality_improvement)} points")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Preprocessing failed: {e}")
        
        return result
    
    def _validate_chunking(self, cleaned_content: str) -> Dict[str, Any]:
        """Validate chunking stage."""
        result = {
            "success": False,
            "chunks": [],
            "chunk_count": 0,
            "avg_chunk_size": 0,
            "chunk_quality_scores": []
        }
        
        try:
            # Create chunks
            chunks = enhanced_chunk_text(cleaned_content, chunk_size=800, chunk_overlap=100)
            
            # Analyze each chunk
            chunk_qualities = []
            for chunk in chunks:
                quality = self.analyzer.analyze_content_quality(chunk)
                chunk_qualities.append(quality["quality_score"])
            
            avg_quality = sum(chunk_qualities) / len(chunk_qualities) if chunk_qualities else 0
            avg_size = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
            
            result.update({
                "success": True,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "avg_chunk_size": int(avg_size),
                "avg_chunk_quality": avg_quality,
                "chunk_quality_scores": chunk_qualities,
                "min_quality": min(chunk_qualities) if chunk_qualities else 0,
                "max_quality": max(chunk_qualities) if chunk_qualities else 0
            })
            
            print(f"  📦 Created {len(chunks)} chunks")
            print(f"  📏 Average chunk size: {int(avg_size)} characters")
            print(f"  📊 Average chunk quality: {avg_quality:.1f}/100")
            print(f"  📈 Quality range: {result['min_quality']:.1f} - {result['max_quality']:.1f}")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"  ❌ Chunking failed: {e}")
        
        return result
    
    def _assess_pipeline_quality(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall pipeline quality."""
        assessment = {
            "overall_score": 0,
            "readiness": "not_ready",
            "recommendations": []
        }
        
        stages = results.get("stages", {})
        
        # Calculate overall score
        scores = []
        
        # Scraping score (40% weight)
        if stages.get("scraping", {}).get("success"):
            scraping_score = stages["scraping"]["quality_score"]
            scores.append(scraping_score * 0.4)
        
        # Preprocessing score (30% weight)
        if stages.get("preprocessing", {}).get("success"):
            preprocessing_score = stages["preprocessing"]["cleaned_quality"]
            scores.append(preprocessing_score * 0.3)
        
        # Chunking score (30% weight)
        if stages.get("chunking", {}).get("success"):
            chunking_score = stages["chunking"]["avg_chunk_quality"]
            scores.append(chunking_score * 0.3)
        
        overall_score = sum(scores) if scores else 0
        assessment["overall_score"] = overall_score
        
        # Determine readiness
        if overall_score >= 70:
            assessment["readiness"] = "ready"
        elif overall_score >= 50:
            assessment["readiness"] = "needs_improvement"
        else:
            assessment["readiness"] = "not_ready"
        
        # Generate recommendations
        recommendations = []
        
        if stages.get("scraping", {}).get("quality_score", 0) < 50:
            recommendations.append("Improve scraping: Try different selectors or wait strategies")
        
        if stages.get("preprocessing", {}).get("quality_improvement", 0) < 0:
            recommendations.append("Preprocessing is reducing quality: Review cleaning rules")
        
        if stages.get("chunking", {}).get("avg_chunk_quality", 0) < 40:
            recommendations.append("Poor chunk quality: Adjust chunk size or overlap")
        
        chunk_count = stages.get("chunking", {}).get("chunk_count", 0)
        if chunk_count < 3:
            recommendations.append("Too few chunks: Content might be too short or over-cleaned")
        elif chunk_count > 50:
            recommendations.append("Too many chunks: Consider larger chunk size")
        
        assessment["recommendations"] = recommendations
        
        print(f"  🎯 Overall Score: {overall_score:.1f}/100")
        print(f"  🚦 Readiness: {assessment['readiness'].replace('_', ' ').title()}")
        
        if recommendations:
            print(f"  💡 Recommendations:")
            for rec in recommendations:
                print(f"     • {rec}")
        
        return assessment
    
    def _save_debug_info(self, results: Dict[str, Any], raw_content: str, cleaned_content: str):
        """Save debug information to files."""
        
        # Create debug directory
        debug_dir = "debug_output"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Generate unique filename based on URL hash
        url_hash = hashlib.md5(results["url"].encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{timestamp}_{url_hash}"
        
        # Save results JSON
        with open(f"{debug_dir}/{base_filename}_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save raw content
        with open(f"{debug_dir}/{base_filename}_raw.txt", 'w', encoding='utf-8') as f:
            f.write(raw_content)
        
        # Save cleaned content
        with open(f"{debug_dir}/{base_filename}_cleaned.txt", 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        # Save chunks
        chunks = results.get("stages", {}).get("chunking", {}).get("chunks", [])
        if chunks:
            with open(f"{debug_dir}/{base_filename}_chunks.txt", 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks, 1):
                    f.write(f"=== CHUNK {i} ===\n")
                    f.write(chunk)
                    f.write(f"\n\n")
        
        print(f"  💾 Debug files saved to: {debug_dir}/{base_filename}_*")
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📋 PIPELINE VALIDATION SUMMARY")
        print("=" * 60)
        
        assessment = results.get("assessment", {})
        overall_score = assessment.get("overall_score", 0)
        readiness = assessment.get("readiness", "unknown")
        
        # Status emoji
        if readiness == "ready":
            status_emoji = "✅"
        elif readiness == "needs_improvement":
            status_emoji = "⚠️"
        else:
            status_emoji = "❌"
        
        print(f"{status_emoji} Overall Score: {overall_score:.1f}/100")
        print(f"🚦 Pipeline Status: {readiness.replace('_', ' ').title()}")
        
        # Stage breakdown
        stages = results.get("stages", {})
        print(f"\n📊 Stage Breakdown:")
        
        for stage_name, stage_data in stages.items():
            if stage_data.get("success"):
                if stage_name == "scraping":
                    score = stage_data.get("quality_score", 0)
                elif stage_name == "preprocessing":
                    score = stage_data.get("cleaned_quality", 0)
                elif stage_name == "chunking":
                    score = stage_data.get("avg_chunk_quality", 0)
                else:
                    score = 0
                
                status = "✅" if score >= 50 else "⚠️" if score >= 30 else "❌"
                print(f"  {status} {stage_name.title()}: {score:.1f}/100")
            else:
                print(f"  ❌ {stage_name.title()}: Failed")
        
        # Recommendations
        recommendations = assessment.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        print("\n" + "=" * 60)


def quick_validate(url: str) -> bool:
    """Quick validation - returns True if pipeline is ready for production."""
    validator = PipelineValidator(debug_mode=False)
    results = validator.validate_full_pipeline(url, save_debug=False)
    
    assessment = results.get("assessment", {})
    return assessment.get("readiness") == "ready"


if __name__ == "__main__":
    # Test the validator
    test_urls = [
        "https://help.shopify.com/en/manual",
        "https://support.microsoft.com/en-us",
        "https://docs.github.com/en"
    ]
    
    validator = PipelineValidator()
    
    print("🧪 Testing Pipeline Validator")
    print("=" * 60)
    
    for url in test_urls[:1]:  # Test first URL only
        try:
            results = validator.validate_full_pipeline(url)
            print(f"\n✅ Validation completed for {url}")
        except Exception as e:
            print(f"\n❌ Validation failed for {url}: {e}")
        
        print("\n" + "-" * 60 + "\n")
