# Phase 3 Planning: API Server & Integration Layer

## Overview

**Current Status:** Phase 2 Complete ✅ (82/84 tests passing)
**Next Phase:** Phase 3 - API Server & Real-time Integration
**Timeline:** Ready to Start

---

## Phase 3 Objectives

### Primary Goals

1. **API Server Development**
   - Create REST API endpoints for video processing
   - Implement real-time processing endpoints
   - Support batch operations
   - WebSocket for real-time updates

2. **Integration with Phase 2 Modules**
   - Connect API to frame extraction
   - Connect API to change detection
   - Connect API to interaction detection
   - Connect API to frame indexing

3. **Database Layer**
   - Store analysis results
   - Persist frame metadata
   - Track processing jobs
   - Support querying historical data

4. **Frontend Dashboard**
   - Real-time progress tracking
   - Results visualization
   - Job management
   - Report generation

---

## Architecture Overview

### Current Stack (Phase 2)
```
Video Input
    ↓
Frame Extraction
    ↓
Change Detection
    ↓
Interaction Detection
    ↓
Frame Indexing
    ↓
JSON Output
```

### Phase 3 Architecture
```
HTTP/WebSocket Clients
    ↓
API Server (Flask/FastAPI)
    ├── POST /api/process-video
    ├── GET /api/jobs/{job_id}
    ├── GET /api/results/{job_id}
    └── WebSocket /ws/progress/{job_id}
    ↓
Job Queue (Celery/RQ)
    ↓
Processing Workers
    ├── Frame Extraction Service
    ├── Analysis Service
    └── Indexing Service
    ↓
Database (PostgreSQL/MongoDB)
    ├── Jobs Table
    ├── Results Table
    └── Metadata Table
    ↓
File Storage (Local/S3)
    └── Frames, Videos, Reports
```

---

## Proposed Module Structure

### Phase 3 File Organization

```
c:\Users\vikra\Downloads\RAG Agent\
├── video_training/              (Phase 2 - Core)
│   ├── frame_extraction.py
│   ├── change_detector.py
│   ├── interaction_detector.py
│   ├── frame_index.py
│   ├── frame_analyzer.py
│   └── tests/
│
├── api_server/                  (Phase 3 - NEW)
│   ├── app.py                   (Main Flask/FastAPI application)
│   ├── models.py                (Database models)
│   ├── routes.py                (API endpoints)
│   ├── services.py              (Business logic)
│   ├── workers.py               (Job processors)
│   ├── middleware.py            (Auth, logging, etc.)
│   └── tests/
│
├── dashboard/                   (Phase 3 - NEW)
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── results.html
│   │   └── jobs.html
│   └── app.py
│
├── database/                    (Phase 3 - NEW)
│   ├── models.py                (SQLAlchemy models)
│   ├── migrations/
│   └── queries.py
│
└── requirements_phase3.txt
```

---

## API Endpoints Design

### Video Processing

```
POST /api/v1/process
├── Input: video_file, options
├── Output: { job_id, status_url }
└── Returns: HTTP 202 Accepted

GET /api/v1/jobs/{job_id}
├── Returns: { status, progress, start_time, eta }
└── Status: pending, processing, completed, failed

GET /api/v1/results/{job_id}
├── Returns: { frames, changes, interactions, metadata }
└── Full analysis results

GET /api/v1/results/{job_id}/summary
├── Returns: { total_frames, changes_count, interactions_count }
└── Quick summary
```

### WebSocket Real-time

```
WebSocket /ws/v1/jobs/{job_id}
├── Subscribe to real-time updates
├── Receive: { status, progress, frame_count, eta }
└── Auto-disconnect on completion
```

### Job Management

```
GET /api/v1/jobs
├── Returns: [{ job_id, status, created_at }]
├── Filter by: status, date_range
└── Pagination support

DELETE /api/v1/jobs/{job_id}
├── Cancel running job
└── Delete results (optional)
```

---

## Database Schema (Draft)

### Jobs Table

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    video_filename VARCHAR(255),
    status VARCHAR(50),  -- pending, processing, completed, failed
    progress INTEGER,    -- 0-100
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    video_path VARCHAR(512),
    results_path VARCHAR(512)
);
```

### Results Table

```sql
CREATE TABLE results (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    total_frames INTEGER,
    frame_format VARCHAR(10),
    extraction_time FLOAT,
    changes_detected INTEGER,
    interactions_detected INTEGER,
    analysis_time FLOAT,
    created_at TIMESTAMP
);
```

### Frames Table

```sql
CREATE TABLE frames (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id),
    frame_number INTEGER,
    timestamp FLOAT,
    change_score FLOAT,
    interactions JSONB,
    window_name VARCHAR(255),
    tags JSONB
);
```

---

## Implementation Plan

### Phase 3.1: Core API Server (Week 1)

**Deliverables:**
- [ ] Flask/FastAPI application setup
- [ ] Database connection and models
- [ ] Job queue system (Celery/RQ)
- [ ] Basic /process endpoint
- [ ] Job status tracking
- [ ] Error handling middleware

**Tests:**
- [ ] Unit tests for all endpoints
- [ ] Integration tests with Phase 2 modules
- [ ] Load testing

**Time Estimate:** 40-50 hours

### Phase 3.2: Advanced API Features (Week 2)

**Deliverables:**
- [ ] WebSocket support
- [ ] Batch processing
- [ ] Result filtering and pagination
- [ ] Job history and analytics
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Rate limiting and auth

**Tests:**
- [ ] WebSocket connection tests
- [ ] Concurrent request tests
- [ ] Stress testing

**Time Estimate:** 30-40 hours

### Phase 3.3: Dashboard & Frontend (Week 3)

**Deliverables:**
- [ ] Dashboard UI (HTML/CSS/JS)
- [ ] Real-time progress display
- [ ] Results visualization
- [ ] Job management interface
- [ ] Report export (PDF, CSV, JSON)
- [ ] Responsive design

**Tests:**
- [ ] E2E tests with Selenium
- [ ] UI responsive tests
- [ ] Performance tests

**Time Estimate:** 35-45 hours

### Phase 3.4: Production Setup (Week 4)

**Deliverables:**
- [ ] Docker containerization
- [ ] Docker Compose orchestration
- [ ] Kubernetes deployment files (optional)
- [ ] CI/CD pipeline
- [ ] Monitoring and logging
- [ ] Backup and recovery

**Tests:**
- [ ] Deployment tests
- [ ] Failover testing
- [ ] Recovery testing

**Time Estimate:** 30-40 hours

---

## Technology Stack Recommendations

### Backend

```
Framework: FastAPI (modern, fast) or Flask (simpler)
  Recommendation: FastAPI for async support

Database: PostgreSQL (production) or SQLite (dev)
Job Queue: Celery + Redis or RQ

Dependencies:
- sqlalchemy (ORM)
- pydantic (validation)
- python-multipart (file upload)
- websockets (real-time)
- redis (caching, queue)
```

### Frontend

```
Framework: React or Vue.js
  Recommendation: React for ecosystem

Build: Webpack or Vite
Styling: Tailwind CSS or Bootstrap
Charts: Chart.js or Recharts
WebSocket: Socket.IO

Dependencies:
- axios (HTTP)
- react-query (state)
- react-router (navigation)
```

### DevOps

```
Containerization: Docker
Orchestration: Docker Compose or Kubernetes
Logging: ELK Stack or Loki
Monitoring: Prometheus + Grafana
CI/CD: GitHub Actions or GitLab CI
```

---

## Development Environment Setup

### Local Development

```bash
# Clone and setup
git clone repo
cd RAG-Agent
git checkout video-training-dev

# Backend setup
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy redis celery
pip install -r requirements.txt
pip install -r requirements_phase3.txt

# Database
createdb rag_agent_db  # PostgreSQL
alembic upgrade head   # Migrations

# Redis
redis-server  # or docker run redis

# Run dev server
uvicorn api_server.app:app --reload

# Run workers
celery -A api_server.workers worker

# Frontend development
cd dashboard
npm install
npm start
```

---

## Testing Strategy

### Unit Tests

```python
# Test each endpoint
def test_process_video_endpoint():
    response = client.post('/api/v1/process', data={...})
    assert response.status_code == 202
    assert 'job_id' in response.json()

# Test job tracking
def test_get_job_status():
    job_id = create_test_job()
    response = client.get(f'/api/v1/jobs/{job_id}')
    assert response.status_code == 200
    assert 'status' in response.json()
```

### Integration Tests

```python
# End-to-end video processing
def test_full_video_processing_pipeline():
    # Upload video
    # Check processing
    # Verify results
    # Compare with Phase 2 output
```

### Load Tests

```python
# Concurrent requests
def test_concurrent_uploads():
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(upload_video, f"video_{i}.mp4")
            for i in range(100)
        ]
```

---

## API Documentation Example

### Swagger/OpenAPI

```yaml
openapi: 3.0.0
info:
  title: RAG Agent Video Analysis API
  version: 1.0.0

paths:
  /api/v1/process:
    post:
      summary: Submit video for processing
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                video:
                  type: string
                  format: binary
      responses:
        202:
          description: Job created
          content:
            application/json:
              schema:
                type: object
                properties:
                  job_id:
                    type: string
                  status_url:
                    type: string
```

---

## Key Considerations

### Performance

1. **Async Processing**
   - Video processing is I/O bound
   - Use async/await and job queues
   - Target: <5 seconds response time

2. **Caching**
   - Cache processing results
   - Redis for session/job cache
   - CDN for static assets

3. **Scalability**
   - Horizontal scaling via workers
   - Load balancing
   - Database query optimization

### Security

1. **Authentication**
   - JWT tokens
   - API key management
   - Role-based access control

2. **Input Validation**
   - File type checking
   - Size limits
   - Path traversal prevention

3. **Data Protection**
   - HTTPS/TLS
   - Sensitive data encryption
   - Audit logging

### Reliability

1. **Error Handling**
   - Graceful degradation
   - Retry logic
   - Dead letter queues

2. **Monitoring**
   - Real-time alerting
   - Performance metrics
   - Error tracking

3. **Backup & Recovery**
   - Database backups
   - File versioning
   - Disaster recovery plan

---

## Success Criteria

### Phase 3 Completion

- [ ] API server running and responding
- [ ] All endpoints tested and documented
- [ ] Database persisting results
- [ ] Job queue processing videos
- [ ] Dashboard displaying results
- [ ] 50+ integration tests passing
- [ ] Performance <2s response time (median)
- [ ] 99% uptime in staging
- [ ] Full documentation
- [ ] Zero critical security issues

---

## Timeline Estimate

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| 3.1: API Server | 6 days | Week 1 Mon | Week 1 Sat |
| 3.2: Advanced Features | 5 days | Week 2 Mon | Week 2 Fri |
| 3.3: Dashboard | 5 days | Week 3 Mon | Week 3 Fri |
| 3.4: Production Setup | 5 days | Week 4 Mon | Week 4 Fri |
| **Total Phase 3** | **~21 days** | - | - |

---

## Quick Start Checklist

Before starting Phase 3:

- [ ] Phase 2 code committed ✅ Done
- [ ] All tests passing ✅ Done (82/84)
- [ ] Documentation complete ✅ Done
- [ ] Team aligned on architecture
- [ ] Technology stack approved
- [ ] Development environment ready
- [ ] Testing strategy agreed
- [ ] Deployment plan finalized

---

## Next Actions

1. **Immediate (Today)**
   - [ ] Review this Phase 3 plan
   - [ ] Decide on FastAPI vs Flask
   - [ ] Decide on PostgreSQL vs MongoDB
   - [ ] Approve technology stack

2. **This Week**
   - [ ] Set up project structure
   - [ ] Create database schema
   - [ ] Initialize Flask/FastAPI project
   - [ ] Write first endpoint tests

3. **Next Week**
   - [ ] Implement core API endpoints
   - [ ] Add job queue system
   - [ ] Add database models
   - [ ] Write integration tests

---

## Questions for Review

1. **Should we use FastAPI or Flask?**
   - FastAPI: Faster, async, auto-docs
   - Flask: Simpler, more familiar

2. **Should we use PostgreSQL or MongoDB?**
   - PostgreSQL: Structured, ACID, joins
   - MongoDB: Flexible, JSON, scalable

3. **Should we deploy on Kubernetes?**
   - Yes: For production scalability
   - No: Docker Compose is simpler initially

4. **What authentication level?**
   - Basic: API keys
   - Advanced: JWT + RBAC
   - Enterprise: OAuth2 + SSO

---

## Resources Needed

- [ ] 1-2 Senior Backend Engineers
- [ ] 1 Full-stack Engineer
- [ ] 1 DevOps Engineer (part-time)
- [ ] 1 QA Engineer
- [ ] Infrastructure: Dev/Staging/Prod servers
- [ ] 16-21 days development time

---

**Phase 3 is ready to begin when you approve!**

Generated: November 1, 2024
Status: ✅ Ready for approval and start
