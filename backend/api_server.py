from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Import the pipeline function
from main import run_pipeline

load_dotenv()

app = FastAPI(title="WebIntel Analytics API", version="1.0.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501", "http://127.0.0.1:8501",  # Streamlit default ports
        "http://localhost:3000", "http://127.0.0.1:3000",  # Node.js backend
        "http://localhost:4200", "http://127.0.0.1:4200",  # Angular frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (in production, use Redis or database)
jobs: Dict[str, Dict[str, Any]] = {}

class PipelineRequest(BaseModel):
    url: str
    query: str = "Extract Golden Questions and Expected Responses that users commonly ask about this product/service for comprehensive bot testing"
    output_filename: str = "golden_qna.xlsx"
    k: int = 30
    scroll_pages: int = 5
    output_format: str = "excel"
    validate_content: bool = True
    crawl: bool = False
    max_depth: int = 1
    max_pages: int = 20
    same_domain_only: bool = True
    with_test_cases: bool = True
    test_cases_llm: bool = False
    tc_variations: int = 20
    tc_negatives: int = 12

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    message: str
    progress: Optional[str] = None
    output_file: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

def run_pipeline_job(job_id: str, request: PipelineRequest):
    """Run the pipeline in background and update job status"""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["message"] = "Pipeline started"
        
        # Ensure output directory exists
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, request.output_filename)
        
        # Run the pipeline
        result_path = run_pipeline(
            url=request.url,
            query=request.query,
            output=output_path,
            k=request.k,
            scroll_pages=request.scroll_pages,
            output_format=request.output_format,
            validate_content=request.validate_content,
            crawl=request.crawl,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            same_domain_only=request.same_domain_only,
            with_test_cases=request.with_test_cases,
            test_cases_llm=request.test_cases_llm,
            tc_variations=request.tc_variations,
            tc_negatives=request.tc_negatives,
        )
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["message"] = "Pipeline completed successfully"
        jobs[job_id]["output_file"] = result_path
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = "Pipeline failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

@app.get("/")
async def root():
    return {"message": "WebIntel Analytics API", "version": "1.0.0"}

@app.post("/api/pipeline/start", response_model=JobStatus)
async def start_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Start a new pipeline job"""
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "message": "Job queued",
        "created_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    # Start background task
    background_tasks.add_task(run_pipeline_job, job_id, request)
    
    return JobStatus(**jobs[job_id])

@app.get("/api/pipeline/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a pipeline job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs[job_id])

@app.get("/api/pipeline/download/{job_id}")
async def download_result(job_id: str):
    """Download the result file for a completed job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    output_file = job.get("output_file")
    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=output_file,
        filename=os.path.basename(output_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs"""
    return {"jobs": list(jobs.values())}

@app.delete("/api/pipeline/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its output file"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    output_file = job.get("output_file")
    
    # Delete output file if exists
    if output_file and os.path.exists(output_file):
        try:
            os.remove(output_file)
        except Exception as e:
            print(f"Failed to delete output file: {e}")
    
    # Remove job from memory
    del jobs[job_id]
    
    return {"message": "Job deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
