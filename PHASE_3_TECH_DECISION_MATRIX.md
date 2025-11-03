# Phase 3 Technology Decision Matrix

## Framework Selection: FastAPI vs Flask

| Criteria | FastAPI | Flask | Winner |
|----------|---------|-------|--------|
| **Performance** | Very Fast (async/await) | Moderate | FastAPI ⭐ |
| **Learning Curve** | Moderate | Easy | Flask ✅ |
| **Type Hints** | Built-in | Not built-in | FastAPI ⭐ |
| **API Documentation** | Auto Swagger/ReDoc | Manual | FastAPI ⭐ |
| **Async Support** | Native, excellent | via extensions | FastAPI ⭐ |
| **WebSocket** | Built-in | via extensions | FastAPI ⭐ |
| **Maturity** | Newer (2018) | Established (2010) | Flask ✅ |
| **Community** | Growing rapidly | Very large | Flask ✅ |
| **Middleware** | Advanced | Simple | FastAPI ⭐ |
| **For Our Use Case** | **Better for real-time** | **Better for simple CRUD** | **FastAPI ⭐⭐⭐** |

### Recommendation: **FastAPI**

**Reasoning:**
- Native async support for concurrent video processing
- Built-in WebSocket support for real-time progress
- Automatic API documentation (Swagger)
- Type hints improve code quality
- Better performance for I/O-bound operations
- Modern Python async framework

---

## Database Selection: PostgreSQL vs MongoDB

| Criteria | PostgreSQL | MongoDB | Winner |
|----------|------------|---------|--------|
| **ACID Compliance** | Full | Limited | PostgreSQL ⭐ |
| **Transactions** | Full support | Limited | PostgreSQL ⭐ |
| **Schema Flexibility** | Fixed schema | Flexible | MongoDB ✅ |
| **Queries** | Complex joins | Simple lookups | PostgreSQL ⭐ |
| **Data Integrity** | Strict | Loose | PostgreSQL ⭐ |
| **Scaling** | Vertical | Horizontal | MongoDB ✅ |
| **JSON Support** | JSONB type | Native | MongoDB ✅ |
| **Performance (small)** | Excellent | Good | PostgreSQL ⭐ |
| **Learning Curve** | SQL required | JavaScript-like | MongoDB ✅ |
| **For Our Use Case** | **Better for structured data** | **Better for flexible schemas** | **PostgreSQL ⭐⭐⭐** |

### Recommendation: **PostgreSQL**

**Reasoning:**
- Frame metadata is highly structured
- Need reliable job tracking (ACID transactions)
- Complex queries for filtering/sorting
- Better for time-series data
- Proven in production
- Superior for analytics queries

### Alternative: **Hybrid Approach**
- **PostgreSQL** for jobs, results, frame metadata
- **Redis** for caching and real-time updates
- **MongoDB** for flexible configuration storage (optional)

---

## Job Queue Selection: Celery vs RQ

| Criteria | Celery | RQ | Winner |
|----------|--------|-----|--------|
| **Setup Complexity** | Complex | Simple | RQ ✅ |
| **Scalability** | Excellent | Good | Celery ⭐ |
| **Monitoring** | Advanced tools | Basic | Celery ⭐ |
| **Retry Logic** | Sophisticated | Basic | Celery ⭐ |
| **Message Broker** | Redis/RabbitMQ | Redis only | RQ ✅ |
| **Learning Curve** | Steep | Shallow | RQ ✅ |
| **For Our Use Case** | **Better for large scale** | **Better for small scale** | **Celery ⭐ (initially RQ)** |

### Recommendation: **Start with RQ, migrate to Celery if needed**

**Reasoning for RQ (Start):**
- Simpler setup with fewer dependencies
- Good enough for initial implementation
- Easier to debug
- Uses only Redis

**Reasoning for Celery (Scale):**
- Better monitoring with Flower
- More sophisticated retry/error handling
- Better suited for production scale
- Migrate later when needed

---

## Containerization & Deployment

| Aspect | Recommendation | Reasoning |
|--------|---|---|
| **Containers** | Docker | Industry standard, easy development/deployment |
| **Orchestration (Start)** | Docker Compose | Simple, perfect for dev/staging |
| **Orchestration (Scale)** | Kubernetes | Enterprise-grade, automatic scaling |
| **CI/CD** | GitHub Actions | Already on GitHub, free for public repos |
| **Registry** | GitHub Container Registry | Integrated with GitHub, free |

---

## Recommended Tech Stack

### Backend

```
Framework:     FastAPI
Web Server:    Uvicorn
ASGI Support:  Yes (WebSocket, async)
ORM:           SQLAlchemy
Database:      PostgreSQL
Cache/Queue:   Redis
Job Queue:     RQ (initially)
API Docs:      Swagger/OpenAPI (auto-generated)

Key Libraries:
- fastapi
- uvicorn
- sqlalchemy
- pydantic
- redis
- python-rq
- psycopg2
- python-multipart
- websockets
```

### Frontend

```
Framework:     React or Vue.js
Build Tool:    Vite
Styling:       Tailwind CSS
State:         React Query or Pinia
WebSocket:     Socket.IO or native WebSocket
Charts:        Recharts or Chart.js

Recommendation: React + Vite + Tailwind
Reasoning:
- Largest ecosystem
- Best tooling
- Better component libraries
- Strong community
```

### Infrastructure

```
Containerization: Docker
Orchestration:    Docker Compose (dev/staging)
                  Kubernetes (production optional)
Logging:          Structured JSON logging + ELK/Loki
Monitoring:       Prometheus + Grafana
CI/CD:            GitHub Actions
Container Registry: GitHub Container Registry
```

---

## Implementation Phases

### Phase 3.1: MVP (2-3 weeks)

**Scope:**
- FastAPI application
- PostgreSQL database
- Basic /process endpoint
- RQ job queue
- Simple progress tracking

**Tech Stack:**
```
Backend: FastAPI + SQLAlchemy + PostgreSQL + RQ
Frontend: Simple HTML/CSS dashboard (minimal)
Deployment: Docker Compose locally
```

**Metrics:**
- Response time: <2 seconds
- Job processing: <5 minutes for 30min video
- Tests: 50+ tests, 95%+ passing

### Phase 3.2: Enhanced (1-2 weeks)

**Additions:**
- WebSocket support
- Advanced API features
- Better dashboard UI
- Authentication/authorization

**Tech Stack:**
```
Add: React frontend + Socket.IO
Add: JWT authentication
Add: Prometheus metrics
```

### Phase 3.3: Production (1 week)

**Additions:**
- Kubernetes deployment
- Advanced monitoring
- Backup/recovery
- Performance optimization

**Tech Stack:**
```
Add: Kubernetes manifests
Add: ELK stack for logging
Add: Grafana dashboards
```

---

## Development Environment Setup Script

### Windows PowerShell

```powershell
# Phase 3 Development Setup

# Create virtual environment
python -m venv venv_phase3
.\venv_phase3\Scripts\Activate.ps1

# Install backend dependencies
pip install fastapi uvicorn
pip install sqlalchemy psycopg2-binary pydantic
pip install redis rq
pip install pytest pytest-asyncio
pip install python-multipart

# Install PostgreSQL (if needed)
# Download from https://www.postgresql.org/download/windows/
# Or use: choco install postgresql12

# Start PostgreSQL
# Windows Service should auto-start

# Start Redis
# docker run -d -p 6379:6379 redis:latest

# Create database
# psql -U postgres -c "CREATE DATABASE rag_agent_db;"

# Start development server
uvicorn api_server.app:app --reload --port 8000

# In another terminal, start RQ worker
rq worker --with-scheduler
```

---

## File Structure Setup

```bash
# Create Phase 3 structure
mkdir api_server
mkdir api_server\tests

# Create initial files
touch api_server\__init__.py
touch api_server\app.py          # Main FastAPI app
touch api_server\models.py       # SQLAlchemy models
touch api_server\schemas.py      # Pydantic schemas
touch api_server\routes.py       # API endpoints
touch api_server\services.py     # Business logic
touch api_server\workers.py      # Job processors
touch api_server\config.py       # Configuration
touch api_server\database.py     # DB connection

mkdir dashboard
mkdir dashboard\static
mkdir dashboard\templates

# API Server configuration template
cat > api_server\config.py << 'EOF'
import os

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/rag_agent_db')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    API_TITLE = "RAG Agent Video Analysis API"
    API_VERSION = "1.0.0"
EOF
```

---

## API Endpoint Examples

### POST /api/v1/process

```python
from fastapi import UploadFile, File
from pydantic import BaseModel

@app.post("/api/v1/process")
async def process_video(
    file: UploadFile = File(...),
    sample_rate: int = 1,
    output_format: str = "png"
):
    """
    Submit a video for processing.
    
    Returns: {"job_id": "uuid", "status_url": "/api/v1/jobs/{job_id}"}
    """
    job_id = create_job(file.filename, sample_rate, output_format)
    queue_job(job_id, file.file)
    return {"job_id": job_id, "status_url": f"/api/v1/jobs/{job_id}"}
```

### GET /api/v1/jobs/{job_id}

```python
@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get job status and progress.
    
    Returns: {"status": "processing", "progress": 45, "eta": 120}
    """
    job = get_job_from_db(job_id)
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress,
        "eta": calculate_eta(job)
    }
```

### WebSocket /ws/v1/jobs/{job_id}

```python
@app.websocket("/ws/v1/jobs/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """
    WebSocket connection for real-time progress updates.
    """
    await websocket.accept()
    try:
        while True:
            job = get_job_from_db(job_id)
            await websocket.send_json({
                "status": job.status,
                "progress": job.progress,
                "frames_processed": job.frames_processed
            })
            await asyncio.sleep(1)
    except Exception as e:
        await websocket.close()
```

---

## Database Models (SQLAlchemy)

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_filename = Column(String(255))
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(String)
    video_path = Column(String(512))
    results_path = Column(String(512))

class Result(Base):
    __tablename__ = "results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    total_frames = Column(Integer)
    changes_detected = Column(Integer)
    interactions_detected = Column(Integer)
    analysis_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Frame(Base):
    __tablename__ = "frames"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"))
    frame_number = Column(Integer)
    timestamp = Column(Float)
    change_score = Column(Float)
    interactions = Column(JSON)
    window_name = Column(String(255))
    tags = Column(JSON)
```

---

## Testing Strategy

### Unit Tests (FastAPI)

```python
from fastapi.testclient import TestClient
from api_server.app import app

client = TestClient(app)

def test_process_video_endpoint():
    response = client.post(
        "/api/v1/process",
        files={"file": ("test.mp4", b"fake video content")}
    )
    assert response.status_code == 202
    assert "job_id" in response.json()

def test_get_job_status():
    job_id = "test-job-123"
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code in [200, 404]
    assert "status" in response.json() or response.status_code == 404
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_processing_pipeline():
    # Create job
    job_id = create_test_job("test_video.mp4")
    
    # Process video
    results = process_video_with_phase2(job_id)
    
    # Verify results match Phase 2 output
    assert results["total_frames"] > 0
    assert "changes" in results
    assert "interactions" in results
```

---

## Success Metrics

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (50%) | <500ms | p50 latency |
| API Response Time (99%) | <2s | p99 latency |
| Video Upload Latency | <5s | File size dependent |
| Job Queue Latency | <1s | Queue time |
| Processing Speed | <1 min per 1GB video | End-to-end |
| Dashboard Load | <2s | Page load time |

### Quality Targets

| Metric | Target |
|--------|--------|
| API Test Coverage | >90% |
| API Tests Passing | 100% |
| Integration Tests | >80 |
| Uptime (staging) | 99%+ |
| Error Rate | <0.1% |
| Critical Bugs | 0 |

---

## Next Steps

1. **Approve technology stack** ✅ Recommendation: FastAPI + PostgreSQL + RQ
2. **Set up development environment** - Follow setup script
3. **Create project structure** - See file structure above
4. **Write initial tests** - Test-driven development
5. **Implement MVP endpoints** - Start with /process endpoint
6. **Integrate Phase 2 modules** - Connect to existing code
7. **Add database layer** - Persist jobs and results
8. **Build job queue** - Implement RQ workers
9. **Create dashboard** - Simple HTML/CSS initially
10. **Performance tuning** - Optimize before production

---

**Ready to start Phase 3 implementation?**

Generated: November 1, 2024
Status: ✅ Technology stack selected and ready
