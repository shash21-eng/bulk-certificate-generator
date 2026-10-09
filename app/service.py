import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from app.config import OUTPUT_DIR
from app.database import connection
from app.certificates import generate_certificate

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def validate_recipient(name, email, course):
    if not name or not name.strip():
        return "Name is required."
    if len(name.strip()) > 200:
        return "Name must be 200 characters or fewer."
    if not email or not EMAIL_RE.match(email.strip()):
        return "A valid email address is required."
    if not course or not course.strip():
        return "Course is required."
    if len(course.strip()) > 200:
        return "Course must be 200 characters or fewer."
    return None

def create_job(event_name, issuer, recipients):
    job_id, now = str(uuid4()), utc_now()
    with connection() as conn:
        conn.execute("INSERT INTO jobs(id,status,total,succeeded,failed,created_at) VALUES(?,?,?,?,?,?)",
                     (job_id, "queued", len(recipients), 0, 0, now))
        for item in recipients:
            conn.execute("""INSERT INTO recipients(job_id,name,email,course,status)
                            VALUES(?,?,?,?,?)""",
                         (job_id, item.get("name", ""), item.get("email", ""),
                          item.get("course", ""), "queued"))
    return job_id

def process_job(job_id, event_name, issuer):
    with connection() as conn:
        conn.execute("UPDATE jobs SET status='processing' WHERE id=?", (job_id,))
        rows = conn.execute("SELECT * FROM recipients WHERE job_id=? ORDER BY id", (job_id,)).fetchall()
    for row in rows:
        error = validate_recipient(row["name"] or "", row["email"] or "", row["course"] or "")
        if error:
            with connection() as conn:
                conn.execute("UPDATE recipients SET status='failed',error=? WHERE id=?", (error, row["id"]))
            continue
        try:
            path = Path(OUTPUT_DIR) / job_id / f"{row['id']}-{uuid4().hex}.pdf"
            generate_certificate(path, row["name"].strip(), row["course"].strip(), event_name, issuer)
            with connection() as conn:
                conn.execute("UPDATE recipients SET status='succeeded',certificate_path=?,error=NULL WHERE id=?",
                             (str(path), row["id"]))
        except Exception:
            with connection() as conn:
                conn.execute("UPDATE recipients SET status='failed',error=? WHERE id=?",
                             ("Certificate generation failed.", row["id"]))
    with connection() as conn:
        succeeded = conn.execute("SELECT COUNT(*) FROM recipients WHERE job_id=? AND status='succeeded'",
                                 (job_id,)).fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM recipients WHERE job_id=? AND status='failed'",
                              (job_id,)).fetchone()[0]
        status = "completed" if failed == 0 else ("failed" if succeeded == 0 else "completed_with_errors")
        conn.execute("UPDATE jobs SET status=?,succeeded=?,failed=?,completed_at=? WHERE id=?",
                     (status, succeeded, failed, utc_now(), job_id))

def get_job(job_id):
    with connection() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            return None
        recipients = conn.execute("SELECT * FROM recipients WHERE job_id=? ORDER BY id",
                                  (job_id,)).fetchall()
    result = dict(job)
    result["recipients"] = []
    for row in recipients:
        item = dict(row)
        item["certificate_url"] = f"/api/certificates/{row['id']}" if row["status"] == "succeeded" else None
        item.pop("certificate_path", None)
        item.pop("job_id", None)
        result["recipients"].append(item)
    return result

def get_certificate(recipient_id):
    with connection() as conn:
        row = conn.execute("SELECT status,certificate_path FROM recipients WHERE id=?",
                           (recipient_id,)).fetchone()
    if not row or row["status"] != "succeeded" or not row["certificate_path"]:
        return None
    path = Path(row["certificate_path"])
    return path if path.is_file() else None
