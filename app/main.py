from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.config import OUTPUT_DIR
from app.database import init_db
from app.schemas import CreateJobRequest, JobResult
from app.service import create_job, get_job, get_certificate, process_job

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(title="Bulk Certificate Generator", version="1.0.0",
              description="Bulk PDF generation with status tracking and downloads.", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/jobs", status_code=202)
def submit_job(request: CreateJobRequest, background_tasks: BackgroundTasks):
    event_name = request.event_name.strip()
    if not event_name:
        raise HTTPException(status_code=422, detail="event_name cannot be blank.")
    issuer = request.issuer.strip() or "Certificate Team"
    job_id = create_job(event_name, issuer, [r.model_dump() for r in request.recipients])
    background_tasks.add_task(process_job, job_id, event_name, issuer)
    return {"job_id": job_id, "status": "queued", "status_url": f"/api/jobs/{job_id}"}

@app.get("/api/jobs/{job_id}", response_model=JobResult)
def job_status(job_id: str):
    result = get_job(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return result

@app.get("/api/certificates/{recipient_id}")
def download_certificate(recipient_id: int):
    path = get_certificate(recipient_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Certificate not found or not ready.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
