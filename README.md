# WebIntel Analytics

Advanced AI-powered web intelligence platform for comprehensive content analysis and strategic question generation.

## Architecture

The application uses a modern 2-tier architecture:

- **Backend** (`backend/`): Python FastAPI REST API that handles the core pipeline processing
- **Frontend** (`angular-frontend/`): Modern Angular web interface with responsive design

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# source venv/bin/activate    # Linux/Mac

# Install Python dependencies
cd backend
pip install -r requirements.txt
python -m playwright install

# Install Angular dependencies  
cd ../angular-frontend
npm install
```

### 2. Configure API Keys

Create `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

### 3. Start the Services

**Option A: Automated Start**
```bash
# Install dependencies (first time only)
install_dependencies.bat

# Start both services
start_simplified.bat
```

**Option B: Manual Start**

Terminal 1 (Backend):
```bash
cd backend
python start_backend.py
# Backend runs on http://localhost:8000
```

Terminal 2 (Frontend):
```bash
cd angular-frontend
npm start
# Frontend runs on http://localhost:4200
```

### 4. Access the Application

- **Angular Frontend**: http://localhost:4200
- **Python Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Features

### Core Pipeline
- **Web Scraping**: Extract content from web pages with optional hyperlink crawling
- **Content Processing**: Clean and chunk text for optimal AI processing
- **Vector Search**: Semantic search using FAISS and sentence transformers
- **Q&A Generation**: Generate golden questions and responses using Groq LLM
- **Test Case Generation**: Create comprehensive test cases with variations and edge cases
- **Excel Export**: Export results to structured Excel files

### Advanced Options
- **Hyperlink Crawling**: Follow links to gather more comprehensive content
- **Content Quality Validation**: Analyze and validate content quality
- **Multiple Test Case Strategies**: Rule-based or LLM-based test case generation
- **Configurable Parameters**: Tune chunk size, retrieval count, and generation parameters

## API Endpoints

### Pipeline Management
- `POST /api/pipeline/start` - Start a new pipeline job
- `GET /api/pipeline/status/{job_id}` - Get job status
- `GET /api/pipeline/download/{job_id}` - Download result file
- `DELETE /api/pipeline/{job_id}` - Delete job and files

### Utility
- `GET /` - Health check
- `GET /api/jobs` - List all jobs

## Output Format

The system generates Excel files with two sheets:

### Golden QnA Sheet
- S.No
- Expected Golden Question  
- Test case (variations and negative cases)
- Expected Result
- URL

### TestCases Sheet (when enabled)
- ID
- Question
- Expected Response
- Test Steps
- Variations
- Negative Case
- Entities/Slots
- Notes

## Development

### Backend Development
```bash
cd backend
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development  
```bash
cd frontend
streamlit run ui_app.py --server.port 8501
```

## Troubleshooting

### Common Issues

1. **Backend not starting**: Check that all dependencies are installed and GROQ_API_KEY is set
2. **Frontend can't connect**: Ensure backend is running on port 8000
3. **Permission errors on Windows**: Close Excel files before running pipeline
4. **Playwright browser not found**: Run `python -m playwright install`

### Dependencies

**Backend Requirements:**
- FastAPI, Uvicorn (API server)
- Playwright (web scraping)
- FAISS, sentence-transformers (vector search)
- Groq (LLM API)
- Pandas, openpyxl (data processing)

**Frontend Requirements:**
- Streamlit (web interface)
- Requests (API communication)

## License

This project is for internal use and development purposes.
