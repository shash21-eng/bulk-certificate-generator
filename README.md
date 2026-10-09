# Bulk Certificate Generator

A FastAPI backend that accepts a bulk recipient list, validates each recipient independently, generates PDF certificates from one fixed template, tracks job status, and exposes download links.

## Stack
- Python 3.10+
- FastAPI and Pydantic
- SQLite via Python's standard library
- ReportLab for PDF generation
- pytest and FastAPI TestClient

## Project structure
```text
app/        API, database, validation, processing, PDF template
tests/      API and failure-handling tests
requirements.txt
README.md
```

## Setup

### Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
If activation is blocked, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```
Docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/health

Database defaults to `data/certificates.db`; PDF files are saved under `certificates/`. Set `CERTGEN_DB_PATH` or `CERTGEN_OUTPUT_DIR` to override these paths.

## API

### Submit one bulk job
`POST /api/jobs`

```json
{
  "event_name": "AI Workshop 2026",
  "issuer": "Example Organization",
  "recipients": [
    {"name": "Ada Lovelace", "email": "ada@example.com", "course": "AI Fundamentals"},
    {"name": "Grace Hopper", "email": "grace@example.com", "course": "Python Backend Development"}
  ]
}
```

Returns `202 Accepted` with `job_id`, initial status, and `status_url`. In Swagger UI, open `/docs` and try the endpoint directly.

### Check progress/results
`GET /api/jobs/{job_id}`

Returns job status, totals, per-recipient status, error details, and a `certificate_url` for each successful recipient.

### Download a PDF
`GET /api/certificates/{recipient_id}`

Use the URL from the job response. A certificate that is unknown or not successfully generated returns `404`.

## Validation and failure handling
- A batch must contain 1–500 recipients.
- Event name is required and limited to 200 characters.
- Each recipient needs a nonblank name, a basic valid email address, and a nonblank course; name and course are limited to 200 characters.
- Recipient fields are validated independently so invalid data does not reject the whole batch.
- Each PDF generation has its own exception boundary. A failed certificate does not stop other valid recipients.
- Client responses contain a generic generation error rather than internal exception details.

## Statuses
- `queued`: accepted and waiting to run
- `processing`: recipients are being processed
- `completed`: all certificates succeeded
- `completed_with_errors`: a mixture of success and failure
- `failed`: no recipient succeeded

## Tests
```bash
pytest -q
```
The suite covers job creation/status, validation, PDF creation and retrieval, unknown resources, invalid-recipient isolation, and simulated individual generation failure.

## Design choices and production considerations
- **BackgroundTasks:** meets the assignment's asynchronous job interface without another service. It runs in the API process and is not a durable queue; for large production workloads, use Celery/RQ/Arq with Redis or another durable queue.
- **SQLite:** keeps setup simple for an assignment. Consider PostgreSQL for multiple application workers and heavier concurrency.
- **One fixed template:** ReportLab creates landscape A4 certificates containing recipient, course, event, and issuer.
- **Independent recipient outcomes:** every recipient is stored and reported separately, making partial success visible to the client.
- **Future improvements:** add authentication, rate limits, retention/cleanup, idempotency keys, retry policy, and a durable task queue.

## Interview walkthrough
1. Receive a single request containing many recipients.
2. Persist a job and recipient rows before scheduling work.
3. Validate and generate each recipient's PDF independently.
4. Store each result and compute the final job summary.
5. Let the client poll status and download successful certificates.
